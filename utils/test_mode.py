"""
测试模式工具集（用户测试版）
===========================
为"用户测试版"提供以下能力，**不影响完整版**：

  1. URL 参数 ?mode=test 检测
  2. 测试模式 CSS：隐藏侧栏页面导航 + 右下角小标识
  3. 知情同意书弹窗（测试模式 + 首次进入时显示）
  4. 匿名数据收集 → data/user_responses.csv
  5. 用户反馈表（5 题 + 1 开放题）→ data/user_feedback.csv
  6. 非评估页跳转：测试模式下访问非评估页自动跳回评估页

设计原则：所有功能均为"加法"。默认 URL（无 ?mode=test）下：
  - render_consent_banner()  立即返回 True，不渲染
  - render_feedback_form()   直接 return，不渲染
  - inject_test_mode_css()   不注入任何 CSS
  - redirect_if_test_mode()  不做任何跳转
  - save_anonymous_response 仍会写入 CSV（mode 字段标记为 "full"）
    —— 你自己测试 / 答辩演示的数据也会被收集，多收集是好事。

数据隐私：
  - 不收集姓名、IP、手机号、设备号
  - session_id 是浏览器会话级 UUID，关闭浏览器即丢失
"""

from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RESPONSES_CSV = DATA_DIR / "user_responses.csv"
FEEDBACK_CSV = DATA_DIR / "user_feedback.csv"


# ============================================================
# Supabase 云数据库支持（数据持久化）
# ============================================================
# 优先写入 Supabase；失败时静默回退本地 CSV，保证用户体验不中断。
# Supabase URL 和 KEY 通过 Streamlit Secrets / 环境变量配置。
def _get_supabase_credentials() -> tuple[str, str]:
    """从 st.secrets / 环境变量读取 Supabase URL + Key。"""
    url = ""
    key = ""
    # 优先 Streamlit Secrets
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        pass
    # 兜底环境变量（本地开发可用 .env）
    if not url:
        url = os.getenv("SUPABASE_URL", "")
    if not key:
        key = os.getenv("SUPABASE_KEY", "")
    return url.strip(), key.strip()


def _is_supabase_configured() -> bool:
    url, key = _get_supabase_credentials()
    return bool(url) and bool(key)


def _post_to_supabase(table: str, payload: dict) -> bool:
    """向 Supabase 表插入一条数据。成功返回 True。
    失败静默返回 False（不影响用户主流程，会回退到本地 CSV）。"""
    if not _is_supabase_configured():
        return False
    try:
        import requests  # 延迟导入，避免本地无 requests 时崩溃
    except ImportError:
        return False

    url, key = _get_supabase_credentials()
    endpoint = f"{url}/rest/v1/{table}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    # 清洗 payload:
    # 1) timestamp 字段 Supabase 已用 created_at 自动管理，移除
    # 2) group 字段在 SQL 里是 group_type（group 是 SQL 保留字）
    # 3) 把空字符串 "" 改成 None → JSON null → Supabase INTEGER 列接受 NULL
    #    （否则学生评估时 living_alone 等中老年字段为 "" 会让 INTEGER 列拒绝）
    clean = {k: v for k, v in payload.items() if k != "timestamp"}
    if "group" in clean:
        clean["group_type"] = clean.pop("group")
    clean = {k: (None if v == "" else v) for k, v in clean.items()}
    try:
        resp = requests.post(endpoint, json=clean, headers=headers, timeout=8)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def fetch_from_supabase(table: str, select: str = "*", limit: int = 1000) -> list[dict]:
    """从 Supabase 读取数据（供评委版数据分析页使用）。
    失败返回空列表。"""
    if not _is_supabase_configured():
        return []
    try:
        import requests
    except ImportError:
        return []

    url, key = _get_supabase_credentials()
    endpoint = f"{url}/rest/v1/{table}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    params = {"select": select, "order": "created_at.desc", "limit": str(limit)}
    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


# ============================================================
# 模式检测
# ============================================================
def is_test_mode() -> bool:
    """是否为用户测试模式（URL 带 ?mode=test，或本次会话已记忆）。

    Streamlit 的 st.switch_page() 跳转时会擦掉 URL 参数，所以光靠
    URL 检测不行。本函数在首次检测到 ?mode=test 时把标志写进
    session_state，后续即使 URL 被擦也能持续识别为测试模式。

    要重新进入完整版：关闭这个浏览器标签页，重新开一个标签（不带 mode 参数）。
    """
    # 1) 会话已记忆 → 直接返回
    if st.session_state.get("__test_mode_active"):
        return True
    # 2) URL 带 ?mode=test → 写入会话标志
    try:
        if st.query_params.get("mode") == "test":
            st.session_state["__test_mode_active"] = True
            return True
    except Exception:
        pass
    return False


