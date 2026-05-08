"""
智能评估
========
临床三合一流程：
  ① 标准化抑郁量表（PHQ-9 / CES-D 10）—— 国际 / 国内临床金标准
  ② 风险因素问卷（生活方式 + 心理社会因素 + 既往史）
  ③ 三模型集成 + 局部贡献分解，输出综合风险评估
"""

import pandas as pd
import streamlit as st

from utils.data_loader import load_model_bundle
from utils.model_utils import (
    predict_with_explain, risk_label_and_advice, column_labels,
)
from utils.llm_assistant import (
    is_configured as llm_is_configured,
    chat_stream as llm_chat_stream,
    get_suggested_questions,
)
from utils.scales import (
    PHQ9_QUESTIONS, PHQ9_OPTIONS, PHQ9_OPTION_VALUES,
    phq9_severity, phq9_clinical_advice,
    CESD10_QUESTIONS, CESD10_OPTIONS, CESD10_OPTION_VALUES,
    cesd10_total, cesd10_severity, cesd10_clinical_advice,
)
from utils.visualizations import risk_gauge, shap_bar


st.set_page_config(page_title="智能评估 | 知忧·解郁", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
.scale-title {font-size: 16px; font-weight: 700; color: #5BC8FF;
              margin: 12px 0 4px 0; padding-left: 10px;
              border-left: 3px solid #5BC8FF; letter-spacing: 1px;}
.scale-subtitle {font-size: 12px; color: #B8C5E0; margin-bottom: 14px;
                padding-left: 10px;}
.warn-box {background: rgba(248,113,113,0.10);
           border: 1px solid rgba(248,113,113,0.4);
           border-left: 4px solid #F87171;
           padding: 12px 16px; border-radius: 6px; margin: 12px 0;
           color: #FCA5A5;}
.score-card {background: linear-gradient(135deg, rgba(91,127,255,0.12),
                                        rgba(167,139,250,0.06));
             border: 1px solid rgba(91,200,255,0.3);
             border-radius: 12px; padding: 18px; text-align: center;}
.score-num {font-size: 42px; font-weight: 800; color: #E8F0FF;
            text-shadow: 0 0 14px rgba(91,200,255,0.4);}
.score-label {font-size: 12px; color: #9CA3AF; letter-spacing: 1px;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 智能抑郁风险评估")
st.caption("结合 **临床标准量表（PHQ-9 / CES-D 10）+ 风险因素问卷 + 机器学习模型** 三合一评估方案")

with st.expander("📌 量表来源 · 使用说明 · 免责声明（建议先阅读）", expanded=False):
    st.markdown("""
**量表来源（公共领域，可免费临床使用）：**
- **PHQ-9** — Kroenke, Spitzer, Williams, *Journal of General Internal Medicine*, 2001
  全球通用抑郁筛查金标准，国家卫生健康委员会、北京安定医院、上海精神卫生中心等推荐使用。
- **CES-D 10** — Andresen et al., *American Journal of Preventive Medicine*, 1994
  中国健康与养老追踪调查（CHARLS）、中国家庭追踪调查（CFPS）采用版本，是中国老年抑郁筛查标准工具。

**使用说明：** 请按照过去 **两周** 的真实感受作答。每题选最贴近你状态的选项即可。

**免责声明：** 本工具是辅助筛查与心理科普工具，**不能替代精神科医生临床诊断**。
若评估结果提示中度及以上风险，强烈建议尽快至精神 / 心理科就诊。
出现自伤 / 自杀念头请**立即**拨打：
- 全国 24h 心理援助热线 **400-161-9995**
- 天津心理援助热线 **022-88188858**
- 教育部高校心理援助热线 **010-67440033**
""")

group = st.radio(
    "请选择您所属人群类型",
    ["学生 / 一般成人（适用 PHQ-9）", "中老年（45 岁及以上，适用 CES-D 10）"],
    horizontal=True,
)
is_student = "学生" in group

st.markdown("---")

# ============================================================
# 学生 / 一般成人版
# ============================================================
if is_student:
    st.markdown('<div class="scale-title">第一部分：PHQ-9 抑郁症状量表</div>',
               unsafe_allow_html=True)
    st.markdown(
        '<div class="scale-subtitle">在过去 <b>两周</b> 内，你有多少时间受以下问题困扰？</div>',
        unsafe_allow_html=True,
    )

    phq9_responses = []
    for i, q in enumerate(PHQ9_QUESTIONS):
        choice = st.radio(
            q,
            options=PHQ9_OPTIONS,
            index=0,
            horizontal=True,
            key=f"phq9_{i}",
            label_visibility="visible",
        )
        phq9_responses.append(PHQ9_OPTION_VALUES[PHQ9_OPTIONS.index(choice)])

    phq9_total = sum(phq9_responses)
    phq9_q9 = phq9_responses[8]

    st.markdown('<div class="scale-title">第二部分：基本信息</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        age = st.number_input("年龄", 17, 30, 21)
    with c2:
        gender = st.selectbox("性别", ["男", "女"])
    with c3:
        grade = st.selectbox("年级",
                            ["大一", "大二", "大三", "大四", "研究生"])
    with c4:
        major = st.selectbox("专业类型",
                            ["医学", "理工", "文史", "经管", "艺术", "其他"])

    st.markdown('<div class="scale-title">第三部分：生活方式</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        sleep = st.slider("平均每日睡眠时长（小时）", 3.0, 11.0, 7.0, 0.5)
    with c2:
        exercise = st.slider("每周中等强度运动次数", 0, 8, 2)
    with c3:
        screen = st.slider("每日屏幕时长（小时）", 1.0, 16.0, 6.0, 0.5)

    st.markdown('<div class="scale-title">第四部分：心理社会因素</div>',
               unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        academic = st.slider("学业压力（1=极小, 10=极大）", 1, 10, 6)
        financial = st.slider("经济压力（1=极小, 10=极大）", 1, 10, 5)
    with c2:
        relationship = st.slider("亲密关系质量（1=极差, 10=极好）", 1, 10, 6)
        social = st.slider("社会支持（家人 / 朋友支持感, 1-10）", 1, 10, 7)

    st.markdown('<div class="scale-title">第五部分：既往史与生活习惯</div>',
               unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        family_hist = st.checkbox("家族抑郁史")
    with c2:
        childhood = st.checkbox("童年不良经历")
    with c3:
        chronic = st.checkbox("慢性疾病")
    with c4:
        smoking = st.checkbox("吸烟")
    with c5:
        drinking = st.checkbox("规律饮酒")

    # 保存当前表单"指纹"，供 sidebar 检测是否需要重新提交
    st.session_state["current_form_signature"] = (
        "student", phq9_total, age, gender, grade, major,
        sleep, exercise, screen, academic, financial,
        relationship, social, family_hist, childhood,
        chronic, smoking, drinking,
    )

    submitted = st.button("🔬 提交评估", type="primary", use_container_width=True)

    if submitted:
        # ---------- ① PHQ-9 临床打分 ----------
        phq9_sev = phq9_severity(phq9_total)

        # ---------- ② 模型推理 ----------
        x_row = pd.DataFrame([{
            "年龄": age,
            "性别_女": int(gender == "女"),
            "睡眠时长_小时": sleep,
            "每周运动次数": exercise,
            "学业压力": academic,
            "经济压力": financial,
            "亲密关系质量": relationship,
            "社会支持": social,
            "家族史": int(family_hist),
            "童年不良经历": int(childhood),
            "慢性疾病": int(chronic),
            "吸烟": int(smoking),
            "饮酒": int(drinking),
            "日均屏幕时长_小时": screen,
            "年级_大四": int(grade == "大四"),
            "年级_研究生": int(grade == "研究生"),
        }])
        bundle = load_model_bundle("student")
        # PHQ-9 总分传入，让最终风险随量表分变化
        result = predict_with_explain(bundle, x_row,
                                     scale_score=phq9_total, scale_max=27)

        st.markdown("---")
        st.markdown("## 📋 综合评估结果")

        # ---------- Q9 自杀风险特别提醒 ----------
        if phq9_q9 >= 1:
            st.markdown("""
<div class="warn-box">
<b style="color:#9D2933; font-size:16px;">⚠️ 重要提醒</b><br>
您在 <b>PHQ-9 第 9 题（自伤 / 自杀念头）</b>选择了非"完全不会"的选项。<br>
无论总分多少，<b>请立即</b>拨打以下任一热线，或告知一位你信任的家人 / 朋友：<br>
　📞 全国 24h 心理援助热线：<b>400-161-9995</b><br>
　📞 天津心理援助热线：<b>022-88188858</b><br>
　📞 教育部高校心理援助热线：<b>010-67440033</b>
</div>
            """, unsafe_allow_html=True)

        # ---------- 双重得分卡 ----------
        col_score1, col_score2, col_score3 = st.columns([1, 1, 2])
        with col_score1:
            st.markdown(f"""
<div class="score-card">
<div class="score-label">PHQ-9 总分</div>
<div class="score-num" style="color:{phq9_sev['color']}">{phq9_total}/27</div>
<div style="margin-top:6px; color:{phq9_sev['color']}; font-weight:700;">{phq9_sev['level']}</div>
<div style="margin-top:8px; font-size:12px; color:#666;">{phq9_sev['interpretation']}</div>
</div>
            """, unsafe_allow_html=True)
        with col_score2:
            # 等级判定以 PHQ-9 量表临床切点为主（Kroenke 2001）
            ml_advice = risk_label_and_advice(result["final_proba"], "student",
                                             scale_score=phq9_total)
            st.markdown(f"""
<div class="score-card">
<div class="score-label">综合风险（量表 + ML）</div>
<div class="score-num" style="color:{ml_advice['color']}">{result['final_proba']*100:.1f}%</div>
<div style="margin-top:6px; color:{ml_advice['color']}; font-weight:700;">{ml_advice['level']}</div>
<div style="margin-top:8px; font-size:12px; color:#666;">等级以 PHQ-9 量表为准 + ML 数值供参考</div>
</div>
            """, unsafe_allow_html=True)
        with col_score3:
            st.plotly_chart(risk_gauge(result["final_proba"], ml_advice["level"]),
                           use_container_width=True)

        # ---------- 综合判读 ----------
        st.markdown("### 🩺 综合判读")
        # 双重判断逻辑
        if phq9_total >= 10 and result["final_proba"] >= 0.5:
            verdict = "**量表与模型一致提示中等及以上抑郁风险**，建议尽快寻求专业评估。"
            verdict_color = "#F25F5C"
        elif phq9_total >= 10:
            verdict = "**PHQ-9 量表提示抑郁症状显著**，但风险因素相对可控。建议关注当前症状，必要时寻求专业评估。"
            verdict_color = "#FF9F45"
        elif result["final_proba"] >= 0.5:
            verdict = "**风险因素较多**，但当前症状尚不典型。建议关注生活方式调整，预防发病。"
            verdict_color = "#FFE066"
        else:
            verdict = "**量表与模型均提示低风险**，建议保持当前生活方式与社交节奏。"
            verdict_color = "#A6E3A1"

        st.markdown(f"""
<div style="background:{verdict_color}22; border-left:4px solid {verdict_color};
padding:14px 18px; border-radius:6px; font-size:15px;">
{verdict}
</div>
        """, unsafe_allow_html=True)

        # ---------- 三模型详情 + 贡献图 ----------
        st.markdown("### 🔬 模型细节")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.markdown(f"""
**风险评估细分：**
- 随机森林：{result['rf_proba']:.3f}
- 梯度提升：{result['gb_proba']:.3f}
- 逻辑回归：{result['lr_proba']:.3f}
- ML 集成：{result['ml_proba']:.3f}（占 40%）
- 量表归一化：{result['scale_proba']:.3f}（占 60%）
- **综合风险：{result['final_proba']:.3f}**
            """)
        with col_b:
            labels_map = column_labels("student")
            display_labels = [labels_map.get(f, f) for f in result["features"]]
            st.plotly_chart(
                shap_bar(display_labels, result["contributions"],
                        title="本次评估中各风险因素的贡献分解"),
                use_container_width=True,
            )
            st.caption("💡 **怎么看这张图：** 蓝色条（向左）= 该因素**降低**了你的抑郁风险；"
                      "红色条（向右）= 该因素**抬升**了你的抑郁风险。条越长，影响越大。")

        # ---------- 临床建议 ----------
        st.markdown("### 💊 个性化建议（基于 PHQ-9 得分）")
        for tip in phq9_clinical_advice(phq9_total, phq9_q9):
            st.markdown(f"- {tip}")

        st.markdown("---")
        st.caption("💡 本评估结果由 **PHQ-9 临床量表（Kroenke, 2001）+ 风险因素 ML 模型** 双重判定。"
                   "中度及以上风险务必前往三甲医院精神 / 心理科评估。")

        # ---------- 保存评估上下文，供 LLM 助手使用 ----------
        labels_map_save = column_labels("student")
        contribs_pairs = sorted(
            zip(result["features"], result["contributions"]),
            key=lambda p: abs(p[1]), reverse=True,
        )
        top3 = [labels_map_save.get(f, f) for f, _ in contribs_pairs[:3]]
        st.session_state["llm_ctx"] = {
            "group": "student",
            "scale_score": phq9_total,
            "severity": phq9_sev["level"],
            "ml_proba": result["final_proba"],
            "top_factors": top3,
            "q9_positive": phq9_q9 >= 1,
        }
        # 记录提交时的表单"指纹"，用于检测后续修改
        st.session_state["llm_form_signature"] = (
            "student", phq9_total, age, gender, grade, major,
            sleep, exercise, screen, academic, financial,
            relationship, social, family_hist, childhood,
            chronic, smoking, drinking,
        )
        # 新评估开始 → 重置聊天历史
        st.session_state["llm_messages"] = []


# ============================================================
# 中老年版（CES-D 10）
# ============================================================
else:
    st.markdown('<div class="scale-title">第一部分：CES-D 10 抑郁症状量表（CHARLS 标准）</div>',
               unsafe_allow_html=True)
    st.markdown(
        '<div class="scale-subtitle">在过去 <b>一周</b> 内，您有多少天有以下感受？</div>',
        unsafe_allow_html=True,
    )

    cesd_responses = []
    for i, q in enumerate(CESD10_QUESTIONS):
        choice = st.radio(
            q,
            options=CESD10_OPTIONS,
            index=0,
            horizontal=True,
            key=f"cesd_{i}",
        )
        cesd_responses.append(CESD10_OPTION_VALUES[CESD10_OPTIONS.index(choice)])

    cesd_total = cesd10_total(cesd_responses)

    st.markdown('<div class="scale-title">第二部分：基本信息</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        age = st.number_input("年龄", 45, 95, 65)
    with c2:
        gender = st.selectbox("性别", ["男", "女"])
    with c3:
        education = st.selectbox("教育程度",
                                ["未上学", "小学", "初中", "高中", "大专及以上"])
    with c4:
        region = st.selectbox("居住地区", ["城市", "城镇", "农村"])

    st.markdown('<div class="scale-title">第三部分：生活与健康</div>', unsafe_allow_html=True)
    # Row 1：3 个 slider 同类对齐
    c1, c2, c3 = st.columns(3)
    with c1:
        sleep = st.slider("平均每日睡眠时长（小时）", 3.0, 11.0, 6.5, 0.5)
    with c2:
        chronic_count = st.slider("慢性病数量", 0, 8, 1)
    with c3:
        adl = st.slider("ADL 生活自理能力（满分 14）", 6.0, 14.0, 13.0, 0.5)

    # Row 2：BMI slider + 经济水平 selectbox（视觉高度接近）
    c1, c2 = st.columns(2)
    with c1:
        bmi = st.slider("BMI", 14.0, 40.0, 23.0, 0.5)
    with c2:
        income = st.selectbox("家庭经济水平", ["低", "中", "高"])

    st.markdown('<div class="scale-title">第四部分：社会参与与生活习惯</div>',
               unsafe_allow_html=True)
    # Row 1：2 个 slider
    c1, c2 = st.columns(2)
    with c1:
        social = st.slider("过去一个月社会活动种类", 0, 8, 2)
    with c2:
        contact = st.slider("子女月均联系次数", 0, 30, 8)

    # Row 2：3 个 checkbox 同类对齐（独居挪到这里和吸烟/饮酒一起）
    c1, c2, c3 = st.columns(3)
    with c1:
        living_alone = st.checkbox("是否独居")
    with c2:
        smoking = st.checkbox("吸烟")
    with c3:
        drinking = st.checkbox("规律饮酒")

    # 保存当前表单"指纹"，供 sidebar 检测是否需要重新提交
    st.session_state["current_form_signature"] = (
        "elderly", cesd_total, age, gender, education, region,
        living_alone, sleep, chronic_count, adl, bmi, income,
        social, contact, smoking, drinking,
    )

    submitted = st.button("🔬 提交评估", type="primary", use_container_width=True)

    if submitted:
        cesd_sev = cesd10_severity(cesd_total)

        edu_num = {"未上学": 0, "小学": 6, "初中": 9,
                   "高中": 12, "大专及以上": 15}[education]
        income_num = {"低": 0, "中": 1, "高": 2}[income]
        x_row = pd.DataFrame([{
            "年龄": age,
            "性别_女": int(gender == "女"),
            "教育年数": edu_num,
            "是否独居": int(living_alone),
            "收入_数值": income_num,
            "慢性病数量": chronic_count,
            "ADL生活自理能力": adl,
            "睡眠时长_小时": sleep,
            "社会活动参与度": social,
            "子女月联系次数": contact,
            "吸烟": int(smoking),
            "饮酒": int(drinking),
            "BMI": bmi,
            "城乡_农村": int(region == "农村"),
        }])
        bundle = load_model_bundle("elderly")
        # CES-D 总分传入，让最终风险随量表分变化
        result = predict_with_explain(bundle, x_row,
                                     scale_score=cesd_total, scale_max=30)
        # 等级判定以 CES-D 量表临床切点为主
        ml_advice = risk_label_and_advice(result["final_proba"], "elderly",
                                         scale_score=cesd_total)

        st.markdown("---")
        st.markdown("## 📋 综合评估结果")

        col_score1, col_score2, col_score3 = st.columns([1, 1, 2])
        with col_score1:
            st.markdown(f"""
<div class="score-card">
<div class="score-label">CES-D 10 总分</div>
<div class="score-num" style="color:{cesd_sev['color']}">{cesd_total}/30</div>
<div style="margin-top:6px; color:{cesd_sev['color']}; font-weight:700;">{cesd_sev['level']}</div>
<div style="margin-top:8px; font-size:12px; color:#666;">{cesd_sev['interpretation']}</div>
</div>
            """, unsafe_allow_html=True)
        with col_score2:
            st.markdown(f"""
<div class="score-card">
<div class="score-label">综合风险（量表 + ML）</div>
<div class="score-num" style="color:{ml_advice['color']}">{result['final_proba']*100:.1f}%</div>
<div style="margin-top:6px; color:{ml_advice['color']}; font-weight:700;">{ml_advice['level']}</div>
<div style="margin-top:8px; font-size:12px; color:#666;">基于躯体健康、社会参与等因素</div>
</div>
            """, unsafe_allow_html=True)
        with col_score3:
            st.plotly_chart(risk_gauge(result["final_proba"], ml_advice["level"]),
                           use_container_width=True)

        st.markdown("### 🩺 综合判读")
        if cesd_total >= 10 and result["final_proba"] >= 0.5:
            verdict = "**量表与模型一致提示明显抑郁风险**，建议立即寻求专业评估。"
            verdict_color = "#F25F5C"
        elif cesd_total >= 10:
            verdict = "**CES-D 量表提示抑郁症状阳性**，建议家属陪同前往老年精神 / 心理科评估。"
            verdict_color = "#FF9F45"
        elif result["final_proba"] >= 0.5:
            verdict = "**躯体与社会风险因素较多**，建议加强家庭关怀与社区参与，定期复测。"
            verdict_color = "#FFE066"
        else:
            verdict = "**量表与模型均提示低风险**，建议保持当前生活与社交节奏。"
            verdict_color = "#A6E3A1"

        st.markdown(f"""
<div style="background:{verdict_color}22; border-left:4px solid {verdict_color};
padding:14px 18px; border-radius:6px; font-size:15px;">
{verdict}
</div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔬 模型细节")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.markdown(f"""
**风险评估细分：**
- 随机森林：{result['rf_proba']:.3f}
- 梯度提升：{result['gb_proba']:.3f}
- 逻辑回归：{result['lr_proba']:.3f}
- ML 集成：{result['ml_proba']:.3f}（占 40%）
- 量表归一化：{result['scale_proba']:.3f}（占 60%）
- **综合风险：{result['final_proba']:.3f}**
            """)
        with col_b:
            labels_map = column_labels("elderly")
            display_labels = [labels_map.get(f, f) for f in result["features"]]
            st.plotly_chart(
                shap_bar(display_labels, result["contributions"],
                        title="本次评估中各风险因素的贡献分解"),
                use_container_width=True,
            )

        st.markdown("### 💊 个性化建议（基于 CES-D 10 得分）")
        for tip in cesd10_clinical_advice(cesd_total):
            st.markdown(f"- {tip}")

        st.markdown("---")
        st.caption("💡 本评估结果由 **CES-D 10（CHARLS 采用版本）量表 + 风险因素 ML 模型** 双重判定。"
                   "中老年群体若量表 ≥10 分，建议家属陪同至老年精神心理科或心身医学科评估。")

        # ---------- 保存评估上下文，供 LLM 助手使用 ----------
        labels_map_save = column_labels("elderly")
        contribs_pairs = sorted(
            zip(result["features"], result["contributions"]),
            key=lambda p: abs(p[1]), reverse=True,
        )
        top3 = [labels_map_save.get(f, f) for f, _ in contribs_pairs[:3]]
        st.session_state["llm_ctx"] = {
            "group": "elderly",
            "scale_score": cesd_total,
            "severity": cesd_sev["level"],
            "ml_proba": result["final_proba"],
            "top_factors": top3,
            "q9_positive": False,  # CES-D 10 没有自杀念头单独题项
        }
        # 记录提交时的表单"指纹"
        st.session_state["llm_form_signature"] = (
            "elderly", cesd_total, age, gender, education, region,
            living_alone, sleep, chronic_count, adl, bmi, income,
            social, contact, smoking, drinking,
        )
        st.session_state["llm_messages"] = []


# ============================================================
# 🤖 AI 心理健康助手（DeepSeek 大模型 · 大赛合规清单内）
# ============================================================
# 放在左侧侧边栏。@st.fragment 必须在调用位置渲染，
# 所以 fragment 内部不能再用 with st.sidebar，要在外部调用时进入 sidebar。

@st.fragment
def render_llm_chat_content():
    """聊天内容（仅内容，不含 sidebar 容器切换）。
    fragment 限制：渲染必须在调用位置，所以 with st.sidebar 必须在外面。
    """
    st.markdown("### 🤖 AI 心理健康助手")

    if "llm_ctx" not in st.session_state:
        st.caption("DeepSeek · 大赛合规清单 AI 工具")
        st.info("👆 先填写并提交评估，我才能基于你的结果回答问题")
        return

    # 检测当前表单是否与上次提交一致
    current_sig = st.session_state.get("current_form_signature")
    saved_sig = st.session_state.get("llm_form_signature")
    is_stale = (current_sig is not None and saved_sig is not None
                and current_sig != saved_sig)

    if is_stale:
        st.caption("DeepSeek · 大赛合规清单 AI 工具")
        st.warning(
            "📝 **问卷已变更**\n\n"
            "你修改了问卷选项。请滚动到顶部，重新点击「🔬 提交评估」"
            "以更新评估结果，AI 助手才能基于最新结果回答。\n\n"
            "或者你也可以清除上次结果："
        )
        if st.button("🗑️ 清除上次评估结果", use_container_width=True,
                    key="clear_stale_ctx"):
            for k in ("llm_ctx", "llm_form_signature", "llm_messages"):
                st.session_state.pop(k, None)
            st.rerun(scope="fragment")
        return

    ctx = st.session_state["llm_ctx"]
    st.caption(f"DeepSeek 大模型 · 已读取评估结果（{ctx['severity']}）")

    if not llm_is_configured():
        st.warning("""
**未配置 API Key**

配置方法：
1. 注册 [DeepSeek](https://platform.deepseek.com/)
2. 项目根目录创建 `.env`：
```
DEEPSEEK_API_KEY=sk-你的key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```
3. 重启 streamlit
        """)
        return

    # ============ 输入框置于顶部 ============
    user_input = st.chat_input("有任何疑问？在这里提问")
    pending = st.session_state.pop("llm_pending", None)
    prompt = pending or user_input

    # 推荐问题（仅首次未输入时显示，紧贴输入框下方）
    has_messages = bool(st.session_state.get("llm_messages"))
    if not has_messages and not prompt:
        sugg = get_suggested_questions(ctx["group"], ctx["scale_score"])
        st.caption("💡 推荐问题（点击直接发送）")
        for i, q in enumerate(sugg):
            if st.button(q, key=f"sugg_sb_{i}", use_container_width=True):
                st.session_state["llm_pending"] = q
                st.rerun(scope="fragment")

    # 写入用户消息到历史
    if prompt:
        st.session_state.setdefault("llm_messages", []).append(
            {"role": "user", "content": prompt}
        )

    # ============ 对话历史置于下方 ============
    if st.session_state.get("llm_messages"):
        st.caption("💬 对话")
        chat_container = st.container(height=380)
        with chat_container:
            # 显示已有历史
            for msg in st.session_state["llm_messages"]:
                avatar = "🩺" if msg["role"] == "assistant" else "🧑"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

            # 流式生成最新回复
            if prompt:
                with st.chat_message("assistant", avatar="🩺"):
                    placeholder = st.empty()
                    full_response = ""
                    try:
                        for token in llm_chat_stream(
                            user_message=prompt,
                            history=st.session_state["llm_messages"][:-1],
                            group=ctx["group"],
                            scale_score=ctx["scale_score"],
                            severity=ctx["severity"],
                            ml_proba=ctx["ml_proba"],
                            top_factors=ctx["top_factors"],
                            q9_positive=ctx["q9_positive"],
                        ):
                            full_response += token
                            placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                    except Exception as e:
                        full_response = (f"⚠️ AI 助手暂时不可用：{e}\n\n"
                                       f"请稍后重试，或拨打热线 **400-161-9995**。")
                        placeholder.error(full_response)

                    st.session_state["llm_messages"].append(
                        {"role": "assistant", "content": full_response}
                    )

        # 清空按钮
        if st.button("🔄 清空对话", use_container_width=True, key="clear_chat"):
            st.session_state["llm_messages"] = []
            st.rerun(scope="fragment")
    elif not prompt:
        # 首次进入且无对话时，简短一行引导（不再占大段空白）
        st.caption("👆 在输入框打字，或点击上方推荐问题开始对话")

    st.caption("⚠️ 仅供参考，不替代医生诊断。紧急情况 400-161-9995")


# 在 sidebar 中调用 fragment（外部进入 sidebar，内部不再切换 container）
with st.sidebar:
    st.markdown("---")
    render_llm_chat_content()
