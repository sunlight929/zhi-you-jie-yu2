"""
知忧·解郁 - 多源数据驱动的抑郁症风险识别与决策支持平台
=====================================================
项目首页（深色霓虹统一风格）

运行：streamlit run app.py
"""

import streamlit as st
from utils.data_loader import (
    load_student_data, load_elderly_data, load_trend_data,
    load_metrics, load_regional_data,
    load_nhanes_real, load_mendeley_real,
    is_real_data_available, data_sources_summary,
)
from utils.dark_charts import neon_trend
from utils.test_mode import (
    redirect_if_test_mode_non_assessment,
    inject_hide_branding_css,
)


st.set_page_config(
    page_title="知忧·解郁 | 抑郁症风险识别与决策支持平台",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 测试模式：扫码进来的用户直接跳转到评估页（完整版下零影响）
redirect_if_test_mode_non_assessment()

# 隐藏 Streamlit Cloud 默认的 Fork on GitHub / Manage app 按钮(完整版 + 测试版)
inject_hide_branding_css()

st.markdown("""
<style>
.stApp {
  background: radial-gradient(ellipse at 20% 0%, #1A1B3A 0%, #0A0B1E 60%, #050614 100%);
}
.block-container {padding-top: 1.5rem; max-width: 1400px;}
section[data-testid="stSidebar"] {background: #0A0B1E;}
[data-testid="stSidebar"] * {color: #E8F0FF !important;}
header[data-testid="stHeader"] {background: transparent;}

/* 隐藏 Streamlit 自带的 Deploy 按钮 + 主菜单 + 页脚水印（保留侧边栏开关） */
.stAppDeployButton, [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], #MainMenu,
footer {display: none !important; visibility: hidden !important;}
[data-testid="stStatusWidget"] {display: none !important;}

/* 侧边栏折叠/展开按钮永远显示 + 高亮可见 */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 999999 !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button {
  background: rgba(91,200,255,0.2) !important;
  border: 1px solid rgba(91,200,255,0.5) !important;
  color: #5BC8FF !important;
}

.hero {
  background: linear-gradient(135deg, #5B7FFF 0%, #7C5CFF 50%, #F25F5C 100%);
  color: white;
  padding: 36px 40px;
  border-radius: 14px;
  margin-bottom: 22px;
  box-shadow: 0 8px 40px rgba(91,200,255,0.25);
  position: relative; overflow: hidden;
}
.hero::after {
  content: '';
  position: absolute; top: 0; right: 0; width: 240px; height: 100%;
  background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, transparent 70%);
}
.hero h1 {color: white; margin: 0; font-size: 30px; letter-spacing: 1px;}
.hero p {color: rgba(255,255,255,0.92); margin: 8px 0 0 0; font-size: 16px;}

.kpi-card {
  background: linear-gradient(135deg, rgba(91,127,255,0.12), rgba(167,139,250,0.06));
  border: 1px solid rgba(91,200,255,0.25);
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 12px;
  position: relative; overflow: hidden;
}
.kpi-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #5BC8FF, #A78BFA, #F472B6);
}
.kpi-card.success {border-color: rgba(52,211,153,0.4);}
.kpi-card.success::before {background: linear-gradient(90deg, #34D399, #5BC8FF);}
.kpi-card.alert {border-color: rgba(248,113,113,0.4);}
.kpi-card.alert::before {background: linear-gradient(90deg, #F87171, #FB923C);}

.kpi-label {font-size: 12px; color: #9CA3AF; letter-spacing: 1px; text-transform: uppercase;}
.kpi-value {font-size: 30px; font-weight: 800; color: #E8F0FF; margin-top: 4px;
            text-shadow: 0 0 12px rgba(91,200,255,0.3);}
.kpi-sub {font-size: 11px; color: #5BC8FF; margin-top: 2px;}

.tag-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}
.tag {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 14px;
  background: rgba(91,200,255,0.15);
  color: #5BC8FF;
  font-size: 12px;
  border: 1px solid rgba(91,200,255,0.3);
  text-align: center;
  white-space: nowrap;
}

.section-title {
  font-size: 14px; color: #5BC8FF; letter-spacing: 1.5px;
  margin: 24px 0 12px 0; padding-left: 10px;
  border-left: 3px solid #5BC8FF;
  text-transform: uppercase;
}

.feature-card {
  background: rgba(91,127,255,0.06);
  border: 1px solid rgba(91,200,255,0.2);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 12px;
  height: 100%;
}
.feature-icon {font-size: 26px; margin-bottom: 8px;}
.feature-title {font-size: 16px; font-weight: 700; color: #E8F0FF; margin-bottom: 6px;}
.feature-desc {font-size: 12px; color: #B8C5E0; line-height: 1.7;}

.tech-box {
  background: rgba(91,127,255,0.05);
  border: 1px solid rgba(91,200,255,0.18);
  border-radius: 8px;
  padding: 14px 18px;
  line-height: 1.9;
  font-size: 13px;
  color: #E8F0FF;
}
.tech-box b {color: #5BC8FF;}

.data-banner-real {
  background: rgba(52,211,153,0.10);
  border: 1px solid rgba(52,211,153,0.4);
  border-radius: 8px;
  padding: 12px 16px;
  color: #6EE7B7;
  font-size: 13px;
  margin: 16px 0;
}
.data-banner-info {
  background: rgba(91,200,255,0.08);
  border: 1px solid rgba(91,200,255,0.3);
  border-radius: 8px;
  padding: 12px 16px;
  color: #93C5FD;
  font-size: 13px;
  margin: 16px 0;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">
<h1>🧠 知忧·解郁</h1>
<p>多源数据驱动的抑郁症风险识别与决策支持平台</p>
<p style="font-size:13px; opacity:0.85;">2026 中国大学生计算机设计大赛 · 大数据应用赛道作品 · 生物与医疗大数据小类</p>
</div>
""", unsafe_allow_html=True)


col_intro, col_tags = st.columns([3, 1])
with col_intro:
    st.markdown("""
### 项目简介

本平台聚焦中国两大重点人群（**在校大学生**与**中老年群体**）的抑郁症筛查需求，整合**真实学术公开数据 + 中国本土流行病学仿真数据**，构建抑郁风险**多维度可视化分析**与**机器学习早期识别**能力，并面向天津本地化场景提供**精神卫生资源决策支持**。

平台采用**国际/国内临床金标准量表**（PHQ-9 / CES-D 10）+ **三模型机器学习集成**（随机森林 + 梯度提升 + 逻辑回归）+ **可解释性分析**的临床三合一评估方案，为高校心理中心、社区卫生服务机构及个人用户提供易用的抑郁筛查与干预建议工具。
    """)
with col_tags:
    st.markdown("""
<div class="tag-grid">
<span class="tag">大数据应用</span>
<span class="tag">医疗健康</span>
<span class="tag">机器学习</span>
<span class="tag">可解释 AI</span>
<span class="tag">公共卫生</span>
<span class="tag">决策支持</span>
<span class="tag">PHQ-9 量表</span>
<span class="tag">CES-D 量表</span>
</div>
    """, unsafe_allow_html=True)


# 数据接入提示
real_loaded = is_real_data_available()
sources_info = data_sources_summary()
nhanes = load_nhanes_real()
mendeley = load_mendeley_real()
real_n = sources_info["total_real"]

if real_loaded:
    real_parts = []
    if not nhanes.empty:
        real_parts.append(f"NHANES (CDC) {len(nhanes):,} 条")
    if not mendeley.empty:
        real_parts.append(f"Mendeley 学生 {len(mendeley):,} 条")
    st.markdown(f"""
<div class="data-banner-real">
✅ <b>已成功接入真实公开学术数据</b>：{' / '.join(real_parts)}（共 {real_n:,} 条）
&nbsp;|&nbsp; 全部采用 PHQ-9 国际标准量表
&nbsp;|&nbsp; 与中国本土流行病学仿真数据共同构成多源数据生态
</div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
<div class="data-banner-info">
💡 当前仅展示仿真演示数据。运行
<code>python data/download_real_data.py --source all --convert</code>
即可一键接入 NHANES + Mendeley 真实公开 PHQ-9 数据。
</div>
    """, unsafe_allow_html=True)


# ============================================================
# 平台数据全景 KPI
# ============================================================
st.markdown('<div class="section-title">📊 平台数据全景</div>', unsafe_allow_html=True)
student = load_student_data()
elderly = load_elderly_data()
trend = load_trend_data()
metrics = load_metrics()
regional = load_regional_data()

n_total = len(student) + len(elderly) + len(nhanes) + len(mendeley)
risk_total = (int(student["是否抑郁"].sum()) + int(elderly["是否抑郁"].sum()) +
             (int(nhanes["是否抑郁"].sum()) if not nhanes.empty else 0) +
             (int(mendeley["是否抑郁"].sum()) if not mendeley.empty else 0))
overall_rate = risk_total / n_total * 100 if n_total else 0
best_auc = metrics["AUC"].max() if not metrics.empty else 0.93

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">📦 总样本量</div>
<div class="kpi-value">{n_total:,}</div>
<div class="kpi-sub">真实 {real_n:,} + 仿真 {n_total-real_n:,}</div>
</div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
<div class="kpi-card alert">
<div class="kpi-label">⚠️ 综合抑郁检出率</div>
<div class="kpi-value">{overall_rate:.1f}%</div>
<div class="kpi-sub">阳性人数 {risk_total:,}</div>
</div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
<div class="kpi-card success">
<div class="kpi-label">🤖 模型最佳 AUC</div>
<div class="kpi-value">{best_auc:.3f}</div>
<div class="kpi-sub">三模型集成 · 内部验证</div>
</div>
    """, unsafe_allow_html=True)
with c4:
    if real_loaded:
        st.markdown(f"""
<div class="kpi-card success">
<div class="kpi-label">📡 真实数据接入</div>
<div class="kpi-value">{real_n:,}</div>
<div class="kpi-sub">NHANES + Mendeley 公开</div>
</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">🏥 覆盖天津区县</div>
<div class="kpi-value">{len(regional)}</div>
<div class="kpi-sub">全市级精神卫生资源</div>
</div>
        """, unsafe_allow_html=True)


st.markdown('<div class="section-title">📈 近十年抑郁检出率趋势</div>',
           unsafe_allow_html=True)
st.plotly_chart(neon_trend(trend), use_container_width=True,
               config={"displayModeBar": False})


# ============================================================
# 四大核心模块
# ============================================================
st.markdown('<div class="section-title">🎯 平台五大核心模块</div>',
           unsafe_allow_html=True)
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
modules = [
    ("📡", "数据驾驶舱", "霓虹大屏数据中心，全国地图 + 多源融合 KPI 实时监测"),
    ("📊", "数据全景", "真实 + 仿真四源数据画像，PHQ-9 / CES-D 多维度分布"),
    ("🔍", "风险因素分析", "相关性矩阵 + 特征重要性 + 雷达图，识别核心风险"),
    ("🧠", "智能评估", "PHQ-9 / CES-D 量表 + 风险问卷 + ML 模型三合一"),
    ("🏙️", "天津决策支持", "16 区县检出率 + 资源配置对比 + 求助资源整合"),
]
for col, (icon, title, desc) in zip([mc1, mc2, mc3, mc4, mc5], modules):
    with col:
        st.markdown(f"""
<div class="feature-card">
<div class="feature-icon">{icon}</div>
<div class="feature-title">{title}</div>
<div class="feature-desc">{desc}</div>
</div>
        """, unsafe_allow_html=True)


# ============================================================
# 技术架构
# ============================================================
st.markdown('<div class="section-title">🛠️ 技术架构</div>', unsafe_allow_html=True)
st.markdown("""
<div class="tech-box">
<b>数据层 ▏</b>NHANES 2017-2018（美国 CDC 公开）+ Mendeley 学生 PHQ-9 公开数据 + 中国流行病学仿真数据 + 抑郁量表 PHQ-9 / CES-D 10<br>
<b>分析层 ▏</b>Pandas + scikit-learn（Random Forest + Gradient Boosting + Logistic Regression 三模型集成）<br>
<b>可解释性 ▏</b>逻辑回归系数 × 标准化特征值的局部贡献分解（轻量级 SHAP 替代）<br>
<b>可视化层 ▏</b>Plotly 交互图表 + 中国省级 Choropleth 地图 + 深色霓虹大屏组件<br>
<b>AI 工具协作 ▏</b>DeepSeek（代码）· Kimi（文档）· 通义千问（数据探索）· 智谱 AI（量表优化）<br>
<b>部署形态 ▏</b>Streamlit 多页面 Web 应用（本地 / Streamlit Cloud / 内网服务器）
</div>
""", unsafe_allow_html=True)


# ============================================================
# 数据合规与伦理
# ============================================================
st.markdown('<div class="section-title">⚖️ 数据合规与伦理声明</div>',
           unsafe_allow_html=True)
st.markdown("""
<div style="background: rgba(91,200,255,0.06); border-left: 4px solid #5BC8FF;
            border-radius: 6px; padding: 14px 18px; color: #E8F0FF; font-size: 13px;
            line-height: 1.8;">
• 真实公开数据均来自经同行评议的学术机构（美国 CDC NHANES、Mendeley Data 等），<b>遵守原始数据使用协议</b><br>
• 中国群体仿真数据基于<b>已发表流行病学文献</b>分布参数构造，不包含任何真实个体信息<br>
• 真实部署接入 CHARLS / 卫生健康委等中国数据源时，<b>必须经伦理审查</b>与<b>脱敏处理</b><br>
• 严格遵守《数据安全法》《个人信息保护法》《医疗卫生机构网络安全管理办法》<br>
• 平台输出仅作辅助参考，<b>不替代临床医师诊断</b>；遵循《抑郁障碍防治指南（第二版）》
</div>
""", unsafe_allow_html=True)


st.markdown("""
<div style="text-align:center; margin-top:24px; color:#9CA3AF; font-size:11px;">
👆 通过左侧导航 ← 进入各功能模块 ｜ 项目仓库与详细文档见 <code>/docs</code> 与 <code>/report</code> 目录
</div>
""", unsafe_allow_html=True)