def get_session_id() -> str:
    """获取当前会话的匿名 ID，仅用于关联同一用户的"评估"+"反馈"两条记录。
    关闭浏览器后无法再关联到本人。"""
    if "anon_session_id" not in st.session_state:
        st.session_state["anon_session_id"] = uuid.uuid4().hex[:12]
    return st.session_state["anon_session_id"]


# ============================================================
# 测试模式 CSS：隐藏侧栏导航 + 右下角小标识
# ============================================================
def inject_hide_branding_css():
    """全局隐藏 Streamlit Cloud 的 Fork on GitHub / Manage app 等品牌元素。
    所有页面都应调用此函数(完整版 + 测试版),保护源码隐私 + 答辩仪表清爽。
    """
    # 隐藏策略:
    #  1) GitHub 链接(凡是 a[href=github] 的直接干掉)
    #  2) Deploy 按钮(右上角"Deploy")
    #  3) 整个汉堡菜单 #MainMenu / stMainMenu —— 里面的"View app source"
    #     是 JS 按钮(不是 <a>),CSS 抓不到 href,只能整块隐藏。
    #     评委不需要 Streamlit 默认菜单(Settings/Print/About),浏览器自带功能足够。
    #  4) 右下角"Made with Streamlit / View source"小徽章 viewerBadge
    #  5) 绝不隐藏 stToolbar / stHeaderActionElements 等容器——侧栏展开按钮
    #     在这些容器内,隐藏会导致侧栏收起后无法展开。
    st.markdown(
        """
    <style>
    /* 1) 任何 GitHub 链接 */
    a[href*="github.com"],
    a[href*="github.io"] {
        display: none !important;
    }
    /* 2) Deploy 按钮(明确 testid,确定不含侧栏控制) */
    [data-testid="stAppDeployButton"],
    .stAppDeployButton {
        display: none !important;
    }
    /* 3) 汉堡菜单(包含"View app source"→ GitHub 仓库的入口) */
    #MainMenu,
    [data-testid="stMainMenu"] {
        display: none !important;
    }
    /* 4) 右下角"Made with Streamlit / View source"徽章(类名带 hash) */
    [class*="viewerBadge"] {
        display: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def inject_test_mode_css():
    """仅在测试模式下注入 CSS：
    - 隐藏整个侧栏（AI 助手改为主页面底部渲染）
    - 移动端单列布局 + 字号 + padding 适配
    - 右下角"用户测试版 v1"小标识

    完整版下完全不注入，零影响。
    """
    if not is_test_mode():
        return
    st.markdown(
        """
    <style>
    /* ===== 测试模式：隐藏整个侧栏（AI 助手挪到主页面底部） ===== */
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}

    /* 隐藏后主内容自动占满 */
    [data-testid="stMainBlockContainer"],
    .main .block-container {
        max-width: 100% !important;
    }

    /* ===== 测试模式右下角小标识 ===== */
    .test-mode-badge {
        position: fixed;
        bottom: 12px; right: 14px;
        background: rgba(91,200,255,0.15);
        border: 1px solid rgba(91,200,255,0.4);
        color: #5BC8FF;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 11px;
        z-index: 9999;
        pointer-events: none;
    }

    /* ===== 移动端适配（屏幕宽度 < 768px） ===== */
    @media (max-width: 768px) {
        /* 所有 Streamlit 多列布局强制变单列堆叠 + 足够间距避免卡片视觉重叠 */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 18px !important;
        }
        [data-testid="stColumn"],
        [data-testid="column"] {
            min-width: 100% !important;
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* 得分卡之间额外加 margin 避免边框紧贴重叠 */
        .score-card {
            margin-bottom: 6px !important;
            padding: 16px 14px !important;
        }

        /* 整体 padding 减少，多出屏幕空间 */
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding: 1rem 0.6rem 4rem 0.6rem !important;
            max-width: 100% !important;
        }

        /* 标题缩小，避免折行太严重 */
        .stApp h1 {font-size: 22px !important; line-height: 1.3 !important;}
        .stApp h2 {font-size: 18px !important; line-height: 1.3 !important;}
        .stApp h3 {font-size: 16px !important; line-height: 1.3 !important;}

        /* PHQ-9 / CES-D 量表题目（标题部分） */
        .stRadio > label {
            font-size: 14.5px !important;
            line-height: 1.5 !important;
            margin-bottom: 8px !important;
            font-weight: 500 !important;
        }
        /* 单选项变垂直堆叠（手机上 4 个横排太挤） */
        .stRadio [role="radiogroup"] {
            flex-direction: column !important;
            gap: 8px !important;
            align-items: stretch !important;
            padding-left: 0 !important;
            margin-left: 0 !important;
        }
        /* 每个选项变成统一卡片：圆点 + 文字水平居中对齐，宽度填满，对齐整齐 */
        .stRadio [role="radiogroup"] > label {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            min-height: 42px !important;
            padding: 10px 14px !important;
            background: rgba(91,127,255,0.06) !important;
            border: 1px solid rgba(91,200,255,0.20) !important;
            border-radius: 8px !important;
            margin: 0 !important;
            font-size: 14px !important;
            cursor: pointer !important;
        }
        /* 选中状态的选项卡片高亮 */
        .stRadio [role="radiogroup"] > label:has(input:checked) {
            background: rgba(91,200,255,0.16) !important;
            border-color: rgba(91,200,255,0.6) !important;
        }

        /* 按钮加大，方便手指点 */
        .stButton > button,
        .stFormSubmitButton > button {
            min-height: 44px !important;
            font-size: 15px !important;
            padding: 10px 16px !important;
        }

        /* 得分卡 - 数字缩小，避免溢出 */
        .score-num {font-size: 30px !important;}
        .score-label {font-size: 11px !important;}

        /* 量表小节标题 */
        .scale-title {font-size: 14px !important; padding-left: 8px !important;}
        .scale-subtitle {font-size: 11px !important;}

        /* 输入框、selectbox、slider 字号 */
        .stTextInput input, .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] {
            font-size: 14px !important;
        }
        .stSlider [data-baseweb="slider"] {
            margin-top: 4px !important;
        }

        /* Plotly 图表容器：自动缩放 */
        .stPlotlyChart {
            width: 100% !important;
            overflow-x: auto !important;
        }

        /* 警告框、信息框：padding 减小 */
        .warn-box, .score-card {
            padding: 12px 14px !important;
        }

        /* 知情同意书卡片 */
        .stApp p {font-size: 13px !important;}
    }

    /* ===== 更小的手机（< 400px）进一步压缩 ===== */
    @media (max-width: 400px) {
        .stApp h1 {font-size: 19px !important;}
        .score-num {font-size: 26px !important;}
    }
    </style>
    <div class="test-mode-badge">用户测试版 v1</div>
    """,
        unsafe_allow_html=True,
    )


# ============================================================
# 温和措辞映射（避免测试用户被"中度抑郁"等临床标签吓到）
# ============================================================
# 完整版（评委 / 答辩）保留原临床标签，体现医学专业性
# 测试模式（同学测试）用更温和的措辞，强调"情绪状态"而非"疾病"
_SOFTEN_LABEL_MAP = {
    # PHQ-9 量表严重度
    "无抑郁症状": "情绪状态良好",
    "轻度抑郁": "轻度情绪困扰",
    "中度抑郁": "中等情绪压力",
    "中重度抑郁": "较明显的情绪压力",
    "重度抑郁": "显著情绪困扰",
    # CES-D 10 量表严重度
    "无明显抑郁症状": "情绪状态良好",
    "抑郁症状阳性（轻 - 中度）": "情绪压力信号（轻-中）",
    "抑郁症状阳性（重度）": "显著情绪压力信号",
    # ML 风险分级
    "低风险": "低风险",  # 已足够温和，保留
    "轻度关注": "轻度关注",  # 已足够温和，保留
    "中度风险": "中等风险信号",
    "高风险": "较高风险信号",
}


def soften_severity_label(level: str) -> str:
    """测试模式下把临床严重度标签转换为温和措辞。
    完整版下原样返回（不影响答辩演示）。"""
    if not is_test_mode():
        return level
    return _SOFTEN_LABEL_MAP.get(level, level)


# 临床解释文字的温和版本（测试模式下替换得分卡底部那行小字）
# 避免出现"轻度/中度/重度抑郁症状"这种容易让人误以为是诊断的词
_SOFTEN_INTERPRETATION_MAP = {
    # PHQ-9
    "未发现明显抑郁症状。":
        "未发现明显情绪困扰。",
    "存在轻度抑郁症状，建议关注情绪变化、自我调节，必要时寻求心理咨询。":
        "近期情绪可能有一些波动，建议关注作息和压力变化，保持自我调节的好习惯。",
    "存在中度抑郁症状，建议尽快寻求精神科或心理科专业评估。":
        "近期情绪压力较明显，建议主动关注情绪状态，必要时和心理咨询师聊聊。",
    "存在中重度抑郁症状，建议及时就医，由精神科医师评估是否需要药物治疗。":
        "情绪压力较明显且可能持续，建议尽早寻求心理咨询或专业评估。",
    "存在重度抑郁症状，强烈建议立即就医并由精神科医师制定综合治疗方案。":
        "情绪困扰较显著，建议尽快寻求专业帮助。如有强烈不适请拨打 400-161-9995。",
    # CES-D 10
    "目前未提示明显抑郁症状，但 ≥6 分仍建议关注情绪变化。":
        "目前未发现明显情绪困扰，仍建议关注作息与情绪变化。",
    "存在抑郁症状，建议尽快寻求精神科或老年心理门诊评估。":
        "情绪压力可能较明显，建议家属多关心，可考虑陪同到老年心理门诊咨询。",
    "存在显著抑郁症状，强烈建议立即就医评估。":
        "情绪困扰较显著，建议尽快寻求专业帮助，家属请加强关心和陪伴。",
}


def soften_interpretation(text: str) -> str:
    """测试模式下软化得分卡底部的解释文字（去掉"抑郁症状"等吓人词）。
    完整版下原样返回。"""
    if not is_test_mode():
        return text
    return _SOFTEN_INTERPRETATION_MAP.get(text, text)


def render_test_disclaimer_banner():
    """测试模式下，在评估结果顶部显示「这不是诊断」红色提醒。
    完整版下不渲染（不影响答辩演示）。"""
    if not is_test_mode():
        return
    st.markdown(
        """
    <div style="background: rgba(239,68,68,0.10);
                border: 2px solid rgba(239,68,68,0.45);
                border-left: 5px solid #EF4444;
                border-radius: 8px;
                padding: 14px 18px;
                margin: 18px 0;
                color: #FCA5A5; font-size: 14px; line-height: 1.7;">
    <b style="color:#FCA5A5; font-size:15px;">⚠️ 体验提醒（请认真阅读）</b><br>
    你正在 <b>体验产品功能</b>。下方显示的「情绪压力」「风险信号」等标签是
    PHQ-9 / CES-D 量表国际标准的筛查结果，<b>不是临床诊断</b>，
    也不代表你患有抑郁症 —— 只代表"过去两周的情绪状态值得被关注"。<br>
    本工具 <b>不能替代精神科医师的诊断</b>。
    如果你最近确实有持续 2 周以上的情绪困扰，请咨询专业医生。
    </div>
    """,
        unsafe_allow_html=True,
    )


# ============================================================
# 知情同意书：测试模式 + 首次进入时显示
# ============================================================
def render_consent_banner() -> bool:
    """显示知情同意书。

    完整版下直接返回 True（不显示，不影响原有流程）。
    测试模式下，用户必须点击"同意"才返回 True 继续渲染评估表单；
    点"拒绝"则 st.stop() 终止页面。
    未做选择时也 st.stop() —— 防止用户跳过同意直接填表。
    """
    if not is_test_mode():
        return True

    if st.session_state.get("consent_given"):
        return True

    st.markdown(
        """
    <div style="background: linear-gradient(135deg, rgba(91,127,255,0.12), rgba(167,139,250,0.06));
                border: 1px solid rgba(91,200,255,0.4);
                border-radius: 14px;
                padding: 24px 28px;
                margin: 20px 0;">
    <h3 style="color:#5BC8FF; margin-top:0;">📋 知情同意</h3>
    <p style="color:#E8F0FF; line-height:1.8; font-size:14px; margin:8px 0 16px 0;">
    欢迎参与「<b>知忧·解郁</b>」抑郁筛查辅助工具的体验测试。本工具由<b>天津大学</b>学生团队研发，
    采用 PHQ-9 / CES-D 国际通用抑郁量表 + 机器学习模型，为你提供风险参考与生活建议。
    </p>
    <p style="color:#B8C5E0; line-height:1.85; font-size:13px; margin:0 0 14px 0;">
    <b style="color:#5BC8FF;">关于你的数据：</b><br>
    ◆ 我们 <b>仅收集匿名问卷答案、评估结果、反馈打分</b><br>
    ◆ <b>不收集</b>姓名、电话、IP、设备等任何身份信息<br>
    ◆ 数据 <b>仅用于</b>系统功能改进与学术研究报告，不用于商业用途、不对外分享<br>
    ◆ 你可以随时关闭页面退出，数据无法被追溯到你本人
    </p>
    <div style="background: rgba(239,68,68,0.10);
                border-left: 4px solid #EF4444;
                border-radius: 6px;
                padding: 12px 16px;
                color: #FCA5A5; font-size: 13px; line-height: 1.75;
                margin: 0;">
    <b style="color:#FCA5A5; font-size:14px;">⚠️ 重要提示：这不是诊断，是体验</b><br>
    完成评估后你会看到"情绪压力"「风险信号」等分级标签，
    这是 <b>筛查量表的标准提示，不是医学诊断</b>。<br>
    即使显示"中等情绪压力"也<b>不代表你患有抑郁症</b>，只代表"过去两周的情绪可能值得关注"。<br>
    本工具 <b>不能替代精神科医师的临床诊断</b>。<br>
    如出现自伤念头，请立即拨打 <b>400-161-9995</b>（24h 心理援助热线）。
    </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        if st.button(
            "✅ 我已了解，开始评估",
            type="primary",
            use_container_width=True,
            key="consent_btn_accept",
        ):
            st.session_state["consent_given"] = True
            st.rerun()
    with col2:
        if st.button("❌ 退出", use_container_width=True, key="consent_btn_decline"):
            st.warning("感谢你的关注。若改变想法，可以随时刷新页面重新参与。")
            st.stop()

    st.stop()  # 未做选择时不渲染下面的评估表单
    return False  # 兜底（实际不会执行到，st.stop 已终止）


