"""
用户测试数据分析（仅完整版 / 评委版可见）
=====================================
从 Supabase 实时读取测试用户提交的评估 + 反馈数据，
反向验证模型可行性、量化用户满意度。

测试模式访问会被自动跳转回评估页。
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr

from utils.test_mode import (
    redirect_if_test_mode_non_assessment,
    fetch_from_supabase,
)
from utils.dark_charts import NEON_BLUE, NEON_PINK, NEON_PURPLE, NEON_GREEN, BG_DARK, TEXT_LIGHT


st.set_page_config(page_title="用户测试数据 | 知忧·解郁", page_icon="📈", layout="wide")

# 测试模式：自动跳转评估页（同学测试用户看不到这页）
redirect_if_test_mode_non_assessment()

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
h2, h3 {color: #5BC8FF !important;}
.kpi-card {
    background: linear-gradient(135deg, rgba(91,127,255,0.12), rgba(167,139,250,0.06));
    border: 1px solid rgba(91,200,255,0.25);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.kpi-label {font-size: 12px; color: #9CA3AF; letter-spacing: 1px;
            text-transform: uppercase;}
.kpi-value {font-size: 28px; font-weight: 800; color: #E8F0FF; margin-top: 4px;}
.kpi-sub {font-size: 11px; color: #5BC8FF; margin-top: 2px;}
.empty-state {
    background: rgba(91,200,255,0.05);
    border: 1px dashed rgba(91,200,255,0.3);
    border-radius: 10px;
    padding: 32px;
    text-align: center;
    color: #9CA3AF;
    margin: 30px 0;
}
</style>
""", unsafe_allow_html=True)


st.title("📈 用户测试数据 · 模型验证")
st.caption("基于 Supabase 实时回流的真实用户填写数据，"
           "反向验证 PHQ-9 / CES-D 量表与机器学习模型的一致性。")


# ============================================================
# 拉数据
# ============================================================
@st.cache_data(ttl=60, show_spinner="📡 拉取最新数据...")
def load_responses():
    rows = fetch_from_supabase("user_responses", limit=2000)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


@st.cache_data(ttl=60, show_spinner=False)
def load_feedback():
    rows = fetch_from_supabase("user_feedback", limit=2000)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


col_refresh, col_info = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_info:
    st.caption("💡 数据每 60 秒自动刷新一次，或手动点「刷新数据」立即拉取最新。")


df_resp = load_responses()
df_fb = load_feedback()

# 仅保留测试模式的数据（mode='test'），完整版的"自测"数据排除
if not df_resp.empty and "mode" in df_resp.columns:
    df_resp_test = df_resp[df_resp["mode"] == "test"].copy()
else:
    df_resp_test = df_resp

if not df_fb.empty and "mode" in df_fb.columns:
    df_fb_test = df_fb[df_fb["mode"] == "test"].copy()
else:
    df_fb_test = df_fb


# ============================================================
# 顶部 KPI
# ============================================================
n_total = len(df_resp_test)
n_student = int((df_resp_test["group_type"] == "student").sum()) if "group_type" in df_resp_test.columns else 0
n_elderly = int((df_resp_test["group_type"] == "elderly").sum()) if "group_type" in df_resp_test.columns else 0

# 反馈完成率：用 session_id 关联（避免历史孤立反馈让比率虚高 > 100%）
# 只统计"既有评估、又有反馈"的 session 数量占评估总数的比例
n_feedback_total = len(df_fb_test)  # 反馈原始数（含所有,用于主观评价聚合）
if n_total > 0 and not df_fb_test.empty and \
   "session_id" in df_resp_test.columns and "session_id" in df_fb_test.columns:
    resp_sessions = set(df_resp_test["session_id"].dropna().unique())
    fb_sessions = set(df_fb_test["session_id"].dropna().unique())
    matched_sessions = resp_sessions & fb_sessions
    n_feedback = len(matched_sessions)
    feedback_rate = min(n_feedback / n_total * 100, 100)  # 上限 100%
else:
    n_feedback = 0
    feedback_rate = 0

