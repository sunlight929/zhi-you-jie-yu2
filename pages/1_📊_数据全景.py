"""数据全景大屏：人群抑郁分布、人口学特征、生活方式画像（深色统一风格）。"""

import streamlit as st
import pandas as pd

from utils.data_loader import (
    load_student_data, load_elderly_data,
    load_nhanes_real, load_mendeley_real,
)
from utils.dark_charts import (
    neon_donut, neon_grouped_bar, neon_bar, neon_horizontal_bar,
)
from utils.test_mode import redirect_if_test_mode_non_assessment
import plotly.express as px

st.set_page_config(page_title="数据全景 | 知忧·解郁", page_icon="📊", layout="wide")

# 测试模式：自动跳转评估页（完整版下零影响）
redirect_if_test_mode_non_assessment()

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1500px;}
.section-title {
  font-size: 14px; color: #5BC8FF; letter-spacing: 1.5px;
  border-left: 3px solid #5BC8FF;
  padding-left: 10px; margin: 18px 0 10px 0;
  text-transform: uppercase;
}
.data-tag {
  display: inline-block; padding: 3px 10px; border-radius: 12px;
  font-size: 10px; margin-right: 6px;
}
.tag-real {background: rgba(52,211,153,0.18); color: #6EE7B7;
           border: 1px solid rgba(52,211,153,0.4);}
.tag-sim {background: rgba(167,139,250,0.18); color: #C4B5FD;
          border: 1px solid rgba(167,139,250,0.4);}
