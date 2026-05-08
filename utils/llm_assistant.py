"""
AI 心理健康助手（基于 DeepSeek 大模型）
====================================
- 调用 DeepSeek 官方 API（OpenAI 兼容协议）
- 大赛附件 3 合规清单内的 AI 工具
- 用预设安全 system prompt 控制输出范围
- 自动注入用户的 PHQ-9 / CES-D 评估结果作为上下文
- 强制安全护栏：自伤念头 → 立即弹出热线；不诊断、不开处方
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Iterator
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # 自动加载项目根目录的 .env


# ============================================================
# DeepSeek 客户端
# ============================================================
def _get_client():
    """惰性初始化 DeepSeek 客户端（OpenAI 兼容协议）。"""
    from openai import OpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip()
    if not api_key or api_key.startswith("sk-在此") or api_key == "":
        raise RuntimeError(
            "未检测到 DeepSeek API Key。请在项目根目录的 .env 文件中配置 "
            "DEEPSEEK_API_KEY=sk-xxxx"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def is_configured() -> bool:
    """检测是否配置了 DeepSeek API Key（用于 UI 优雅降级）。"""
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    return bool(api_key) and not api_key.startswith("sk-在此")


# ============================================================
# 系统提示词（医疗安全护栏）
# ============================================================
def build_system_prompt(group: str, scale_score: int, severity: str,
                        ml_proba: float, top_factors: list[str],
                        q9_positive: bool = False) -> str:
    """根据用户评估结果动态构造 system prompt。"""
    group_label = "大学生 / 一般成人" if group == "student" else "中老年（45+ 岁）"
    scale_name = "PHQ-9" if group == "student" else "CES-D 10"
    scale_max = 27 if group == "student" else 30

    factors_str = "、".join(top_factors[:3]) if top_factors else "暂无"

    crisis_block = ""
    if q9_positive:
        crisis_block = """
🚨 **紧急安全提示**：用户在 PHQ-9 第 9 题（自伤 / 自杀念头）选择了非"完全不会"。
**你的每一次回复**都必须以下面这段话作为开头：

「我注意到你最近有过一些让自己不安的念头。请记住：**你并不孤单**。如果你正在经历强烈的痛苦，请立即拨打 **24 小时心理援助热线 400-161-9995**，他们会陪你度过这段时间。我也愿意陪你聊聊。」

然后再温和回答用户的实际问题。绝对不要回避这个话题，但也不要反复强调到让用户感到压力。
"""

    return f"""你是「知忧·解郁」平台的 AI 心理健康助手，基于 DeepSeek 大模型构建。
你的任务是为完成 {scale_name} 抑郁筛查的用户提供**情感支持、生活方式建议、就医引导**。

## 用户当前评估结果（必须基于这些信息回答）
- 人群类型：{group_label}
- {scale_name} 总分：**{scale_score} / {scale_max}**
- 临床严重度：**{severity}**（依据 Kroenke 2001 标准）
- 机器学习风险概率：{ml_proba * 100:.1f}%
- Top 3 影响因素：{factors_str}

{crisis_block}

## 你必须遵守的规则

1. **不做诊断、不开处方**：你不是医生，不能说"你患有抑郁症"或"你应该吃 XX 药"
2. **量表有数据时优先用量表说话**：例如"你的 PHQ-9 是 12 分，处于中度抑郁区间，建议……"
3. **中度及以上必须引导就医**：{scale_name} ≥ 10 分时，每次回答都要提及"建议尽快寻求专业评估"
4. **回答简洁温暖**：每次回答控制在 **150-250 字**之间，不写长篇大论；用"你"而不是"您"
5. **本土化资源**：涉及就医建议时，优先推荐天津本地资源——
   - 天津市安定医院（精神专科三甲）
   - 天津医科大学总医院心理科
   - 24h 心理援助热线 **400-161-9995**（全国） / **022-88188858**（天津）