st.markdown("### 📊 测试覆盖总览")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">👥 累计测试人数</div>
<div class="kpi-value">{n_total}</div>
<div class="kpi-sub">来自匿名用户测试</div>
</div>
""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">🎓 学生 / 成人</div>
<div class="kpi-value">{n_student}</div>
<div class="kpi-sub">PHQ-9 量表评估</div>
</div>
""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">🧓 中老年</div>
<div class="kpi-value">{n_elderly}</div>
<div class="kpi-sub">CES-D 10 量表评估</div>
</div>
""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">📝 反馈完成率</div>
<div class="kpi-value">{feedback_rate:.0f}%</div>
<div class="kpi-sub">{n_feedback} / {n_total}</div>
</div>
""", unsafe_allow_html=True)


# 数据为空时的友好提示
if df_resp_test.empty:
    st.markdown("""
<div class="empty-state">
<h3 style="color:#5BC8FF;">📡 暂无用户测试数据</h3>
<p>用户通过 <code>?mode=test</code> 提交评估后，数据会实时同步到这里。</p>
<p style="font-size:12px; margin-top:10px;">
若已有测试用户，请检查 Supabase 配置或点击「🔄 刷新数据」。
</p>
</div>
""", unsafe_allow_html=True)
    st.stop()


# ============================================================
# 1. 样本人口学概览
# ============================================================
st.markdown("---")
st.markdown("### 👥 样本人口学概览")

col_a, col_b = st.columns(2)

with col_a:
    if "age" in df_resp_test.columns and df_resp_test["age"].notna().sum() > 0:
        fig_age = px.histogram(
            df_resp_test, x="age", color="group_type",
            nbins=20, title="年龄分布（按人群）",
            color_discrete_map={"student": NEON_BLUE, "elderly": NEON_PINK},
        )
        fig_age.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=320,
            margin=dict(t=50, b=40, l=40, r=20),
            legend=dict(orientation="h", y=-0.18),
        )
        st.plotly_chart(fig_age, use_container_width=True,
                       config={"displayModeBar": False})

with col_b:
    if "gender" in df_resp_test.columns and df_resp_test["gender"].notna().sum() > 0:
        gender_counts = df_resp_test["gender"].value_counts().reset_index()
        gender_counts.columns = ["性别", "人数"]
        fig_gender = px.pie(
            gender_counts, values="人数", names="性别",
            title="性别分布", hole=0.4,
            color_discrete_sequence=[NEON_BLUE, NEON_PINK],
        )
        fig_gender.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=320,
            margin=dict(t=50, b=40, l=40, r=40),
        )
        st.plotly_chart(fig_gender, use_container_width=True,
                       config={"displayModeBar": False})


# ============================================================
# 2. 量表分数分布
# ============================================================
st.markdown("---")
st.markdown("### 📐 量表分数分布与检出率")

col_phq, col_ces = st.columns(2)

with col_phq:
    phq_data = df_resp_test[df_resp_test["scale_name"] == "PHQ-9"].copy() \
        if "scale_name" in df_resp_test.columns else pd.DataFrame()
    if not phq_data.empty:
        fig_phq = px.histogram(
            phq_data, x="scale_score", nbins=14,
            title=f"PHQ-9 总分分布（n = {len(phq_data)}）",
            color_discrete_sequence=[NEON_BLUE],
        )
        fig_phq.add_vline(x=10, line_dash="dash", line_color="#F25F5C",
                         annotation_text="临床切点 ≥10", annotation_position="top")
        fig_phq.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=320,
            xaxis_title="PHQ-9 总分", yaxis_title="人数",
            margin=dict(t=50, b=40, l=40, r=20),
        )
        st.plotly_chart(fig_phq, use_container_width=True,
                       config={"displayModeBar": False})
        positive_rate = (phq_data["scale_score"] >= 10).mean() * 100
        st.caption(f"💡 PHQ-9 ≥ 10 检出率: **{positive_rate:.1f}%** "
                   f"(参考 Gao 2020 大学生 ~21%)")
    else:
        st.info("暂无 PHQ-9 数据")

with col_ces:
    ces_data = df_resp_test[df_resp_test["scale_name"] == "CES-D 10"].copy() \
        if "scale_name" in df_resp_test.columns else pd.DataFrame()
    if not ces_data.empty:
        fig_ces = px.histogram(
            ces_data, x="scale_score", nbins=16,
            title=f"CES-D 10 总分分布（n = {len(ces_data)}）",
            color_discrete_sequence=[NEON_PINK],
        )
        fig_ces.add_vline(x=10, line_dash="dash", line_color="#F25F5C",
                         annotation_text="临床切点 ≥10", annotation_position="top")
        fig_ces.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=320,
            xaxis_title="CES-D 总分", yaxis_title="人数",
            margin=dict(t=50, b=40, l=40, r=20),
        )
        st.plotly_chart(fig_ces, use_container_width=True,
                       config={"displayModeBar": False})
        positive_rate = (ces_data["scale_score"] >= 10).mean() * 100
        st.caption(f"💡 CES-D ≥ 10 检出率: **{positive_rate:.1f}%** "
                   f"(参考 CHARLS 中老年 ~15-30%)")
    else:
        st.info("暂无 CES-D 数据")


# ============================================================
# 3. ⭐ 模型可行性验证（核心王牌）
# ============================================================
st.markdown("---")
st.markdown("### 🎯 模型可行性验证：量表分 vs ML 概率")
st.caption("散点越紧密贴近趋势线，证明 ML 模型与临床量表越一致 —— **答辩核心证据**")

if "scale_score" in df_resp_test.columns and "final_proba" in df_resp_test.columns:
    valid = df_resp_test.dropna(subset=["scale_score", "final_proba"]).copy()
    valid["scale_score"] = pd.to_numeric(valid["scale_score"], errors="coerce")
    valid["final_proba"] = pd.to_numeric(valid["final_proba"], errors="coerce")
    valid = valid.dropna(subset=["scale_score", "final_proba"])

    if len(valid) >= 3:
        # 归一化 scale_score 到 0-1（PHQ-9: /27, CES-D: /30）
        def norm_score(row):
            return row["scale_score"] / 27.0 if row["scale_name"] == "PHQ-9" \
                else row["scale_score"] / 30.0
        valid["scale_norm"] = valid.apply(norm_score, axis=1)

        # Pearson 相关
        r, p = pearsonr(valid["scale_norm"], valid["final_proba"])

        fig_scatter = px.scatter(
            valid, x="scale_norm", y="final_proba",
            color="group_type",
            color_discrete_map={"student": NEON_BLUE, "elderly": NEON_PINK},
            labels={"scale_norm": "量表归一化分数 (0-1)",
                    "final_proba": "ML 综合风险概率",
                    "group_type": "人群"},
            title=f"散点图：Pearson r = {r:.3f}, p = {p:.4f} (n = {len(valid)})",
        )
        # 对角线参考线
        fig_scatter.add_shape(
            type="line", x0=0, y0=0, x1=1, y1=1,
            line=dict(color="#A6E3A1", dash="dash", width=2),
        )
        fig_scatter.update_traces(marker=dict(size=10, opacity=0.75,
                                              line=dict(color="white", width=0.5)))
        fig_scatter.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=420,
            margin=dict(t=60, b=50, l=60, r=20),
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_scatter, use_container_width=True,
                       config={"displayModeBar": False})

        # 模型评价
        if r >= 0.7:
            verdict_color = "#A6E3A1"
            verdict = (f"✅ **模型与量表高度一致** (r = {r:.3f})。"
                       "ML 模型的风险概率与临床金标准量表的归一化分数呈强正相关，"
                       "表明模型有效捕捉到了量表所反映的核心抑郁信号。")
        elif r >= 0.5:
            verdict_color = "#FFE066"
            verdict = (f"🟡 **模型与量表中度一致** (r = {r:.3f})。"
                       "存在显著正相关，但仍有改进空间。")
        else:
            verdict_color = "#FF9F45"
            verdict = (f"⚠️ **样本量较小或相关性较弱** (r = {r:.3f})。"
                       "建议继续收集更多用户数据进行验证。")

        st.markdown(f"""
