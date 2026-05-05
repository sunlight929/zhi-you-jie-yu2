"""
临床抑郁筛查量表
==============
- PHQ-9 (Patient Health Questionnaire-9)
  Kroenke K, Spitzer RL, Williams JB. The PHQ-9: validity of a brief depression
  severity measure. J Gen Intern Med. 2001;16(9):606-13.
  全球精神科 / 内科 / 全科最广泛使用的抑郁筛查量表，
  也被国家卫生健康委员会、北京安定医院、上海市精神卫生中心等推荐使用。

- CES-D 10（中国健康与养老追踪调查 CHARLS 采用版本）
  Andresen EM, et al. Screening for depression in well older adults: evaluation
  of a short form of the CES-D. Am J Prev Med. 1994;10(2):77-84.
  CHARLS、CFPS 等中国大型人群健康调查采用，是中国老年群体抑郁筛查标准工具。

注：PHQ-9 量表为公共领域（public domain），可免费用于非商业临床和研究用途。
    CES-D 量表同样属于公共领域。
"""

from __future__ import annotations
from typing import List


# ============================================================
# PHQ-9（适用于一般人群、青年、成人）
# ============================================================

PHQ9_QUESTIONS: List[str] = [
    "1. 做事时提不起劲或没有兴趣",
    "2. 感到心情低落、沮丧或绝望",
    "3. 入睡困难、睡不安稳，或睡眠过多",
    "4. 感觉疲倦或没有活力",
    "5. 食欲不振或吃太多",
    "6. 觉得自己很糟，或觉得自己很失败,或让自己 / 家人失望",
    "7. 对事物专注有困难，例如阅读报纸或看电视时",
    "8. 动作或说话速度缓慢到别人已经察觉？或者相反——变得比平日更烦躁、坐立不安、动来动去",
    "9. 有不如死掉或用某种方式伤害自己的念头",
]

PHQ9_OPTIONS: List[str] = [
    "完全不会（0 分）",
    "好几天（1 分）",
    "超过一半的天数（2 分）",
    "几乎每天（3 分）",
]

PHQ9_OPTION_VALUES: List[int] = [0, 1, 2, 3]


def phq9_severity(score: int) -> dict:
    """根据 PHQ-9 总分给出临床严重度判定（依据 Kroenke 2001）。"""
    if score <= 4:
        return {
            "level": "无抑郁症状",
            "color": "#A6E3A1",
            "code": "minimal",
            "interpretation": "未发现明显抑郁症状。",
        }
    if score <= 9:
        return {
            "level": "轻度抑郁",
            "color": "#FFE066",
            "code": "mild",
            "interpretation": "存在轻度抑郁症状，建议关注情绪变化、自我调节，必要时寻求心理咨询。",
        }
    if score <= 14:
        return {
            "level": "中度抑郁",
            "color": "#FF9F45",
            "code": "moderate",
            "interpretation": "存在中度抑郁症状，建议尽快寻求精神科或心理科专业评估。",
        }
    if score <= 19:
        return {
            "level": "中重度抑郁",
            "color": "#F25F5C",
            "code": "moderately_severe",
            "interpretation": "存在中重度抑郁症状，建议及时就医，由精神科医师评估是否需要药物治疗。",
        }
    return {
        "level": "重度抑郁",
        "color": "#9D2933",
        "code": "severe",
        "interpretation": "存在重度抑郁症状，强烈建议立即就医并由精神科医师制定综合治疗方案。",
    }


def phq9_clinical_advice(score: int, q9_score: int) -> List[str]:
    """根据 PHQ-9 得分及 Q9（自伤念头）给出分层建议。"""
    advice: List[str] = []

    if q9_score >= 1:
        advice.append("⚠️ **第 9 题（自伤 / 自杀念头）≥ 1，需要立即关注**："
                     "请立即拨打 24 小时心理援助热线 **400-161-9995**（全国）"
                     " 或 **022-88188858**（天津），并告知一位你信任的家人或朋友。")
        advice.append("近期请避免独处，暂停做出重大人生决定。")

    if score <= 4:
        advice.extend([
            "保持规律作息、适度运动与社交活动。",
            "若两周内出现新增情绪困扰，建议重新自评。",
        ])
    elif score <= 9:
        advice.extend([
            "保证 7-8 小时规律睡眠，每周 3 次以上中等强度运动。",
            "可尝试正念冥想、写情绪日记、与亲友交流。",
            "建议在 4 周内安排一次校园 / 单位心理咨询。",
        ])
    elif score <= 14:
        advice.extend([
            "建议 2 周内前往学校心理中心或医院精神 / 心理科评估。",
            "可同时进行 GAD-7 焦虑量表筛查。",
            "记录近一个月的情绪、睡眠、社交日记，复诊时供医生参考。",
            "暂时减少高强度学业 / 工作负担。",
        ])
    elif score <= 19:
        advice.extend([
            "建议 1 周内前往三甲医院精神（心理）科或专科医院评估。",
            "由精神科医师判断是否需要心理治疗或药物治疗。",
            "避免独自做出重大决定（休学、辞职、分手等）。",
        ])
    else:
        advice.extend([
            "建议立即前往三甲医院精神专科或精神卫生中心就诊。",
            "由专业医师评估住院或日间病房治疗的必要性。",
            "请家人或朋友陪同就医，并在治疗期间提供支持。",
        ])
    return advice


