"""模型推理与简单可解释性工具。"""

from __future__ import annotations
import numpy as np
import pandas as pd


STUDENT_COLUMN_LABELS = {
    "年龄": "年龄",
    "性别_女": "女性",
    "睡眠时长_小时": "睡眠时长",
    "每周运动次数": "每周运动",
    "学业压力": "学业压力",
    "经济压力": "经济压力",
    "亲密关系质量": "亲密关系",
    "社会支持": "社会支持",
    "家族史": "家族史",
    "童年不良经历": "童年逆境",
    "慢性疾病": "慢性病",
    "吸烟": "吸烟",
    "饮酒": "饮酒",
    "日均屏幕时长_小时": "屏幕时长",
    "年级_大四": "大四毕业季",
    "年级_研究生": "研究生身份",
}

ELDERLY_COLUMN_LABELS = {
    "年龄": "年龄",
    "性别_女": "女性",
    "教育年数": "教育年数",
    "是否独居": "独居",
    "收入_数值": "经济收入",
    "慢性病数量": "慢性病数量",
    "ADL生活自理能力": "ADL自理能力",
    "睡眠时长_小时": "睡眠时长",
    "社会活动参与度": "社会参与",
    "子女月联系次数": "子女联系",
    "吸烟": "吸烟",
    "饮酒": "饮酒",
    "BMI": "BMI",
    "城乡_农村": "农村居住",
}


def predict_with_explain(bundle: dict, x_row: pd.DataFrame,
                         scale_score: int = None,
                         scale_max: int = 27) -> dict:
    """三模型集成 + 量表分加权融合。

    返回 final_proba（综合风险）= 0.5 × ML 集成 + 0.5 × 量表归一化
    确保 PHQ-9 / CES-D 量表得分变化能直接反映在最终风险上。

    Args:
        scale_score: PHQ-9（0-27）或 CES-D（0-30）原始得分，None 则不融合
        scale_max:   量表满分（PHQ-9=27，CES-D=30）
    """
    rf = bundle["rf"]
    lr = bundle["lr"]
    scaler = bundle["scaler"]
    features = bundle["features"]

    x = x_row[features].copy()
    rf_proba = float(rf.predict_proba(x)[0, 1])
    gb_proba = float(bundle["gb"].predict_proba(x)[0, 1])
    x_scaled = scaler.transform(x)
    lr_proba = float(lr.predict_proba(x_scaled)[0, 1])
    ml_proba = float(np.mean([rf_proba, gb_proba, lr_proba]))

    # 量表分归一化（PHQ-9 ≥ 10 已是中度临界，归一化时按线性 + 拐点处理）
    if scale_score is not None:
        # 拐点：≤4=低，5-9=轻，10+=中以上
        # 用分段映射避免平滑掩盖临床切点
        if scale_score <= 4:
            scale_proba = scale_score / 4 * 0.20    # 0-20%
        elif scale_score <= 9:
            scale_proba = 0.20 + (scale_score - 4) / 5 * 0.30  # 20-50%
        elif scale_score <= 14:
            scale_proba = 0.50 + (scale_score - 9) / 5 * 0.20  # 50-70%
        elif scale_score <= 19:
            scale_proba = 0.70 + (scale_score - 14) / 5 * 0.15  # 70-85%
        else:
            scale_proba = 0.85 + (scale_score - 19) / (scale_max - 19) * 0.15  # 85-100%
        scale_proba = max(0.0, min(1.0, scale_proba))
        # 加权融合：量表占 60%（更具临床权威性），ML 占 40%
        final_proba = 0.6 * scale_proba + 0.4 * ml_proba
    else:
        scale_proba = None
        final_proba = ml_proba

    contributions = (lr.coef_[0] * x_scaled[0]).tolist()

    return {
        "rf_proba": rf_proba,
        "gb_proba": gb_proba,
        "lr_proba": lr_proba,
        "ml_proba": ml_proba,           # 纯 ML 集成结果
        "scale_proba": scale_proba,     # 量表归一化概率
        "final_proba": final_proba,     # 综合最终风险
        "contributions": contributions,
        "features": features,
    }


