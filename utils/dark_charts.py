"""深色大屏专用 Plotly 图表（霓虹科技风）。"""

from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# 深色大屏配色
BG_DARK = "rgba(0,0,0,0)"
TEXT_LIGHT = "#E8F0FF"
GRID_DIM = "rgba(91,127,255,0.18)"
NEON_BLUE = "#5BC8FF"
NEON_PURPLE = "#A78BFA"
NEON_PINK = "#F472B6"
NEON_GREEN = "#34D399"
NEON_YELLOW = "#FACC15"
NEON_ORANGE = "#FB923C"
NEON_RED = "#F87171"


SEVERITY_NEON = {
    "无": "#34D399",
    "轻度": "#FACC15",
    "中度": "#FB923C",
    "中重度": "#F87171",
    "重度": "#A855F7",
}
SEVERITY_ORDER = ["无", "轻度", "中度", "中重度", "重度"]


def _dark_theme(fig: go.Figure, height: int = 280, title_size: int = 13) -> go.Figure:
    fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(family="PingFang SC, Microsoft YaHei, Arial",
                 color=TEXT_LIGHT, size=11),
        margin=dict(l=40, r=20, t=50, b=30),
        height=height,
        title=dict(x=0.0, xanchor="left", y=0.97, yanchor="top",
                  font=dict(size=title_size, color=TEXT_LIGHT)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID_DIM, color=TEXT_LIGHT,
                    linecolor=GRID_DIM, zerolinecolor=GRID_DIM)
    fig.update_yaxes(showgrid=True, gridcolor=GRID_DIM, color=TEXT_LIGHT,
                    linecolor=GRID_DIM, zerolinecolor=GRID_DIM)
    return fig


def neon_donut(df: pd.DataFrame, severity_col: str, title: str) -> go.Figure:
    counts = df[severity_col].value_counts().reindex(SEVERITY_ORDER).fillna(0)
    total_v = int(counts.sum())
    # 大于 5% 的标签放饼内部，小于 5% 的放外部带引线
    text_arr = []
    text_pos = []
    for v in counts.values:
        pct = v / total_v if total_v else 0
        text_arr.append(f"{pct*100:.1f}%")
        text_pos.append("inside" if pct >= 0.05 else "outside")
    fig = go.Figure(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.62,
        marker=dict(colors=[SEVERITY_NEON[k] for k in counts.index],
                   line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=text_arr,
        textinfo="text",
        textposition=text_pos,           # 大块在内、小块外引线
        insidetextorientation="horizontal",
        textfont=dict(size=11, family="PingFang SC"),
        # 内部用深色字（在彩色饼上显眼），外部由 plotly 自动用引线 + 浅色字
        outsidetextfont=dict(color=TEXT_LIGHT, size=10),
        insidetextfont=dict(color="#0A0B1E"),
        automargin=True,
        showlegend=True,
        sort=False,
        direction="clockwise",
        domain=dict(x=[0.05, 0.95], y=[0.25, 1.0]),
    ))
    fig.add_annotation(text=f"<b>{total_v}</b><br><span style='font-size:10px'>样本量</span>",
                      x=0.5, y=0.625, showarrow=False,
                      font=dict(size=18, color=TEXT_LIGHT))
    fig.update_layout(
        title=dict(text=title, x=0.0, xanchor="left",
                  font=dict(size=13, color=TEXT_LIGHT)),
        plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
        margin=dict(l=10, r=10, t=50, b=20),
        font=dict(family="PingFang SC, Microsoft YaHei",
                 color=TEXT_LIGHT, size=10),
        height=380,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.02,
            xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_LIGHT, size=11),
            itemsizing="constant",
        ),
    )
    return fig


def neon_radial(value: float, label: str, color: str = NEON_BLUE) -> go.Figure:
    """单值环形进度图（霓虹）。"""
    pct = max(0.0, min(1.0, value))
    fig = go.Figure(go.Pie(
        values=[pct, 1 - pct],
        hole=0.78,
        marker=dict(colors=[color, "rgba(255,255,255,0.06)"],
                   line=dict(color="rgba(0,0,0,0)", width=0)),
        sort=False,
        direction="clockwise",
        rotation=270,
        textinfo="none",
        showlegend=False,
    ))
    fig.add_annotation(
        text=f"<b style='font-size:24px'>{pct*100:.1f}%</b>"
             f"<br><span style='font-size:10px;color:#9CA3AF'>{label}</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT_LIGHT),
    )
    fig.update_layout(plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
                     margin=dict(l=8, r=8, t=8, b=8), height=160)
    return fig