<div style="background:{verdict_color}22; border-left:4px solid {verdict_color};
padding:14px 18px; border-radius:6px; font-size:14px; margin-top:10px;">
{verdict}
</div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"样本量太小（{len(valid)} < 3），无法做相关性分析。")
else:
    st.info("缺少 scale_score 或 final_proba 字段，无法分析。")


# ============================================================
# 4. 风险因子频次
# ============================================================
st.markdown("---")
st.markdown("### 🔍 真实用户的 Top 1 风险因子频次")

if "top_factor_1" in df_resp_test.columns:
    factor_counts = df_resp_test["top_factor_1"].dropna()
    factor_counts = factor_counts[factor_counts != ""].value_counts().head(10)
    if not factor_counts.empty:
        fig_factor = px.bar(
            x=factor_counts.values, y=factor_counts.index,
            orientation="h",
            labels={"x": "出现次数", "y": "风险因子"},
            title=f"Top 10 风险因子频次 (n = {len(df_resp_test)})",
            color_discrete_sequence=[NEON_PURPLE],
        )
        fig_factor.update_layout(
            plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
            font=dict(color=TEXT_LIGHT, size=12),
            title_font_size=14, height=380,
            margin=dict(t=50, b=40, l=140, r=20),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_factor, use_container_width=True,
                       config={"displayModeBar": False})
    else:
        st.info("暂无风险因子数据")


