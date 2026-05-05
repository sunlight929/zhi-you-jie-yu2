"""风险因素分析（深色统一风格）：相关性、特征重要性、模型对比、雷达图。"""

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import (
    load_student_data, load_elderly_data,
    load_importance, load_metrics,
)
from utils.dark_charts import (
    neon_heatmap, neon_horizontal_bar, neon_radar,
    NEON_BLUE, NEON_PINK, NEON_PURPLE, NEON_GREEN, TEXT_LIGHT, BG_DARK,
)

st.set_page_config(page_title="风险因素分析 | 知忧·解郁", page_icon="🔍", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1500px;}
.section-title {
  font-size: 14px; color: #5BC8FF; letter-spacing: 1.5px;
  border-left: 3px solid #5BC8FF;
  padding-left: 10px; margin: 18px 0 10px 0;
  text-transform: uppercase;
}
.findings {
  background: rgba(91,127,255,0.06);
  border: 1px solid rgba(91,200,255,0.2);
  border-radius: 8px; padding: 14px 18px;
  font-size: 14px; line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 风险因素分析")
st.caption("从相关性、机器学习特征重要性、模型对比三个层面识别核心风险因子")

tab_s, tab_e, tab_metrics = st.tabs(["👨‍🎓 学生群体", "👴 中老年群体", "📐 模型性能"])


# ============================================================
# 学生
# ============================================================
with tab_s:
    df = load_student_data()
    imp = load_importance("student")

    st.markdown('<div class="section-title">▍核心变量相关性矩阵</div>',
               unsafe_allow_html=True)
    cols_s = ["PHQ9分数", "睡眠时长_小时", "学业压力", "经济压力",
              "亲密关系质量", "社会支持", "每周运动次数",
              "日均屏幕时长_小时", "童年不良经历", "家族史"]
    st.plotly_chart(neon_heatmap(df[cols_s].corr().round(2),
                                "学生群体核心变量 Pearson 相关系数"),
                   use_container_width=True,
                   config={"displayModeBar": False})
    st.caption("解读：**社会支持**、**亲密关系**与 PHQ-9 强负相关；**学业压力**、**经济压力**、**童年不良经历**强正相关。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">▍随机森林特征重要性</div>',
                   unsafe_allow_html=True)
        top_imp = imp.head(12).copy()
        st.plotly_chart(
            neon_horizontal_bar(top_imp, "随机森林重要性", "特征",
                              "Top 12 特征", is_percent=False),
            use_container_width=True, config={"displayModeBar": False},
        )
    with col2:
        st.markdown('<div class="section-title">▍核心 6 因子雷达</div>',
                   unsafe_allow_html=True)
        top6 = imp.head(6)
        st.plotly_chart(neon_radar(top6["特征"].tolist(),
                                   top6["随机森林重要性"].tolist(),
                                   "RF 重要性 (Top 6)"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    st.markdown('<div class="section-title">▍逻辑回归系数（方向性）</div>',
               unsafe_allow_html=True)
    show = imp.copy().sort_values("逻辑回归系数",
                                 key=lambda x: x.abs(),
                                 ascending=False).head(12)
    show["效应方向"] = show["逻辑回归系数"].apply(
        lambda x: "↑ 升高风险" if x > 0 else "↓ 降低风险")
    st.dataframe(
        show[["特征", "逻辑回归系数", "效应方向", "随机森林重要性"]].round(3),
        use_container_width=True, hide_index=True,
    )

    st.markdown('<div class="section-title">▍核心风险因子总结</div>',
               unsafe_allow_html=True)
    st.markdown("""
<div class="findings">
<b style="color:#34D399">🛡️ 保护因素（应增强）</b><br>
• <b>社会支持</b>：模型贡献度最高的保护因子<br>
• <b>充足睡眠</b>：每多睡 1 小时显著降低风险<br>
• <b>良好亲密关系</b>：朋友 / 家人 / 伴侣的支持网络<br>
• <b>规律运动</b>：每周 3 次以上中等强度运动<br><br>
<b style="color:#F87171">⚠️ 危险因素（应干预）</b><br>
• <b>学业压力</b>：尤其大四毕业季和研究生群体突出<br>
• <b>经济压力</b>：影响日常情绪与未来预期<br>
• <b>童年不良经历</b>：家庭暴力、忽视、丧亲等长期累积效应<br>
• <b>家族抑郁史</b>：遗传易感性叠加环境因素<br>
• <b>过长屏幕时间</b>：影响睡眠质量和现实社交
</div>
    """, unsafe_allow_html=True)


# ============================================================
# 中老年
# ============================================================
with tab_e:
    df = load_elderly_data()
    imp = load_importance("elderly")

    st.markdown('<div class="section-title">▍核心变量相关性矩阵</div>',
               unsafe_allow_html=True)
    cols_e = ["CESD分数", "ADL生活自理能力", "睡眠时长_小时", "慢性病数量",
              "社会活动参与度", "子女月联系次数", "BMI", "是否独居"]
    st.plotly_chart(neon_heatmap(df[cols_e].corr().round(2),
                                "中老年核心变量 Pearson 相关系数"),
                   use_container_width=True,
                   config={"displayModeBar": False})
    st.caption("解读：**ADL 自理能力**、**社会参与**与 CES-D 强负相关；**慢性病数量**、**独居**显著正相关。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">▍随机森林特征重要性</div>',
                   unsafe_allow_html=True)
        top_imp = imp.head(12).copy()
        st.plotly_chart(
            neon_horizontal_bar(top_imp, "随机森林重要性", "特征",
                              "Top 12 特征", is_percent=False),
            use_container_width=True, config={"displayModeBar": False},
        )
    with col2:
        st.markdown('<div class="section-title">▍核心 6 因子雷达</div>',
                   unsafe_allow_html=True)
        top6 = imp.head(6)
        st.plotly_chart(neon_radar(top6["特征"].tolist(),
                                   top6["随机森林重要性"].tolist(),
                                   "RF 重要性 (Top 6)"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    st.markdown('<div class="section-title">▍逻辑回归系数（方向性）</div>',
               unsafe_allow_html=True)
    show = imp.copy().sort_values("逻辑回归系数",
                                 key=lambda x: x.abs(),
                                 ascending=False).head(12)
    show["效应方向"] = show["逻辑回归系数"].apply(
        lambda x: "↑ 升高风险" if x > 0 else "↓ 降低风险")
    st.dataframe(
        show[["特征", "逻辑回归系数", "效应方向", "随机森林重要性"]].round(3),
        use_container_width=True, hide_index=True,
    )

    st.markdown('<div class="section-title">▍核心风险因子总结</div>',
               unsafe_allow_html=True)
    st.markdown("""
<div class="findings">
<b style="color:#34D399">🛡️ 保护因素</b><br>
• <b>ADL 自理能力</b>：日常生活独立性是最强保护因子<br>
• <b>充足睡眠</b>：随年龄增长，睡眠质量影响愈加显著<br>
• <b>社会参与</b>：广场舞、棋牌、社区活动等显著缓解抑郁<br>
• <b>子女联系</b>：高频家庭情感联结<br><br>
<b style="color:#F87171">⚠️ 危险因素</b><br>
• <b>慢性病共病</b>：每多 1 种慢性病，风险显著上升<br>
• <b>独居</b>：尤其农村空巢老人<br>
• <b>低教育 / 低收入</b>：双重弱势叠加<br>
• <b>农村居住</b>：精神卫生资源可及性低
</div>
    """, unsafe_allow_html=True)


# ============================================================
# 模型性能
# ============================================================
with tab_metrics:
    metrics = load_metrics()
    if metrics.empty:
        st.warning("尚未生成模型性能数据，请先运行 `python models/train_models.py`。")
    else:
        st.markdown('<div class="section-title">▍三模型性能对比</div>',
                   unsafe_allow_html=True)
        st.dataframe(metrics, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-title">▍性能可视化</div>',
                   unsafe_allow_html=True)
        m_long = metrics.melt(id_vars=["群体", "模型"],
                             value_vars=["准确率", "精确率", "召回率", "F1", "AUC"],
                             var_name="指标", value_name="数值")
        fig = px.bar(m_long, x="模型", y="数值", color="指标",
                    barmode="group", facet_col="群体",
                    color_discrete_sequence=[NEON_BLUE, NEON_PURPLE,
                                            NEON_PINK, NEON_GREEN, "#FACC15"])
        fig.update_layout(plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
                         font=dict(color=TEXT_LIGHT),
                         yaxis_title="性能值", height=400,
                         legend=dict(bgcolor="rgba(0,0,0,0)",
                                    font=dict(color=TEXT_LIGHT)))
        fig.update_xaxes(gridcolor="rgba(91,127,255,0.18)")
        fig.update_yaxes(range=[0, 1], gridcolor="rgba(91,127,255,0.18)")
        for ann in fig.layout.annotations:
            ann.font.color = TEXT_LIGHT
        st.plotly_chart(fig, use_container_width=True,
                       config={"displayModeBar": False})

        st.markdown("""
### 📝 模型选型说明

- **随机森林**：作为主预测模型，对非线性关系建模能力强、鲁棒性好
- **梯度提升**：精度通常最高，作为辅助验证
- **逻辑回归**：提供**可解释性** —— 系数符号即效应方向，便于临床 / 政策解读
- **集成策略**：最终风险概率取三模型平均，兼顾**准确性**与**可解释性**
- **类不平衡处理**：使用 `class_weight="balanced"` 提升少数类（抑郁阳性）召回率，
  符合医疗筛查"宁可错召不可漏诊"原则
        """)