# ============================================================
# CES-D 10（适用于中老年群体；CHARLS 采用版本）
# ============================================================

CESD10_QUESTIONS: List[str] = [
    "1. 我因为一些小事而烦恼",
    "2. 我做事时无法集中精力",
    "3. 我感到情绪低落",
    "4. 我觉得做任何事都很费劲",
    "5. 我对未来充满希望",      # 反向计分
    "6. 我感到害怕",
    "7. 我的睡眠不安稳",
    "8. 我很愉快",              # 反向计分
    "9. 我感到孤单",
    "10. 我觉得我无法继续我的生活",
]

# 反向计分题（索引从 0 开始）：第 5 题 (索引 4) 与第 8 题 (索引 7)
CESD10_REVERSE_INDEX = [4, 7]

CESD10_OPTIONS: List[str] = [
    "很少或根本没有（不到 1 天）",
    "不太多（1-2 天）",
    "有时（3-4 天）",
    "大多数时间（5-7 天）",
]

CESD10_OPTION_VALUES: List[int] = [0, 1, 2, 3]


def cesd10_total(raw_scores: List[int]) -> int:
    """计算 CES-D 10 总分（反向题已自动反向计分）。"""
    if len(raw_scores) != 10:
        raise ValueError("CES-D 10 必须包含 10 个条目")
    total = 0
    for i, s in enumerate(raw_scores):
        total += (3 - s) if i in CESD10_REVERSE_INDEX else s
    return total


def cesd10_severity(score: int) -> dict:
    """CES-D 10 严重度判定。
    标准临界值：≥10 提示抑郁症状阳性（Andresen 1994 / CHARLS 标准）。
    更细分级根据 CHARLS 与中老年研究文献的常用切点。
    """
    if score < 10:
        return {
            "level": "无明显抑郁症状",
            "color": "#A6E3A1",
            "code": "negative",
            "interpretation": "目前未提示明显抑郁症状，但 ≥6 分仍建议关注情绪变化。",
        }
    if score < 16:
        return {
            "level": "抑郁症状阳性（轻 - 中度）",
            "color": "#FF9F45",
            "code": "mild_moderate",
            "interpretation": "存在抑郁症状，建议尽快寻求精神科或老年心理门诊评估。",
        }
    return {
        "level": "抑郁症状阳性（重度）",
        "color": "#F25F5C",
        "code": "severe",
        "interpretation": "存在显著抑郁症状，强烈建议立即就医评估。",
    }


def cesd10_clinical_advice(score: int) -> List[str]:
    """根据 CES-D 10 得分给出分层建议（适配老年人群）。"""
    if score < 10:
        return [
            "保持规律作息，每日 6-8 小时睡眠。",
            "积极参与社区活动（广场舞、棋牌、志愿服务等）。",
            "与家人保持每周 1-2 次以上电话或见面。",
            "若慢病增加或自理能力下降，建议复测。",
        ]
    if score < 16:
        return [
            "建议 2 周内前往社区卫生服务中心精神卫生科或三甲医院老年心理 / 心身医学门诊评估。",
            "可同步评估认知功能（MMSE / MoCA）排除老年期共病。",
            "请家人加强陪伴，关注饮食、睡眠与日常活动变化。",
            "若有自杀念头，请立即拨打 **400-161-9995** 或 **022-88188858**。",
        ]
    return [
        "建议立即前往天津市安定医院、天津市第四中心医院精神科或老年心身医学门诊就诊。",
        "请家属陪同就医，告知医生近期所有躯体症状与药物使用情况。",
        "由精神科医师评估是否需要药物治疗、心理治疗或住院观察。",
        "若出现自杀念头，立即拨打急救电话 120 或心理援助热线 400-161-9995。",
    ]