def risk_label_and_advice(proba: float, group: str = "student",
                          scale_score: int = None) -> dict:
    """风险等级判定。

    若提供 scale_score（PHQ-9 / CES-D 总分），**以量表临床切点为主**
    （Kroenke 2001 / CHARLS 标准），保证量表为 0-4 时结论必为"低风险"。
    """
    if scale_score is not None:
        if scale_score <= 4:
            return {
                "level": "低风险", "color": "#A6E3A1",
                "summary": "量表未提示明显抑郁症状（PHQ-9 ≤ 4 / CES-D < 10）。",
                "advice": [
                    "保持当前的生活与社交节奏。",
                    "建议每年进行一次心理体检（PHQ-9 / CES-D 量表）。",
                    "若近期情绪、睡眠出现持续 2 周以上变化，重新评估。",
                ],
            }
        if scale_score <= 9:
            return {
                "level": "轻度关注", "color": "#FFE066",
                "summary": "量表提示轻度抑郁症状，建议自我调节并关注变化。",
                "advice": [
                    "保证 7-8 小时规律睡眠，减少夜间使用屏幕。",
                    "每周不少于 3 次中等强度运动（每次 ≥30 分钟）。",
                    "主动与家人朋友、辅导员/同事交流近况。",
                    "可使用学校 / 单位心理咨询资源进行一次咨询。",
                ],
            }
        if scale_score <= 14:
            return {
                "level": "中度风险", "color": "#FF9F45",
                "summary": "量表提示中度抑郁症状，建议尽快寻求专业评估。",
                "advice": [
                    "建议两周内前往学校心理中心 / 三甲医院精神（心理）科评估。",
                    "进行规范的 PHQ-9 + GAD-7 量表筛查。",
                    "记录近一个月情绪、睡眠、社交日记，复诊时供医生参考。",
                    "暂时减少高强度学业 / 工作负担。",
                ],
            }
        return {
            "level": "高风险", "color": "#F25F5C",
            "summary": "量表提示中重度及以上抑郁，强烈建议立即寻求专业医疗干预。",
            "advice": [
                "尽快前往三甲医院精神（心理）科或专科医院就诊。",
                "如出现自伤 / 自杀念头，请立即拨打 24 小时心理援助热线 400-161-9995。",
                "告知一位你信任的家人或朋友当前的状态，避免独处。",
                "暂停做出重大人生决定（休学、辞职、离婚等）。",
            ],
        }
    # 兼容老调用：仅基于 proba 判定
    if proba < 0.30:
        return {
            "level": "低风险",
            "color": "#A6E3A1",
            "summary": "当前未表现出显著抑郁倾向。",
            "advice": [
                "保持当前的生活与社交节奏。",
                "建议每年进行一次心理体检（PHQ-9 / CES-D 量表）。",
                "若近期情绪、睡眠出现持续 2 周以上变化，重新评估。",
            ],
        }
    if proba < 0.50:
        return {
            "level": "轻度关注",
            "color": "#FFE066",
            "summary": "存在一定抑郁倾向，建议自我调节并关注变化。",
            "advice": [
                "保证 7-8 小时规律睡眠，减少夜间使用屏幕。",
                "每周不少于 3 次中等强度运动（每次 ≥30 分钟）。",
                "主动与家人朋友、辅导员/同事交流近况。",
                "可使用学校 / 单位心理咨询资源进行一次咨询。",
            ],
        }
    if proba < 0.70:
        return {
            "level": "中度风险",
            "color": "#FF9F45",
            "summary": "抑郁风险较高，建议尽快寻求专业评估。",
            "advice": [
                "建议两周内前往学校心理中心 / 三甲医院精神（心理）科评估。",
                "进行规范的 PHQ-9 + GAD-7 量表筛查。",
                "记录近一个月情绪、睡眠、社交日记，复诊时供医生参考。",
                "暂时减少高强度学业 / 工作负担，避免独自决策重大事项。",
            ],
        }
    return {
        "level": "高风险",
        "color": "#F25F5C",
        "summary": "存在明显抑郁倾向，强烈建议立即寻求专业医疗干预。",
        "advice": [
            "尽快前往三甲医院精神（心理）科或专科医院就诊。",
            "如出现自伤 / 自杀念头，请立即拨打 24 小时心理援助热线 400-161-9995。",
            "告知一位你信任的家人或朋友当前的状态，避免独处。",
            "暂停做出重大人生决定（休学、辞职、离婚等）。",
        ],
    }


def column_labels(group: str) -> dict:
    return STUDENT_COLUMN_LABELS if group == "student" else ELDERLY_COLUMN_LABELS