def neon_trend(df: pd.DataFrame) -> go.Figure:
    """近十年抑郁检出率趋势（深色背景 + 平滑曲线，两条都用实线）。"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["年份"], y=df["大学生抑郁检出率_百分比"],
        mode="lines+markers", name="大学生",
        line=dict(color=NEON_BLUE, width=3, shape="spline", smoothing=1.0),
        marker=dict(size=9, color=NEON_BLUE,
                   line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(91,200,255,0.12)",
    ))
    fig.add_trace(go.Scatter(
        x=df["年份"], y=df["中老年抑郁检出率_百分比"],
        mode="lines+markers", name="中老年",
        # 改成实线（之前的虚线在动画下视觉上会一顿一顿）
        line=dict(color=NEON_PINK, width=3, shape="spline", smoothing=1.0),
        marker=dict(size=9, color=NEON_PINK,
                   symbol="diamond",
                   line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(244,114,182,0.10)",
    ))
    fig.update_layout(
        title=dict(text="近十年抑郁检出率趋势 / 大学生 vs 中老年",
                  x=0.0, xanchor="left", y=0.97, yanchor="top",
                  font=dict(size=13, color=TEXT_LIGHT)),
        hovermode="x unified", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom",
                   y=-0.42, xanchor="center", x=0.5,
                   bgcolor="rgba(0,0,0,0)",
                   font=dict(color=TEXT_LIGHT, size=11)),
        yaxis_title="检出率(%)", xaxis_title="",
    )
    fig = _dark_theme(fig, height=360, title_size=13)
    # 底部预留更多空间给 X 轴标签 + 图例
    fig.update_layout(margin=dict(l=50, r=20, t=55, b=110))
    return fig


def neon_bar(df: pd.DataFrame, x: str, y: str, title: str,
            color: str = NEON_BLUE) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df[x], y=df[y], marker=dict(
            color=df[y], colorscale=[[0, NEON_BLUE], [0.5, NEON_PURPLE], [1, NEON_PINK]],
            line=dict(color="rgba(255,255,255,0.1)", width=1),
        ),
        text=df[y].round(1), textposition="outside",
        textfont=dict(color=TEXT_LIGHT, size=10),
        cliponaxis=False,
    ))
    # 给顶部 label 预留 18% 空间
    ymax = df[y].max()
    fig.update_yaxes(range=[0, ymax * 1.18])
    fig.update_layout(title=title)
    fig = _dark_theme(fig, height=320)
    fig.update_layout(margin=dict(l=50, r=20, t=50, b=50))
    return fig


def neon_horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str,
                        is_percent: bool = True) -> go.Figure:
    df_sorted = df.sort_values(x, ascending=True)
    if is_percent:
        text_arr = df_sorted[x].round(1).astype(str) + "%"
    else:
        text_arr = df_sorted[x].round(3).astype(str)
    fig = go.Figure(go.Bar(
        x=df_sorted[x], y=df_sorted[y], orientation="h",
        marker=dict(
            color=df_sorted[x],
            colorscale=[[0, NEON_GREEN], [0.5, NEON_YELLOW],
                       [0.75, NEON_ORANGE], [1, NEON_RED]],
            line=dict(color="rgba(255,255,255,0.1)", width=1),
        ),
        text=text_arr, textposition="auto",
        textfont=dict(color=TEXT_LIGHT, size=10),
        cliponaxis=False,
    ))
    xmax = df_sorted[x].max()
    fig.update_xaxes(range=[0, xmax * 1.18])
    fig.update_layout(title=title)
    fig = _dark_theme(fig, height=440)
    fig.update_layout(margin=dict(l=110, r=60, t=42, b=40))
    return fig


def neon_gauge(value: float, label: str, suffix: str = "%") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=suffix, font=dict(size=22, color=TEXT_LIGHT)),
        title=dict(text=f"<span style='font-size:11px;color:#9CA3AF'>{label}</span>",
                  font=dict(size=11)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=TEXT_LIGHT,
                     tickfont=dict(color=TEXT_LIGHT, size=9),
                     tickvals=[0, 25, 50, 75, 100]),
            bar=dict(color=NEON_BLUE, thickness=0.25),
            bgcolor="rgba(255,255,255,0.04)",
            borderwidth=0,
            steps=[
                dict(range=[0, 30], color="rgba(52,211,153,0.18)"),
                dict(range=[30, 60], color="rgba(250,204,21,0.18)"),
                dict(range=[60, 80], color="rgba(251,146,60,0.20)"),
                dict(range=[80, 100], color="rgba(248,113,113,0.22)"),
            ],
        ),
    ))
    # 增加底部和左右 margin 防止刻度被裁
    fig.update_layout(plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
                     font=dict(color=TEXT_LIGHT),
                     margin=dict(l=30, r=30, t=40, b=30),
                     height=180)
    return fig


def neon_grouped_bar(df: pd.DataFrame, x: str, y: str, color: str,
                    title: str) -> go.Figure:
    """分组堆叠柱状图（按抑郁分级着色，含整齐图例）。"""
    fig = go.Figure()
    palette = SEVERITY_NEON
    # 倒序添加（从重度→无）以便图例从左到右是 无→轻→中→中重→重
    for level in SEVERITY_ORDER:
        sub = df[df[color] == level]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Bar(
            x=sub[x], y=sub[y], name=level,
            marker=dict(color=palette[level],
                       line=dict(color="rgba(255,255,255,0.15)", width=1)),
            hovertemplate=f"<b>{level}</b><br>%{{x}}: %{{y}} 人<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title,
                  x=0.0, xanchor="left",
                  font=dict(size=13, color=TEXT_LIGHT)),
        barmode="stack", showlegend=True,
        legend=dict(
            orientation="h", yanchor="top",
            y=-0.18, xanchor="center", x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_LIGHT, size=11),
            traceorder="normal",  # 按添加顺序
            itemsizing="constant",
            title=dict(text="抑郁分级 ▏",
                      font=dict(color="#5BC8FF", size=11)),
        ),
    )
    fig = _dark_theme(fig, height=380)
    fig.update_layout(margin=dict(l=50, r=20, t=50, b=90))
    return fig


def neon_heatmap(corr: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale=[[0, NEON_BLUE], [0.5, "#1E1B4B"], [1, NEON_PINK]],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(thickness=10, len=0.7,
                     tickfont=dict(color=TEXT_LIGHT, size=9)),
        text=corr.round(2).values, texttemplate="%{text}",
        textfont=dict(color=TEXT_LIGHT, size=9),
    ))
    fig.update_layout(title=title)
    fig = _dark_theme(fig, height=380)
    fig.update_xaxes(tickangle=-30, tickfont=dict(size=10))
    fig.update_yaxes(tickfont=dict(size=10))
    return fig


def china_province_choropleth(df: pd.DataFrame, location_col: str = "province",
                              value_col: str = "rate",
                              title: str = "全国抑郁检出率分布") -> go.Figure:
    """中国省级抑郁检出率分布图（深色风格 choropleth）。
    使用 Plotly 的 china geojson + scope='asia' 兜底。"""
    # 使用国家测绘地理信息局公开发布的中国省级 GeoJSON CDN
    geojson_url = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    try:
        import urllib.request
        import json as _json
        with urllib.request.urlopen(geojson_url, timeout=8) as r:
            geojson = _json.loads(r.read().decode())
    except Exception:
        # 网络失败兜底：返回简单热力柱状图
        fallback = px.bar(df, x=location_col, y=value_col,
                         title=title + "（地图加载失败 - 展示柱状图）",
                         color=value_col,
                         color_continuous_scale=[[0, NEON_BLUE], [1, NEON_PINK]])
        fallback.update_layout(height=420, plot_bgcolor=BG_DARK,
                              paper_bgcolor=BG_DARK,
                              font=dict(color=TEXT_LIGHT))
        return fallback

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=df[location_col],
        z=df[value_col],
        featureidkey="properties.name",
        colorscale=[[0, "#1E1B4B"], [0.3, NEON_BLUE], [0.6, NEON_PURPLE],
                    [0.85, NEON_PINK], [1, NEON_RED]],
        marker=dict(line=dict(color="rgba(91,200,255,0.4)", width=0.5)),
        colorbar=dict(thickness=10, len=0.6,
                     tickfont=dict(color=TEXT_LIGHT, size=9),
                     title=dict(text="检出率(%)",
                               font=dict(color=TEXT_LIGHT, size=10))),
    ))
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor=BG_DARK,
    )
    fig.update_layout(
        title=dict(text=title, x=0.0, xanchor="left",
                  font=dict(size=13, color=TEXT_LIGHT)),
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_LIGHT),
        margin=dict(l=10, r=10, t=42, b=10),
        height=420,
    )
    return fig


def neon_radar(categories: list, values: list, title: str) -> go.Figure:
    """雷达图：风险因子重要性。边缘 label 不被裁，长名自动换行。"""
    # 长 label 自动换行（>4 字插入 <br>）
    short_cats = []
    for c in categories:
        c_clean = c.replace("_小时", "").replace("日均", "")
        if len(c_clean) <= 4:
            short_cats.append(c_clean)
        else:
            # 在第 4 字后换行（HTML <br>）
            short_cats.append(c_clean[:4] + "<br>" + c_clean[4:])

    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=short_cats + [short_cats[0]],
        fill="toself",
        fillcolor="rgba(91,200,255,0.18)",
        line=dict(color=NEON_BLUE, width=2.5),
        marker=dict(size=7, color=NEON_BLUE,
                   line=dict(color="white", width=1.5)),
        hovertext=categories + [categories[0]],  # hover 时显示完整名称
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(255,255,255,0.02)",
            radialaxis=dict(
                visible=True, range=[0, max(values) * 1.18],
                tickfont=dict(color="#9CA3AF", size=9),
                gridcolor=GRID_DIM,
                # 把数值刻度放在角度轴的特定位置，避免堆叠
                angle=90, tickangle=90,
                nticks=4,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT_LIGHT, size=12),
                gridcolor=GRID_DIM,
            ),
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
        ),
        plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
        font=dict(color=TEXT_LIGHT, family="PingFang SC, Microsoft YaHei"),
        title=dict(text=title, x=0.0, xanchor="left",
                  font=dict(size=13, color=TEXT_LIGHT)),
        # 加大整体高度 + 充足 margin 让多边形撑满
        margin=dict(l=70, r=70, t=70, b=50),
        height=460,
    )
    return fig