.kpi {
  background: linear-gradient(135deg, rgba(91,127,255,0.12), rgba(167,139,250,0.06));
  border: 1px solid rgba(91,200,255,0.25);
  border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
}
.kpi-l {font-size: 11px; color: #9CA3AF; letter-spacing: 1px;}
.kpi-v {font-size: 24px; font-weight: 800; color: #E8F0FF; margin-top: 4px;}
.kpi-s {font-size: 10px; color: #5BC8FF; margin-top: 2px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 数据全景")
st.caption("从多个数据源刻画大学生与中老年群体的抑郁分布画像")

tab_real, tab_s, tab_e, tab_compare = st.tabs([
    "🌟 真实公开数据", "🇨🇳 中国学生（仿真）",
    "🇨🇳 中国中老年（仿真）", "🆚 群体对比",
])

# ============================================================
# Tab 1：真实公开数据
# ============================================================
with tab_real:
    st.markdown('<span class="data-tag tag-real">真实公开数据</span> '
               '由 NHANES（美国 CDC）与 Mendeley Data 学术开放数据组成',
               unsafe_allow_html=True)

    nhanes = load_nhanes_real()
    mendeley = load_mendeley_real()

    if nhanes.empty and mendeley.empty:
        st.warning("尚未下载真实数据。请运行：\n"
                  "```bash\npython data/download_real_data.py --source all --convert\n```")
    else:
        # NHANES 部分
        if not nhanes.empty:
            st.markdown('<div class="section-title">🇺🇸 NHANES 2017-2018（美国 CDC 公开）</div>',
                       unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">📦 样本量</div>
<div class="kpi-v">{len(nhanes):,}</div>
<div class="kpi-s">真实公开数据</div>
</div>
                """, unsafe_allow_html=True)
            with c2:
                rate = nhanes["是否抑郁"].mean() * 100
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">⚠️ 抑郁检出率</div>
<div class="kpi-v">{rate:.1f}%</div>
<div class="kpi-s">PHQ-9 ≥ 10</div>
</div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">📈 平均 PHQ-9</div>
<div class="kpi-v">{nhanes['PHQ9分数'].mean():.1f}</div>
<div class="kpi-s">满分 27</div>
</div>
                """, unsafe_allow_html=True)
            with c4:
                avg_age = nhanes["年龄"].mean() if "年龄" in nhanes.columns else 0
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">👥 平均年龄</div>
<div class="kpi-v">{avg_age:.0f} 岁</div>
<div class="kpi-s">全人群覆盖</div>
</div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(neon_donut(nhanes, "抑郁分级",
                                          "PHQ-9 五级分布"),
                               use_container_width=True,
                               config={"displayModeBar": False})
            with col2:
                if "性别" in nhanes.columns:
                    g = (nhanes.groupby(["性别", "抑郁分级"], observed=True)
                                .size().reset_index(name="人数"))
                    st.plotly_chart(neon_grouped_bar(g, "性别", "人数",
                                                    "抑郁分级",
                                                    "性别 × 抑郁分级"),
                                   use_container_width=True,
                                   config={"displayModeBar": False})

        st.markdown("---")

        # Mendeley 部分
        if not mendeley.empty:
            st.markdown('<div class="section-title">🌏 Mendeley 学生 PHQ-9 公开数据集（kkzjk253cy）</div>',
                       unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">📦 样本量</div>
<div class="kpi-v">{len(mendeley):,}</div>
<div class="kpi-s">真实学生数据</div>
</div>
                """, unsafe_allow_html=True)
            with c2:
                rate = mendeley["是否抑郁"].mean() * 100
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">⚠️ 抑郁检出率</div>
<div class="kpi-v">{rate:.1f}%</div>
<div class="kpi-s">PHQ-9 ≥ 10</div>
</div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
<div class="kpi">
<div class="kpi-l">📈 平均 PHQ-9</div>
<div class="kpi-v">{mendeley['PHQ9分数'].mean():.1f}</div>
<div class="kpi-s">满分 27</div>
</div>
                """, unsafe_allow_html=True)
            with c4:
                if "学业压力等级" in mendeley.columns:
                    high_stress = (mendeley["学业压力等级"] >= 3).mean() * 100
                    st.markdown(f"""
<div class="kpi">
<div class="kpi-l">📚 高学业压力比例</div>
<div class="kpi-v">{high_stress:.0f}%</div>
<div class="kpi-s">压力 ≥ Bad</div>
</div>
                    """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(neon_donut(mendeley, "抑郁分级",
                                          "PHQ-9 五级分布（学生）"),
                               use_container_width=True,
                               config={"displayModeBar": False})
            with col2:
                # 按学业压力分组的抑郁率
                if "学业压力等级" in mendeley.columns:
                    stress_rate = (mendeley.groupby("学业压力等级")["是否抑郁"]
                                          .mean() * 100).round(1).reset_index()
                    stress_label_map = {0: "Best", 1: "Good", 2: "Average",
                                       3: "Bad", 4: "Worst"}
                    stress_rate["学业压力"] = stress_rate["学业压力等级"].map(stress_label_map)
                    stress_rate.columns = ["压力等级", "检出率", "学业压力"]
                    st.plotly_chart(neon_bar(stress_rate, "学业压力", "检出率",
                                            "学业压力 × 抑郁检出率(%)"),
                                   use_container_width=True,
                                   config={"displayModeBar": False})


# ============================================================
# Tab 2：中国学生仿真数据
# ============================================================
with tab_s:
    st.markdown('<span class="data-tag tag-sim">仿真数据</span> '
               '基于 Gao L et al. (2020) Sci Rep 中国大学生抑郁 Meta 分析参数构造',
               unsafe_allow_html=True)

    df = load_student_data()
    n = len(df)
    pos = int(df["是否抑郁"].sum())
    rate = pos / n * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">📦 样本量</div>
<div class="kpi-v">{n:,}</div><div class="kpi-s">中国大学生</div></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">⚠️ 抑郁检出率</div>
<div class="kpi-v">{rate:.1f}%</div><div class="kpi-s">PHQ-9 ≥ 10</div></div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">📈 平均 PHQ-9</div>
<div class="kpi-v">{df['PHQ9分数'].mean():.1f}</div><div class="kpi-s">满分 27</div></div>
        """, unsafe_allow_html=True)
    with c4:
        severe = (df["抑郁分级"].isin(["中重度", "重度"])).mean() * 100
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">🔴 中重度及以上</div>
<div class="kpi-v">{severe:.1f}%</div><div class="kpi-s">需立即干预</div></div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(neon_donut(df, "抑郁分级", "PHQ-9 五级分布"),
                       use_container_width=True,
                       config={"displayModeBar": False})
    with col2:
        g = (df.groupby(["性别", "抑郁分级"], observed=True)
              .size().reset_index(name="人数"))
        st.plotly_chart(neon_grouped_bar(g, "性别", "人数", "抑郁分级",
                                         "性别 × 抑郁分级"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    col3, col4 = st.columns(2)
    with col3:
        gr = (df.groupby("年级")["是否抑郁"].mean() * 100).round(1).reset_index()
        gr.columns = ["年级", "检出率"]
        st.plotly_chart(neon_bar(gr, "年级", "检出率", "不同年级抑郁检出率(%)"),
                       use_container_width=True,
                       config={"displayModeBar": False})
    with col4:
        mj = (df.groupby("专业类型")["是否抑郁"].mean() * 100).round(1).reset_index()
        mj.columns = ["专业类型", "检出率"]
        st.plotly_chart(neon_bar(mj, "专业类型", "检出率", "不同专业抑郁检出率(%)"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    with st.expander("📋 查看原始数据样本（前 100 行）"):
        st.dataframe(df.head(100), use_container_width=True, height=300)


# ============================================================
# Tab 3：中国中老年仿真数据
# ============================================================
with tab_e:
    st.markdown('<span class="data-tag tag-sim">仿真数据</span> '
               '基于 CHARLS（北京大学）与 Lei et al. (2014) 流行病学分布参数构造',
               unsafe_allow_html=True)

    df = load_elderly_data()
    n = len(df)
    pos = int(df["是否抑郁"].sum())
    rate = pos / n * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">📦 样本量</div>
<div class="kpi-v">{n:,}</div><div class="kpi-s">中老年(45+)</div></div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">⚠️ 抑郁检出率</div>
<div class="kpi-v">{rate:.1f}%</div><div class="kpi-s">CES-D ≥ 10</div></div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">📈 平均 CES-D</div>
<div class="kpi-v">{df['CESD分数'].mean():.1f}</div><div class="kpi-s">满分 30</div></div>
        """, unsafe_allow_html=True)
    with c4:
        alone = df["是否独居"].mean() * 100
        st.markdown(f"""
<div class="kpi"><div class="kpi-l">🏠 独居比例</div>
<div class="kpi-v">{alone:.1f}%</div><div class="kpi-s">高危因子</div></div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(neon_donut(df, "抑郁分级", "CES-D 五级分布"),
                       use_container_width=True,
                       config={"displayModeBar": False})
    with col2:
        g = (df.groupby(["性别", "抑郁分级"], observed=True)
              .size().reset_index(name="人数"))
        st.plotly_chart(neon_grouped_bar(g, "性别", "人数", "抑郁分级",
                                         "性别 × 抑郁分级"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    col3, col4 = st.columns(2)
    with col3:
        ed = (df.groupby("教育程度")["是否抑郁"].mean() * 100).round(1).reset_index()
        ed.columns = ["教育程度", "检出率"]
        st.plotly_chart(neon_bar(ed, "教育程度", "检出率",
                                "教育程度 × 抑郁检出率(%)"),
                       use_container_width=True,
                       config={"displayModeBar": False})
    with col4:
        rg = (df.groupby("居住地区")["是否抑郁"].mean() * 100).round(1).reset_index()
        rg.columns = ["居住地区", "检出率"]
        st.plotly_chart(neon_bar(rg, "居住地区", "检出率",
                                "居住地区 × 抑郁检出率(%)"),
                       use_container_width=True,
                       config={"displayModeBar": False})

    with st.expander("📋 查看原始数据样本（前 100 行）"):
        st.dataframe(df.head(100), use_container_width=True, height=300)


# ============================================================
# Tab 4：群体对比
# ============================================================
with tab_compare:
    st.markdown("基于多源数据的核心指标对比", unsafe_allow_html=True)
    s = load_student_data()
    e = load_elderly_data()
    n = load_nhanes_real()
    m = load_mendeley_real()

    rows = [
        {"群体": "🇺🇸 NHANES 美国",
         "类型": "真实", "样本量": len(n) if not n.empty else 0,
         "检出率(%)": round(n["是否抑郁"].mean() * 100, 1) if not n.empty else 0,
         "平均量表分": round(n["PHQ9分数"].mean(), 1) if not n.empty else 0},
        {"群体": "🌏 Mendeley 学生",
         "类型": "真实", "样本量": len(m) if not m.empty else 0,
         "检出率(%)": round(m["是否抑郁"].mean() * 100, 1) if not m.empty else 0,
         "平均量表分": round(m["PHQ9分数"].mean(), 1) if not m.empty else 0},
        {"群体": "🇨🇳 中国大学生",
         "类型": "仿真", "样本量": len(s),
         "检出率(%)": round(s["是否抑郁"].mean() * 100, 1),
         "平均量表分": round(s["PHQ9分数"].mean(), 1)},
        {"群体": "🇨🇳 中国中老年",
         "类型": "仿真", "样本量": len(e),
         "检出率(%)": round(e["是否抑郁"].mean() * 100, 1),
         "平均量表分": round(e["CESD分数"].mean(), 1)},
    ]
    cdf = pd.DataFrame(rows)
    cdf = cdf[cdf["样本量"] > 0]
    st.dataframe(cdf, use_container_width=True, hide_index=True)

    fig = px.bar(cdf, x="群体", y="检出率(%)", text="检出率(%)",
                color="类型",
                color_discrete_map={"真实": "#34D399", "仿真": "#A78BFA"},
                title="多源数据抑郁检出率对比")
    fig.update_traces(texttemplate="%{text:.1f}%",
                     textposition="outside",
                     textfont=dict(size=12, color="#E8F0FF"),
                     cliponaxis=False)
    # 给顶部标签留 25% 空间
    ymax = cdf["检出率(%)"].max()
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E8F0FF",
                 family="PingFang SC, Microsoft YaHei"),
        yaxis=dict(title="检出率(%)", range=[0, ymax * 1.25],
                  gridcolor="rgba(91,127,255,0.18)"),
        xaxis=dict(title="", showgrid=False, tickfont=dict(size=12)),
        height=460,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.12,
            xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            title=dict(text="数据类型 ▏",
                      font=dict(color="#5BC8FF", size=11)),
            font=dict(size=11),
        ),
        margin=dict(l=50, r=20, t=60, b=80),
    )
    st.plotly_chart(fig, use_container_width=True,
                   config={"displayModeBar": False})

    st.markdown("""
### 💡 关键发现

- **真实数据 vs 仿真**：NHANES 美国数据检出率较低（~9%），与 Lu et al. 2021 报告的中国成人 6.8% 终生患病率方向一致；
  Mendeley 学生数据检出率较高（~47%），属于自愿筛查样本（**自选择偏差**），与中国大学生群体研究的 24.7% 处于同一数量级
- **中国学生 vs 中老年**：学生检出率高于中老年，但中老年**重度比例**更突出，临床干预紧迫性强
- **方法学一致性**：四类数据均采用 PHQ-9 / CES-D 国际标准量表，可跨数据集横向比较
- **数据生态**：本平台同时呈现"真实学术公开数据"+ "中国本土流行病学仿真数据"，
  既有外部验证，又贴近中国国情，是大赛"数据驱动决策"主题的合规演示
    """)