# ============================================================
# 5. 用户主观反馈
# ============================================================
st.markdown("---")
st.markdown("### 💬 用户主观评价")

if not df_fb_test.empty:
    score_cols = {
        "clarity_score": "量表清晰度",
        "trust_score": "结果可信度",
        "ai_helpfulness_score": "AI 助手帮助",
        "ui_score": "整体使用体验",
    }
    nps_col = "nps_score"

    # 四项均分
    cols_kpi = st.columns(4)
    for (col_name, label), col in zip(score_cols.items(), cols_kpi):
        if col_name in df_fb_test.columns:
            scores = pd.to_numeric(df_fb_test[col_name], errors="coerce").dropna()
            scores = scores[scores > 0]  # 排除"未使用"等空值
            avg = scores.mean() if len(scores) > 0 else 0
            with col:
                st.markdown(f"""
<div class="kpi-card">
<div class="kpi-label">{label}</div>
<div class="kpi-value">{avg:.2f} <span style="font-size:14px;color:#9CA3AF;">/ 5</span></div>
<div class="kpi-sub">n = {len(scores)}</div>
</div>
""", unsafe_allow_html=True)

    # 推荐意愿 / NPS
    # 标准 NPS（Bain 公司商业版）用 9-10/7-8/0-6,但中文学生场景打分偏保守,
    # 6-7 分实际是中性评价。我们采用宽松版分段 8-10/6-7/0-5,更贴合中国问卷文化。
    if nps_col in df_fb_test.columns:
        nps_scores = pd.to_numeric(df_fb_test[nps_col], errors="coerce").dropna()
        if len(nps_scores) > 0:
            avg_recommend = nps_scores.mean()  # 主指标:平均推荐意愿(无门槛偏差)
            # 宽松版 NPS 分段（适配中文场景）
            promoters = (nps_scores >= 8).sum()
            detractors = (nps_scores <= 5).sum()
            passives = len(nps_scores) - promoters - detractors
            nps = (promoters - detractors) / len(nps_scores) * 100

            col_avg, col_nps, col_chart = st.columns([1, 1, 2])
            with col_avg:
                # 主指标:平均推荐意愿(0-10,最直观)
                rec_color = ("#A6E3A1" if avg_recommend >= 8
                             else "#5BC8FF" if avg_recommend >= 6
                             else "#FFE066" if avg_recommend >= 4
                             else "#F25F5C")
                st.markdown(f"""
<div class="kpi-card" style="border-color:{rec_color};">
<div class="kpi-label">推荐意愿均分</div>
<div class="kpi-value" style="color:{rec_color};">{avg_recommend:.1f}<span style="font-size:14px;color:#9CA3AF;"> / 10</span></div>
<div class="kpi-sub">n = {len(nps_scores)}</div>
</div>
""", unsafe_allow_html=True)
            with col_nps:
                nps_color = "#A6E3A1" if nps >= 30 else "#5BC8FF" if nps >= 0 else "#FFE066" if nps >= -20 else "#F25F5C"
                st.markdown(f"""
<div class="kpi-card" style="border-color:{nps_color};">
<div class="kpi-label">NPS 净推荐值</div>
<div class="kpi-value" style="color:{nps_color};">{nps:+.0f}</div>
<div class="kpi-sub">推荐 {promoters} · 中立 {passives} · 贬损 {detractors}</div>
</div>
""", unsafe_allow_html=True)
            with col_chart:
                fig_nps = go.Figure(go.Bar(
                    x=["推荐者 (8-10)", "中立 (6-7)", "贬损 (0-5)"],
                    y=[promoters, passives, detractors],
                    marker_color=["#A6E3A1", "#FFE066", "#F25F5C"],
                ))
                fig_nps.update_layout(
                    plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
                    font=dict(color=TEXT_LIGHT, size=11),
                    title="推荐意愿三段分布（适配中文学生场景）", title_font_size=13,
                    height=200, margin=dict(t=40, b=30, l=40, r=20),
                )
                st.plotly_chart(fig_nps, use_container_width=True,
                               config={"displayModeBar": False})

            st.caption("💡 **关于 NPS 分段**：标准 NPS（Bain 1993）用 9-10 / 7-8 / 0-6,"
                       "在中文学生填问卷场景下打分普遍偏保守,我们采用宽松版 **8-10 / 6-7 / 0-5**,"
                       "更贴合中国问卷文化。**平均推荐意愿均分**为最直观指标,无门槛偏差。")

    # 开放反馈原文
    if "open_feedback" in df_fb_test.columns:
        feedback_texts = df_fb_test["open_feedback"].dropna()
        feedback_texts = feedback_texts[feedback_texts.astype(str).str.strip() != ""]
        if len(feedback_texts) > 0:
            st.markdown("#### 📝 用户开放反馈原文")
            for i, txt in enumerate(feedback_texts.head(15), 1):
                st.markdown(
                    f"<div style='background:rgba(91,127,255,0.08); "
                    f"border-left:3px solid {NEON_PURPLE}; padding:10px 14px; "
                    f"border-radius:6px; margin:6px 0; font-size:13px; color:#E8F0FF;'>"
                    f"<b>#{i}</b> &nbsp; {txt}</div>",
                    unsafe_allow_html=True,
                )
else:
    st.info("📡 暂无用户反馈数据（用户填完评估后未必填反馈）")


# ============================================================
# 6. 原始数据预览（最近 50 条，可下载）
# ============================================================
st.markdown("---")
with st.expander("🔬 查看原始数据（最近 50 条 + CSV 导出）", expanded=False):
    cols_to_show = [c for c in ["created_at", "session_id", "group_type",
                                 "scale_name", "scale_score", "scale_severity",
                                 "final_proba", "age", "gender",
                                 "top_factor_1", "top_factor_2"]
                    if c in df_resp_test.columns]
    if cols_to_show:
        st.dataframe(df_resp_test[cols_to_show].head(50),
                    use_container_width=True, height=300)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if not df_resp_test.empty:
            csv = df_resp_test.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 下载评估数据 CSV", csv,
                file_name=f"user_responses_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )
    with col_dl2:
        if not df_fb_test.empty:
            csv_fb = df_fb_test.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 下载反馈数据 CSV", csv_fb,
                file_name=f"user_feedback_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )


st.markdown("---")
st.caption("📡 数据由 Supabase 实时同步 · 仅完整版可见 · 测试模式访问会自动跳转到评估页")
