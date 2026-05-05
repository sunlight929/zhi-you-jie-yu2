"""可视化封装。基于 Plotly，颜色统一，避免标题/图例重叠。"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PRIMARY = "#5B7FFF"
ACCENT = "#F25F5C"
NEUTRAL = "#2E2E3A"
SOFT_BG = "rgba(91, 127, 255, 0.08)"

LEVEL_ORDER = ["无", "轻度", "中度", "中重度", "重度"]
LEVEL_COLORS = {
    "无": "#A6E3A1",
    "轻度": "#FFE066",
    "中度": "#FF9F45",
    "中重度": "#F25F5C",
    "重度": "#9D2933",
}


def _apply_theme(fig: go.Figure, title_pad_top: int = 80) -> go.Figure:
    """统一主题：标题位于顶部，图例位于底部，避免重叠。"""
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="PingFang SC, Microsoft YaHei, Arial", color=NEUTRAL, size=12),
        margin=dict(l=50, r=30, t=title_pad_top, b=80),
        title=dict(x=0.0, xanchor="left", y=0.97, yanchor="top",
                  font=dict(size=15, color=NEUTRAL)),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEE")
    fig.update_yaxes(showgrid=True, gridcolor="#EEE")
    return fig


def kpi_card_value(df: pd.DataFrame, col: str = "是否抑郁") -> dict:
    n = len(df)
    pos = int(df[col].sum())
    rate = pos / n * 100 if n else 0
    return {"样本量": n, "抑郁人数": pos, "检出率": f"{rate:.1f}%"}


def severity_donut(df: pd.DataFrame, title: str) -> go.Figure:
    counts = df["抑郁分级"].value_counts().reindex(LEVEL_ORDER).fillna(0)
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.55,
        marker=dict(colors=[LEVEL_COLORS[k] for k in counts.index]),
        textinfo="label+percent",
        textposition="outside",
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(text=title, x=0.0, xanchor="left", y=0.97,
                  font=dict(size=15, color=NEUTRAL)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="PingFang SC, Microsoft YaHei, Arial", color=NEUTRAL, size=12),
        margin=dict(l=20, r=20, t=80, b=20),
        height=380,
    )
    return fig


def gender_grouped_bar(df: pd.DataFrame) -> go.Figure:
    g = df.groupby(["性别", "抑郁分级"], observed=True).size().reset_index(name="人数")
    fig = px.bar(
        g, x="性别", y="人数", color="抑郁分级",
        category_orders={"抑郁分级": LEVEL_ORDER},
        color_discrete_map=LEVEL_COLORS,
        title="不同性别的抑郁分级分布",
        barmode="stack",
    )
    fig.update_layout(height=420)
    return _apply_theme(fig, title_pad_top=70)


def grade_rate_bar(df: pd.DataFrame, group_col: str, title: str) -> go.Figure:
    g = df.groupby(group_col)["是否抑郁"].mean().reset_index()
    g["抑郁检出率_百分比"] = (g["是否抑郁"] * 100).round(1)
    fig = px.bar(
        g, x=group_col, y="抑郁检出率_百分比", text="抑郁检出率_百分比",
        title=title, color="抑郁检出率_百分比",
        color_continuous_scale=["#A6E3A1", "#FFE066", "#FF9F45", "#F25F5C"],
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, yaxis_title="检出率(%)", height=400)
    return _apply_theme(fig, title_pad_top=70)


def correlation_heatmap(df: pd.DataFrame, cols: list, title: str) -> go.Figure:
    corr = df[cols].corr().round(2)
    fig = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title=title,
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="相关系数", thickness=12, len=0.7),
        height=520,
    )
    return _apply_theme(fig, title_pad_top=70)


def feature_importance_bar(importance_df: pd.DataFrame,
                           top_n: int = 12,
                           col: str = "随机森林重要性",
                           title: str = "Top 特征重要性") -> go.Figure:
    df = importance_df.head(top_n).copy()
    df = df.sort_values(col)
    fig = px.bar(
        df, x=col, y="特征", orientation="h",
        color=col, color_continuous_scale=["#5B7FFF", "#F25F5C"],
        title=title, text=col,
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="auto",
                     textfont=dict(color="#E8F0FF", size=11),
                     cliponaxis=False)
    xmax = df[col].max()
    fig.update_xaxes(range=[0, xmax * 1.18])
    fig.update_layout(coloraxis_showscale=False, height=480,
                     margin=dict(l=110, r=70, t=60, b=40))
    return _apply_theme(fig, title_pad_top=70)


def trend_line(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["年份"], y=df["大学生抑郁检出率_百分比"],
        mode="lines+markers", name="大学生",
        line=dict(color=PRIMARY, width=3), marker=dict(size=10),
    ))
    fig.add_trace(go.Scatter(
        x=df["年份"], y=df["中老年抑郁检出率_百分比"],
        mode="lines+markers", name="中老年(60+)",
        line=dict(color=ACCENT, width=3, dash="dash"), marker=dict(size=10),
    ))
    fig.update_layout(
        title="近十年中国主要人群抑郁检出率趋势",
        xaxis_title="年份", yaxis_title="检出率(%)",
        hovermode="x unified",
        height=380,
    )
    return _apply_theme(fig, title_pad_top=70)


def regional_bar(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("抑郁检出率_百分比", ascending=True)
    fig = px.bar(
        df, x="抑郁检出率_百分比", y="区县", orientation="h",
        color="抑郁检出率_百分比",
        color_continuous_scale=["#A6E3A1", "#FFE066", "#FF9F45", "#F25F5C"],
        text="抑郁检出率_百分比",
        title="天津市各区抑郁检出率（仿真示例）",
        hover_data={"样本量": True, "60岁以上人口占比_百分比": True,
                    "每千人精神卫生资源数": True},
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=620,
                     xaxis_title="抑郁检出率(%)", yaxis_title="")
    return _apply_theme(fig, title_pad_top=70)


def regional_scatter(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df, x="每千人精神卫生资源数", y="抑郁检出率_百分比",
        size="60岁以上人口占比_百分比",
        color="抑郁检出率_百分比",
        color_continuous_scale=["#A6E3A1", "#F25F5C"],
        hover_name="区县",
        title="精神卫生资源 vs 抑郁检出率（点大小=老龄化程度）",
        labels={"每千人精神卫生资源数": "每千人精神卫生资源数",
                "抑郁检出率_百分比": "抑郁检出率(%)"},
    )
    fig.update_layout(coloraxis_showscale=False, height=480)
    return _apply_theme(fig, title_pad_top=70)


def risk_gauge(prob: float, label: str) -> go.Figure:
    """风险仪表盘 — 加粗的高亮蓝色指针（低风险也能看清）+ threshold 阈值标识。"""
    pct = prob * 100
    # 根据风险等级动态选择颜色
    if pct < 30:
        bar_color = "#34D399"   # 绿
    elif pct < 50:
        bar_color = "#FACC15"   # 黄
    elif pct < 70:
        bar_color = "#FB923C"   # 橙
    else:
        bar_color = "#F87171"   # 红

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 40, "color": "#E8F0FF"}},
        title={"text": f"<b style='color:#E8F0FF'>{label}</b>"
                       f"<br><span style='font-size:12px;color:#9CA3AF'>抑郁风险评估值</span>",
              "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                    "tickcolor": "#9CA3AF",
                    "tickfont": {"color": "#9CA3AF", "size": 10},
                    "tickvals": [0, 25, 50, 75, 100]},
            # 主指针：粗一些 + 颜色随风险等级变化（低风险也很显眼）
            "bar": {"color": bar_color, "thickness": 0.65,
                   "line": {"color": "white", "width": 2}},
            "bgcolor": "rgba(255,255,255,0.06)",
            "borderwidth": 1,
            "bordercolor": "rgba(91,200,255,0.3)",
            "steps": [
                {"range": [0, 30], "color": "rgba(52,211,153,0.18)"},
                {"range": [30, 50], "color": "rgba(250,204,21,0.18)"},
                {"range": [50, 70], "color": "rgba(251,146,60,0.22)"},
                {"range": [70, 100], "color": "rgba(248,113,113,0.25)"},
            ],
            # 用一根白色亮线作为指针，确保任何位置都明显可见
            "threshold": {
                "line": {"color": "#FFFFFF", "width": 3},
                "thickness": 0.85,
                "value": pct,
            },
        },
    ))
    fig.update_layout(height=340,
                     margin=dict(t=80, b=40, l=40, r=40),
                     paper_bgcolor="rgba(0,0,0,0)",
                     plot_bgcolor="rgba(0,0,0,0)",
                     font=dict(family="PingFang SC, Microsoft YaHei",
                              color="#E8F0FF"))
    return fig


def shap_bar(features: list, values: list,
             title: str = "本次评估的特征贡献") -> go.Figure:
    """
    特征贡献分解条形图（深色风格 + 大字号 + 清晰方向标签）。
    左侧（蓝）= 降低风险；右侧（红）= 升高风险。
    """
    df = pd.DataFrame({"特征": features, "贡献值": values})
    df = df.sort_values("贡献值", key=lambda x: x.abs(), ascending=True).tail(10)
    df["方向"] = df["贡献值"].apply(lambda v: "↑ 升高风险" if v > 0 else "↓ 降低风险")
    df["显示文本"] = df["贡献值"].apply(
        lambda v: f"+{v:.2f}" if v > 0 else f"{v:.2f}")
    fig = px.bar(
        df, x="贡献值", y="特征", color="方向", orientation="h",
        color_discrete_map={"↑ 升高风险": "#F87171", "↓ 降低风险": "#5BC8FF"},
        title=title, text="显示文本",
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=11, color="#E8F0FF"),
        marker=dict(line=dict(color="rgba(255,255,255,0.18)", width=1)),
        cliponaxis=False,   # 关键：标签不被坐标轴 0 线裁切
    )
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.4)", width=1.5))

    # 给左右两侧各留 30% 的额外空间，让 +0.xx / -0.xx 完整显示
    vmax = max(abs(v) for v in values) if values else 1
    fig.update_xaxes(range=[-vmax * 1.35, vmax * 1.35],
                    gridcolor="rgba(91,127,255,0.18)",
                    color="#E8F0FF", zerolinecolor="rgba(255,255,255,0.4)")
    fig.update_yaxes(gridcolor="rgba(91,127,255,0.18)",
                    color="#E8F0FF", tickfont=dict(size=12))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="PingFang SC, Microsoft YaHei, Arial",
                 color="#E8F0FF", size=12),
        height=480,
        xaxis_title="贡献值（→ 越右抬升风险，← 越左降低风险）",
        yaxis_title="",
        title=dict(text=title, font=dict(size=14, color="#E8F0FF"), x=0.0,
                  xanchor="left"),
        # 给底部图例足够空间，与 X 轴标题分开
        margin=dict(l=110, r=80, t=60, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.30,
            xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E8F0FF", size=11),
            title=dict(text="效应方向 ▏",
                      font=dict(color="#5BC8FF", size=11)),
        ),
        bargap=0.35,
    )
    return fig


def boxplot_by_level(df: pd.DataFrame, value: str, title: str) -> go.Figure:
    fig = px.box(
        df, x="抑郁分级", y=value, color="抑郁分级",
        category_orders={"抑郁分级": LEVEL_ORDER},
        color_discrete_map=LEVEL_COLORS,
        title=title,
    )
    fig.update_layout(showlegend=False, height=360)
    return _apply_theme(fig, title_pad_top=70)