# ============================================================
# 匿名数据收集：评估提交时调用
# ============================================================
RESPONSE_FIELDS = [
    "timestamp",
    "session_id",
    "mode",  # "test" or "full"
    "group",  # "student" or "elderly"
    "scale_name",  # "PHQ-9" or "CES-D 10"
    "scale_score",
    "scale_severity",
    "ml_proba",  # ML 集成概率
    "final_proba",  # 最终融合概率
    "age",
    "gender",
    "top_factor_1",
    "top_factor_2",
    "top_factor_3",
    # 学生特有
    "grade",
    "major",
    # 中老年特有
    "education",
    "region",
    "living_alone",
    # 生活方式（共有）
    "sleep_hours",
    "smoking",
    "drinking",
]


def save_anonymous_response(payload: dict) -> bool:
    """评估提交时静默把匿名结果存储。

    存储策略:
    1. 优先 Supabase（云数据库，持久化）
    2. 同时也写入本地 CSV（双备份，万一 Supabase 不可用也不丢数据）

    设计为永远不抛错，失败时返回 False。
    """
    # 准备完整 row
    row = {field: payload.get(field, "") for field in RESPONSE_FIELDS}
    row["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["session_id"] = get_session_id()
    row["mode"] = "test" if is_test_mode() else "full"

    # 优先写 Supabase
    supabase_ok = _post_to_supabase("user_responses", row)

    # 同时写本地 CSV（双备份）
    csv_ok = False
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        write_header = not RESPONSES_CSV.exists()
        with open(RESPONSES_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=RESPONSE_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        csv_ok = True
    except Exception:
        pass

    return supabase_ok or csv_ok


# ============================================================
# 反馈表（5 题打分 + 1 开放题）
# ============================================================
FEEDBACK_FIELDS = [
    "timestamp",
    "session_id",
    "mode",
    "clarity_score",  # 1-5
    "trust_score",  # 1-5
    "ai_helpfulness_score",  # 1-5 or empty if 未使用
    "ui_score",  # 1-5
    "nps_score",  # 0-10
    "open_feedback",
]


def _save_feedback(payload: dict) -> bool:
    """把反馈存储。Supabase + 本地 CSV 双备份。失败不抛错。"""
    row = {field: payload.get(field, "") for field in FEEDBACK_FIELDS}
    row["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["session_id"] = get_session_id()
    row["mode"] = "test" if is_test_mode() else "full"

    # Supabase
    supabase_ok = _post_to_supabase("user_feedback", row)

    # 本地 CSV 双备份
    csv_ok = False
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        write_header = not FEEDBACK_CSV.exists()
        with open(FEEDBACK_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FEEDBACK_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        csv_ok = True
    except Exception:
        pass

    return supabase_ok or csv_ok


@st.fragment
def render_feedback_form():
    """评估结果下方的反馈表（独立 fragment，避免与 AI 助手 fragment 冲突）。

    完整版下直接 return，不渲染（评委、答辩演示不会看到）。
    测试版下在评估结果末尾展开显示。

    @st.fragment 装饰器确保:
    - form 被正确检测到 submit button（修复"Missing Submit Button"错误）
    - 提交反馈后只重新渲染本表单,不影响外部已渲染的评估结果
    """
    if not is_test_mode():
        return

    if st.session_state.get("feedback_submitted"):
        st.markdown(
            """
        <div style="background: rgba(52,211,153,0.10);
                    border: 1px solid rgba(52,211,153,0.4);
                    border-left: 4px solid #34D399;
                    border-radius: 8px;
                    padding: 14px 18px;
                    margin: 20px 0;
                    color: #6EE7B7; font-size: 14px;">
        ✅ <b>感谢你的反馈！</b>你的意见已成功提交，对我们改进系统非常重要。
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    st.markdown("---")
    st.markdown("### 📝 帮我们改进 · 30 秒反馈（强烈建议填写）")
    st.caption(
        "你的反馈直接决定我们怎么改进这个工具。全部题目都是单选 / 打分，最后一题选填。"
    )

    with st.form("feedback_form_test", clear_on_submit=False):
        clarity = st.radio(
            "**1. 量表的题目你能看懂吗？**",
            ["1 - 完全看不懂", "2 - 大部分看不懂", "3 - 一般", "4 - 大部分能看懂", "5 - 完全能看懂"],
            index=3,
            horizontal=False,
        )

        trust = st.radio(
            "**2. 你觉得评估结果（风险等级、AI 建议）可信吗？**",
            ["1 - 完全不可信", "2 - 不太可信", "3 - 一般", "4 - 比较可信", "5 - 非常可信"],
            index=3,
            horizontal=False,
        )

        ai_help = st.radio(
            '**3. AI 心理健康助手的回答对你有帮助吗？**（没用过可选「未使用」）',
            ["未使用", "1 - 完全没帮助", "2 - 不太有用", "3 - 一般", "4 - 比较有用", "5 - 非常有用"],
            index=0,
            horizontal=False,
        )

        ui = st.radio(
            "**4. 整体使用体验（界面、流程）如何？**",
            ["1 - 很糟糕", "2 - 比较差", "3 - 一般", "4 - 比较好", "5 - 非常好"],
            index=3,
            horizontal=False,
        )

        nps = st.slider(
            "**5. 你有多大可能把这个工具推荐给身边可能需要的人？**（0 = 完全不会，10 = 非常愿意）",
            0,
            10,
            7,
        )

        open_text = st.text_area(
            "**6. 你觉得最需要改进的地方是什么？**（选填，1-2 句话即可）",
            placeholder="例如：某道题不好懂 / 想让 AI 多说点 / 建议增加 XX 功能……",
            max_chars=300,
            height=80,
        )

        submitted = st.form_submit_button(
            "📨 提交反馈", type="primary", use_container_width=True
        )
        if submitted:
            def _parse_score(s: str) -> int | None:
                """从 '4 - 比较好' 中解析出 4；'未使用' 返回 None。"""
                if not s or not s[0].isdigit():
                    return None
                return int(s.split(" - ")[0])

            payload = {
                "clarity_score": _parse_score(clarity) or 0,
                "trust_score": _parse_score(trust) or 0,
                "ai_helpfulness_score": _parse_score(ai_help) if _parse_score(ai_help) is not None else "",
                "ui_score": _parse_score(ui) or 0,
                "nps_score": int(nps),
                "open_feedback": open_text.strip(),
            }
            if _save_feedback(payload):
                st.session_state["feedback_submitted"] = True
                # fragment scope rerun:只重新渲染本反馈表（显示"感谢"消息）
                # 不触发整页重跑（评估结果、AI 助手都保持显示）
                st.rerun(scope="fragment")
            else:
                st.error("反馈保存失败，请稍后重试。或者把意见告诉团队成员也可以。")


# ============================================================
# 非评估页跳转：测试模式下访问非评估页 → 跳回评估页
# ============================================================
def redirect_if_test_mode_non_assessment():
    """放在非评估页（数据驾驶舱、数据全景、风险因素、天津、关于）的顶部。
    测试模式下立即跳转到评估页，避免测试用户看到不相关的内容。
    完整版下零影响。"""
    if is_test_mode():
        st.switch_page("pages/3_🧠_智能评估.py")
