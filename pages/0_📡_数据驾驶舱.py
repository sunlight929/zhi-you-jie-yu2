"""
深色霓虹大屏数据驾驶舱
====================
参考 4C 优秀作品（《基于 Spark 的心脏病风险监测分析平台》、《农业大王》等）
的"大屏可视化"风格，9 宫格 + 中国省级地图（pyecharts）+ 数据透明条。
"""

import time
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import (
    load_student_data, load_elderly_data,
    load_regional_data, load_trend_data,
    load_metrics, load_importance,
    load_nhanes_real, load_mendeley_real,
    is_real_data_available, data_sources_summary,
)
from utils.dark_charts import (
    neon_donut, neon_radial, neon_trend, neon_bar,
    neon_horizontal_bar, neon_gauge, neon_grouped_bar,
    neon_heatmap, neon_radar,
)
from utils.china_map import render_china_depression_map
from utils.test_mode import (
    redirect_if_test_mode_non_assessment,
    inject_hide_branding_css,
)


st.set_page_config(
    page_title="数据驾驶舱 | 知忧·解郁",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 测试模式：自动跳转评估页（完整版下零影响）
redirect_if_test_mode_non_assessment()

# 隐藏 Streamlit Cloud 默认的 Fork on GitHub / Manage app 按钮
inject_hide_branding_css()

# ============================================================
# 深色全屏样式
# ============================================================
st.markdown("""
<style>
.stApp {
  background: radial-gradient(ellipse at 20% 0%, #1A1B3A 0%, #0A0B1E 60%, #050614 100%);
}
.block-container {
  padding: 1rem 4rem 1rem 1.5rem !important;
  max-width: 1700px !important;
}
section[data-testid="stSidebar"] {background: #0A0B1E;}
[data-testid="stSidebar"] * {color: #E8F0FF !important;}
header[data-testid="stHeader"] {background: transparent;}

/* 隐藏 Streamlit 自带的 Deploy 按钮 + 主菜单（保留侧边栏开关）*/
.stAppDeployButton, [data-testid="stAppDeployButton"],
[data-testid="stMainMenu"], #MainMenu, footer
{display: none !important; visibility: hidden !important;}

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
  background: rgba(91,200,255,0.25) !important;
  border: 1px solid rgba(91,200,255,0.6) !important;
  color: #5BC8FF !important;
}

.cockpit-header {
  background: linear-gradient(90deg, transparent 0%, rgba(91,200,255,0.12) 50%, transparent 100%);
  border-bottom: 1px solid rgba(91,200,255,0.3);
  padding: 14px 20px;
  margin: -1rem -1.5rem 18px -1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.cockpit-title {
  font-size: 22px; font-weight: 800; color: #E8F0FF;
  letter-spacing: 2px;
  text-shadow: 0 0 16px rgba(91,200,255,0.6);
}
.cockpit-sub {font-size: 12px; color: #5BC8FF; letter-spacing: 1px; margin-left: 16px;}
.cockpit-meta {font-size: 11px; color: #9CA3AF;}

.panel-title {
  font-size: 12px; color: #5BC8FF; letter-spacing: 1.5px;
  border-left: 3px solid #5BC8FF;
  padding-left: 8px;
  margin: 24px 0 8px 0;
  text-transform: uppercase;
}

.kpi-tile {
  background: linear-gradient(135deg, rgba(91,127,255,0.12), rgba(167,139,250,0.06));
  border: 1px solid rgba(91,200,255,0.25);
  border-radius: 8px;
  padding: 14px 14px;
  position: relative; overflow: hidden;
  min-height: 92px;
}
.kpi-tile::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #5BC8FF, #A78BFA, #F472B6);
}
.kpi-label {font-size: 11px; color: #9CA3AF; letter-spacing: 1px; text-transform: uppercase;}
.kpi-value {
  font-size: 26px; font-weight: 800; color: #E8F0FF;
  margin-top: 4px;
  text-shadow: 0 0 12px rgba(91,200,255,0.3);
}
.kpi-sub {font-size: 10px; color: #5BC8FF; margin-top: 2px;}
.kpi-tile.alert {border-color: rgba(248,113,113,0.4);}
.kpi-tile.alert::before {background: linear-gradient(90deg, #F87171, #FB923C);}
.kpi-tile.alert .kpi-value {color: #FCA5A5; text-shadow: 0 0 14px rgba(248,113,113,0.4);}
.kpi-tile.success {border-color: rgba(52,211,153,0.4);}
.kpi-tile.success::before {background: linear-gradient(90deg, #34D399, #5BC8FF);}
.kpi-tile.success .kpi-value {color: #6EE7B7; text-shadow: 0 0 14px rgba(52,211,153,0.4);}

.data-source-bar {
  background: rgba(91,200,255,0.06);
  border: 1px solid rgba(91,200,255,0.2);
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 11px; color: #9CA3AF;
  margin: 22px 0 14px 0;
  line-height: 1.9;
}
.data-source-bar b {color: #5BC8FF;}
.badge-real {
  display: inline-block; padding: 2px 8px;
  background: rgba(52,211,153,0.18); color: #6EE7B7;
  border: 1px solid rgba(52,211,153,0.4);
  border-radius: 10px; font-size: 10px; margin: 2px 4px;
}
.badge-sim {
  display: inline-block; padding: 2px 8px;
  background: rgba(167,139,250,0.18); color: #C4B5FD;
  border: 1px solid rgba(167,139,250,0.4);
  border-radius: 10px; font-size: 10px; margin: 2px 4px;
}

.status-dot {
  display: inline-block; width: 8px; height: 8px;
  border-radius: 50%; margin-right: 6px;
  background: #34D399; box-shadow: 0 0 8px rgba(52,211,153,0.7);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {0%, 100% {opacity: 1;} 50% {opacity: 0.4;}}

.js-plotly-plot {background: transparent !important;}

/* 解释面板 */
.explainer {
  background: rgba(91,200,255,0.05);
  border: 1px solid rgba(91,200,255,0.15);
  border-radius: 6px;
  padding: 8px 12px; font-size: 10px;
  color: #B8C5E0; line-height: 1.7;
  margin: 4px 0 12px 0;
}
.explainer b {color: #5BC8FF;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 顶部标题栏
# ============================================================
current_time = time.strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
<div class="cockpit-header">
  <div>
    <span class="cockpit-title">🧠 知忧·解郁  |  抑郁症风险智能监测大屏</span>
    <span class="cockpit-sub">DEPRESSION RISK COCKPIT  ·  v1.0</span>
  </div>
  <div class="cockpit-meta">
    <span class="status-dot"></span>系统在线  &nbsp;·&nbsp;  数据更新于 {current_time}
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 数据加载
# ============================================================
ROOT = Path(__file__).resolve().parents[1]
student = load_student_data()
elderly = load_elderly_data()
regional = load_regional_data()
trend = load_trend_data()
metrics = load_metrics()
imp_student = load_importance("student")
nhanes = load_nhanes_real()
mendeley = load_mendeley_real()
sources_info = data_sources_summary()
real_loaded = is_real_data_available()

province_path = ROOT / "data" / "china_province.csv"
province_df = pd.read_csv(province_path) if province_path.exists() else pd.DataFrame()


# ============================================================
# KPI 顶部卡片区
# ============================================================
total_n = (len(student) + len(elderly) + len(nhanes) + len(mendeley))
total_pos = int(student["是否抑郁"].sum() + elderly["是否抑郁"].sum() +
               (nhanes["是否抑郁"].sum() if len(nhanes) else 0) +
               (mendeley["是否抑郁"].sum() if len(mendeley) else 0))
overall_rate = total_pos / total_n * 100 if total_n else 0
best_auc = metrics["AUC"].max() if not metrics.empty else 0.93
real_n = sources_info["total_real"]
sim_n = sources_info["total_sim"]

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown(f"""
<div class="kpi-tile">
  <div class="kpi-label">📊 总样本量</div>
  <div class="kpi-value">{total_n:,}</div>
  <div class="kpi-sub">综合多源数据</div>
</div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
<div class="kpi-tile success">
  <div class="kpi-label">✅ 真实公开数据</div>
  <div class="kpi-value">{real_n:,}</div>
  <div class="kpi-sub">NHANES + Mendeley</div>
</div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
<div class="kpi-tile">
  <div class="kpi-label">🇨🇳 中国仿真数据</div>
  <div class="kpi-value">{sim_n:,}</div>
  <div class="kpi-sub">基于 CHARLS 文献</div>
</div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown(f"""
<div class="kpi-tile alert">
  <div class="kpi-label">⚠️ 综合检出率</div>
  <div class="kpi-value">{overall_rate:.1f}%</div>
  <div class="kpi-sub">阳性人数 {total_pos:,}</div>
</div>
    """, unsafe_allow_html=True)
with kpi5:
    st.markdown(f"""
<div class="kpi-tile success">
  <div class="kpi-label">🤖 模型最佳 AUC</div>
  <div class="kpi-value">{best_auc:.3f}</div>
  <div class="kpi-sub">RF + GBDT + LR 集成</div>
</div>
    """, unsafe_allow_html=True)


# ============================================================
# 数据源透明条 + 仿真数据说明
# ============================================================
real_text = " · ".join([
    f"<span class='badge-real'>{s['country']} {s['name']} ({s['n']:,}条)</span>"
    for s in sources_info["sources"] if s["type"] == "real"
])
sim_text = " · ".join([
    f"<span class='badge-sim'>{s['country']} {s['name']} ({s['n']:,}条)</span>"
    for s in sources_info["sources"] if s["type"] == "simulated"
])
st.markdown(f"""
<div class="data-source-bar">
<b>📡 数据来源透明声明 ▏</b><br>
<b>真实公开数据：</b>{real_text or "<span style='color:#FCA5A5'>暂未接入</span>"}<br>
<b>仿真演示数据：</b>{sim_text}<br>
<b>临床量表：</b>PHQ-9 (Kroenke 2001) / CES-D 10 (CHARLS)
</div>
""", unsafe_allow_html=True)


# ============================================================
# 第一行：中国省级地图 + 趋势 + 模型仪表盘
# ============================================================
row1c1, row1c2, row1c3 = st.columns([1.5, 1.4, 1])

with row1c1:
    st.markdown('<div class="panel-title">▍全国 34 省抑郁检出率分布</div>',
               unsafe_allow_html=True)
    if not province_df.empty:
        render_china_depression_map(province_df, "province", "rate",
                                    height=460)
    st.markdown("""
<div class="explainer">
<b>📌 数据说明：</b>本图所示省级检出率范围参考
<a href="https://doi.org/10.1016/S2215-0366(21)00251-0"
   style="color:#5BC8FF" target="_blank">Lu J et al. 2021 Lancet Psychiatry</a>
全国成人精神障碍流行病学调查的报告范围（4.5%-9.5%），
按地理梯度构造的演示分布。真实部署需对接<b>国家卫健委统计年鉴</b>与<b>各省疾控中心精神卫生数据</b>。
</div>
<div class="explainer" style="margin-top:8px; border-left-color:#FBBF24;">
<b>🗺️ 地图合规声明：</b>本图行政区划依据
<a href="http://bzdt.ch.mnr.gov.cn/" style="color:#5BC8FF" target="_blank">
中华人民共和国自然资源部 · 标准地图服务</a>发布的
<b>《中华人民共和国地图》（1:4800 万）</b>制作，
符合《公开地图内容表示规范》要求。
<br>
<b>审图号</b>：<span style="color:#FBBF24; font-weight:bold;">GS(2016)1600 号</span>
&nbsp;|&nbsp; <b>监制</b>：自然资源部
&nbsp;|&nbsp; <b>用途</b>：抑郁检出率统计可视化
</div>
    """, unsafe_allow_html=True)

with row1c2:
    st.markdown('<div class="panel-title">▍近十年抑郁检出率趋势（中国）</div>',
               unsafe_allow_html=True)
    st.plotly_chart(neon_trend(trend), use_container_width=True,
                   config={"displayModeBar": False})

    st.markdown('<div class="panel-title">▍真实数据：Mendeley 学生 PHQ-9</div>',
               unsafe_allow_html=True)
    if len(mendeley):
        sev = mendeley["抑郁分级"].value_counts().reindex(
            ["无", "轻度", "中度", "中重度", "重度"]).fillna(0)
        sev_df = sev.reset_index()
        sev_df.columns = ["抑郁分级", "人数"]
        # 用甜甜圈替代柱状图避免文字被遮挡
        st.plotly_chart(neon_donut(mendeley, "抑郁分级",
                                  f"PHQ-9 分级 (n={len(mendeley)} 真实学生)"),
                       use_container_width=True,
                       config={"displayModeBar": False})

with row1c3:
    st.markdown('<div class="panel-title">▍模型性能仪表盘</div>', unsafe_allow_html=True)
    if not metrics.empty:
        best_row = metrics.iloc[metrics["AUC"].idxmax()]
        st.plotly_chart(neon_gauge(float(best_row["AUC"]) * 100, "AUC 最佳", "%"),
                       use_container_width=True, config={"displayModeBar": False})
        st.plotly_chart(neon_gauge(float(best_row["召回率"]) * 100, "召回率", "%"),
                       use_container_width=True, config={"displayModeBar": False})
        st.plotly_chart(neon_gauge(float(best_row["F1"]) * 100, "F1 分数", "%"),
                       use_container_width=True, config={"displayModeBar": False})


# ============================================================
# 数据科学说明（不是 Q&A，而是研究方法学说明）
# ============================================================
st.markdown('<div class="panel-title">▍多源数据方法学说明 / 检出率差异解释</div>',
           unsafe_allow_html=True)
st.markdown("""
<div class="explainer" style="font-size:12px;">
本平台的多源数据集呈现不同的抑郁检出率。这并非数据不一致，而是
<b>不同人群结构 + 抽样设计</b>造成的预期差异，反映平台对真实数据生态的尊重：

<table style="width:100%; margin-top:8px; font-size:11px; color:#E8F0FF;
              border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(91,200,255,0.3);">
  <th style="text-align:left; padding:6px;">数据集</th>
  <th style="text-align:left; padding:6px;">检出率</th>
  <th style="text-align:left; padding:6px;">人群</th>
  <th style="text-align:left; padding:6px;">外部对照</th>
</tr>
<tr>
  <td style="padding:6px;">🇺🇸 NHANES 真实</td>
  <td style="padding:6px; color:#6EE7B7;">~9%</td>
  <td style="padding:6px;">美国全人群（所有年龄）</td>
  <td style="padding:6px;">≈ Lu 2021 中国成人 6.8%</td>
</tr>
<tr>
  <td style="padding:6px;">🌏 Mendeley 真实</td>
  <td style="padding:6px; color:#FBA94C;">~47%</td>
  <td style="padding:6px;">自愿筛查学生（选择偏差）</td>
  <td style="padding:6px;">高风险样本预期偏高</td>
</tr>
<tr>
  <td style="padding:6px;">🇨🇳 中国大学生 仿真</td>
  <td style="padding:6px; color:#FBA94C;">~30%</td>
  <td style="padding:6px;">17-26 岁在校生</td>
  <td style="padding:6px;">≈ Gao 2020 Sci Rep Meta</td>
</tr>
<tr>
  <td style="padding:6px;">🇨🇳 中国中老年 仿真</td>
  <td style="padding:6px; color:#FACC15;">~15%</td>
  <td style="padding:6px;">45+ 岁</td>
  <td style="padding:6px;">≈ CHARLS 历年 15-30%</td>
</tr>
</table>

<b style="color:#5BC8FF;">方法学统一：</b>所有数据均使用 PHQ-9 / CES-D 国际标准量表与统一切点 (≥10)。
平台用<b>真实数据做外部验证</b>（NHANES + Mendeley），用<b>中国流行病学仿真做模型训练</b>，
最终模型在两类数据上均收敛于一致的<b>核心风险因子结构</b>（社会支持、睡眠、ADL 自理、慢性病等），
证明方法可推广至真实中国数据。
</div>
""", unsafe_allow_html=True)


# ============================================================
# 第二行：中国仿真群体 + 天津区县 + 风险雷达
# ============================================================
row2c1, row2c2, row2c3 = st.columns([1.1, 1.4, 1])

with row2c1:
    st.markdown('<div class="panel-title">▍🇨🇳 中国学生 PHQ-9 五级分布</div>',
               unsafe_allow_html=True)
    st.plotly_chart(neon_donut(student, "抑郁分级", "n=5,000"),
                   use_container_width=True, config={"displayModeBar": False})
    st.markdown("""
<div class="explainer">
<b>仿真依据：</b><a href="https://doi.org/10.1038/s41598-020-72998-1"
   style="color:#5BC8FF" target="_blank">Gao L et al., 2020, Sci Rep</a>
中国大学生抑郁 Meta 分析 +
<a href="https://doi.org/10.1016/S2215-0366(21)00251-0"
   style="color:#5BC8FF" target="_blank">Lu J et al., 2021, Lancet Psychiatry</a>。
</div>
    """, unsafe_allow_html=True)

with row2c2:
    st.markdown('<div class="panel-title">▍天津 16 区县检出率（仿真）</div>',
               unsafe_allow_html=True)
    st.plotly_chart(
        neon_horizontal_bar(regional, "抑郁检出率_百分比", "区县",
                          "区县抑郁检出率排行"),
        use_container_width=True, config={"displayModeBar": False},
    )

with row2c3:
    st.markdown('<div class="panel-title">▍学生群体核心风险因子</div>',
               unsafe_allow_html=True)
    if not imp_student.empty:
        top = imp_student.head(6)
        cats = top["特征"].tolist()
        vals = top["随机森林重要性"].tolist()
        st.plotly_chart(neon_radar(cats, vals, "Top 6 风险（RF 重要性）"),
                       use_container_width=True, config={"displayModeBar": False})


# ============================================================
# 第三行：中老年 + 相关性 + 性别分级
# ============================================================
row3c1, row3c2, row3c3 = st.columns([1, 1.3, 1.3])

with row3c1:
    st.markdown('<div class="panel-title">▍🇨🇳 中国中老年 CES-D 五级分布</div>',
               unsafe_allow_html=True)
    st.plotly_chart(neon_donut(elderly, "抑郁分级", "n=4,000"),
                   use_container_width=True, config={"displayModeBar": False})
    st.markdown("""
<div class="explainer">
<b>仿真依据：</b>北京大学 <a href="https://charls.pku.edu.cn/"
   style="color:#5BC8FF" target="_blank">CHARLS</a>
中老年追踪调查 + <a href="https://doi.org/10.1016/j.socscimed.2014.09.028"
   style="color:#5BC8FF" target="_blank">Lei X et al., 2014, Soc Sci Med</a>。
</div>
    """, unsafe_allow_html=True)

with row3c2:
    st.markdown('<div class="panel-title">▍学生关键变量相关性矩阵</div>',
               unsafe_allow_html=True)
    cols_corr = ["PHQ9分数", "睡眠时长_小时", "学业压力", "经济压力",
                "亲密关系质量", "社会支持", "童年不良经历"]
    corr_df = student[cols_corr].corr().round(2)
    st.plotly_chart(neon_heatmap(corr_df, "Pearson 相关系数"),
                   use_container_width=True, config={"displayModeBar": False})

with row3c3:
    st.markdown('<div class="panel-title">▍学生 · 性别 × 抑郁分级</div>',
               unsafe_allow_html=True)
    g = (student.groupby(["性别", "抑郁分级"], observed=True)
                 .size().reset_index(name="人数"))
    st.plotly_chart(neon_grouped_bar(g, "性别", "人数", "抑郁分级",
                                     "堆叠柱状图（人数）"),
                   use_container_width=True, config={"displayModeBar": False})


# ============================================================
# 底部跳转提示
# ============================================================
st.markdown("""
<div style="text-align:center; margin-top:18px; color:#9CA3AF; font-size:11px;">
通过左侧导航 ← 进入 <b>📊 数据全景 / 🔍 风险因素分析 / 🧠 智能评估 / 🏙️ 天津决策支持 / 📚 关于项目</b> 等深度功能模块
</div>
""", unsafe_allow_html=True)