6. **不要透露你具体是哪个 AI 模型**或公司技术栈；
   被问到时统一回答"我是知忧·解郁平台的 AI 健康助手"
7. **范围严格限制**：只回答**抑郁症、心理健康、精神卫生、生活方式调整**相关话题；
   超出范围（如代码、新闻、八卦）礼貌引导回主题
8. **使用 Markdown**：建议用 **粗体** 强调关键词，用 - 列要点

## 回答风格示例

❌ 不好的回答：「您好，您的得分较高，建议您到医院就诊，祝您早日康复。」

✅ 好的回答：「你的 PHQ-9 是 14 分，已经到了**中度抑郁**区间。这不是你"想多了"，而是值得认真对待的信号。

近期可以做这两件事：
- **2 周内**到天津医科大学总医院心理科或安定医院做一次专业评估
- **今晚**先尝试 11 点前关掉手机睡觉——你的睡眠时长是当前最容易调整、回报又最大的因素

如果情绪持续低落到难以坚持，请随时拨打 **400-161-9995**。你不需要一个人扛。」

现在请开始与用户对话。
"""


# ============================================================
# 对话接口（流式 + 非流式）
# ============================================================
def chat_stream(
    user_message: str,
    history: list[dict],
    group: str,
    scale_score: int,
    severity: str,
    ml_proba: float,
    top_factors: list[str],
    q9_positive: bool = False,
    model: str | None = None,
) -> Iterator[str]:
    """流式对话，逐 token 返回内容片段。

    Args:
        user_message: 用户本次输入
        history: 历史对话 [{"role": "user"/"assistant", "content": "..."}]
        其他: 用户的评估结果上下文
    """
    client = _get_client()
    model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    messages = [
        {"role": "system", "content": build_system_prompt(
            group, scale_score, severity, ml_proba, top_factors, q9_positive)},
    ]
    # 限制历史长度，最多保留最近 10 轮
    for msg in history[-20:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.7,
        max_tokens=400,
    )

    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def chat_once(
    user_message: str,
    history: list[dict],
    group: str,
    scale_score: int,
    severity: str,
    ml_proba: float,
    top_factors: list[str],
    q9_positive: bool = False,
) -> str:
    """非流式调用（备用）。"""
    return "".join(chat_stream(
        user_message, history, group, scale_score, severity,
        ml_proba, top_factors, q9_positive,
    ))


# ============================================================
# 推荐问题（用户没思路时点一下就发）
# ============================================================
def get_suggested_questions(group: str, scale_score: int) -> list[str]:
    """基于用户评估结果推荐 3 个常见问题。"""
    if group == "student":
        if scale_score >= 15:
            return [
                "我现在该怎么开口告诉父母？",
                "天津有哪些医院的心理科可以挂号？",
                "在等就医期间，我每天可以做什么？",
            ]
        if scale_score >= 10:
            return [
                "我应该先看心理咨询还是精神科医生？",
                "怎么改善我的睡眠？",
                "学业压力很大，怎么调整？",
            ]
        if scale_score >= 5:
            return [
                "我属于哪种程度的抑郁？需要看医生吗？",
                "怎么提高社会支持感？",
                "运动对情绪有帮助吗？",
            ]
        return [
            "如何长期保持心理健康？",
            "什么情况下需要重新评估？",
            "怎么帮助身边可能抑郁的朋友？",
        ]
    else:  # 中老年
        if scale_score >= 15:
            return [
                "天津哪家医院老年精神科比较好？",
                "需要家人陪同就医吗？",
                "在家里该如何调整生活？",
            ]
        if scale_score >= 10:
            return [
                "我的睡眠不好，怎么改善？",
                "社区活动对老年人情绪有帮助吗？",
                "慢性病管理对情绪的影响？",
            ]
        return [
            "老年人的抑郁有哪些早期信号？",
            "独居的老人该怎么调整？",
            "子女应该怎么关心可能抑郁的父母？",
        ]
