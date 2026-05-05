"""
数据生成模块
==========
基于已发表流行病学研究中报告的真实分布参数，构造贴近现实的演示数据集。
研究真实数据后续可替换为：
- CHARLS（中国健康与养老追踪调查）抑郁量表数据
- Kaggle 上的 Student Mental Health 公开数据
- NHANES PHQ-9 数据

参考文献：
[1] Lei X, et al. Depressive symptoms and SES among the mid-aged and elderly in China.
    Soc Sci Med. 2014;120:224-32.
[2] Gao L, et al. Prevalence of depression among Chinese university students:
    a systematic review and meta-analysis. Sci Rep. 2020;10:15897.
    DOI: 10.1038/s41598-020-72998-1
[3] WHO. Depression and Other Common Mental Disorders: Global Health Estimates. 2017.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
DATA_DIR = Path(__file__).parent


def _phq9_from_factors(score_logit: np.ndarray) -> np.ndarray:
    """根据潜在因子打分映射到 PHQ-9 分数 (0-27)。"""
    prob = 1 / (1 + np.exp(-score_logit))
    base = prob * 27
    noise = RNG.normal(0, 2.5, size=len(prob))
    return np.clip(np.round(base + noise), 0, 27).astype(int)


def generate_student_data(n: int = 5000) -> pd.DataFrame:
    """模拟大学生群体抑郁筛查数据。"""
    age = RNG.integers(17, 26, size=n)
    gender = RNG.choice(["男", "女"], size=n, p=[0.48, 0.52])
    grade = RNG.choice(["大一", "大二", "大三", "大四", "研究生"], size=n,
                       p=[0.22, 0.22, 0.22, 0.22, 0.12])
    major = RNG.choice(
        ["医学", "理工", "文史", "经管", "艺术", "其他"], size=n,
        p=[0.18, 0.30, 0.15, 0.20, 0.07, 0.10]
    )

    sleep_hours = np.clip(RNG.normal(7.0, 1.4, size=n), 3, 11).round(1)
    exercise_per_week = np.clip(RNG.normal(2.5, 1.6, size=n), 0, 8).round(0).astype(int)

    academic_pressure = RNG.integers(1, 11, size=n)
    financial_stress = RNG.integers(1, 11, size=n)
    relationship_quality = RNG.integers(1, 11, size=n)
    social_support = RNG.integers(1, 11, size=n)

    family_history = RNG.choice([0, 1], size=n, p=[0.88, 0.12])
    childhood_adversity = RNG.choice([0, 1], size=n, p=[0.78, 0.22])
    chronic_disease = RNG.choice([0, 1], size=n, p=[0.93, 0.07])
    smoking = RNG.choice([0, 1], size=n, p=[0.85, 0.15])
    drinking = RNG.choice([0, 1], size=n, p=[0.78, 0.22])
    screen_hours = np.clip(RNG.normal(6.5, 2.5, size=n), 1, 16).round(1)

    score_logit = (
        -2.0
        + 0.45 * (gender == "女").astype(int)
        + 0.30 * (academic_pressure - 5) / 2
        + 0.40 * (financial_stress - 5) / 2
        - 0.35 * (sleep_hours - 7)
        - 0.20 * exercise_per_week / 3
        - 0.45 * (social_support - 5) / 2
        - 0.30 * (relationship_quality - 5) / 2
        + 0.85 * family_history
        + 0.95 * childhood_adversity
        + 0.40 * chronic_disease
        + 0.20 * smoking
        + 0.15 * drinking
        + 0.18 * (screen_hours - 6) / 2
        + 0.30 * (grade == "大四").astype(int)
        + 0.20 * (grade == "研究生").astype(int)
        + RNG.normal(0, 0.5, size=n)
    )

    phq9 = _phq9_from_factors(score_logit)
    depression_level = pd.cut(
        phq9,
        bins=[-1, 4, 9, 14, 19, 27],
        labels=["无", "轻度", "中度", "中重度", "重度"],
    )

    df = pd.DataFrame({
        "样本编号": [f"S{i:05d}" for i in range(1, n + 1)],
        "年龄": age,
        "性别": gender,
        "年级": grade,
        "专业类型": major,
        "睡眠时长_小时": sleep_hours,
        "每周运动次数": exercise_per_week,
        "学业压力": academic_pressure,
        "经济压力": financial_stress,
        "亲密关系质量": relationship_quality,
        "社会支持": social_support,
        "家族史": family_history,
        "童年不良经历": childhood_adversity,
        "慢性疾病": chronic_disease,
        "吸烟": smoking,
        "饮酒": drinking,
        "日均屏幕时长_小时": screen_hours,
        "PHQ9分数": phq9,
        "抑郁分级": depression_level,
        "是否抑郁": (phq9 >= 10).astype(int),
        "数据来源": "学生群体仿真数据(基于公开文献分布参数)",
    })
    return df


def generate_elderly_data(n: int = 4000) -> pd.DataFrame:
    """模拟中老年群体抑郁筛查数据（参考 CHARLS 设计）。"""
    age = np.clip(RNG.normal(65, 9, size=n), 45, 95).astype(int)
    gender = RNG.choice(["男", "女"], size=n, p=[0.49, 0.51])
    education = RNG.choice(
        ["未上学", "小学", "初中", "高中", "大专及以上"],
        size=n, p=[0.20, 0.32, 0.26, 0.14, 0.08]
    )
    region = RNG.choice(["城市", "城镇", "农村"], size=n, p=[0.32, 0.20, 0.48])
    living_alone = RNG.choice([0, 1], size=n, p=[0.78, 0.22])
    income_level = RNG.choice(["低", "中", "高"], size=n, p=[0.45, 0.42, 0.13])
    chronic_count = RNG.poisson(1.5, size=n).clip(0, 8)
    adl_score = np.clip(RNG.normal(13, 1.5, size=n), 6, 14).round(1)
    sleep_hours = np.clip(RNG.normal(6.4, 1.5, size=n), 3, 11).round(1)
    social_activity = RNG.integers(0, 8, size=n)
    family_contact_per_month = np.clip(RNG.normal(8, 5, size=n), 0, 30).round(0).astype(int)
    smoking = RNG.choice([0, 1], size=n, p=[0.74, 0.26])
    drinking = RNG.choice([0, 1], size=n, p=[0.70, 0.30])
    bmi = np.clip(RNG.normal(23.5, 3.5, size=n), 14, 40).round(1)

    edu_num = pd.Series(education).map(
        {"未上学": 0, "小学": 1, "初中": 2, "高中": 3, "大专及以上": 4}
    ).values
    income_num = pd.Series(income_level).map({"低": 0, "中": 1, "高": 2}).values

    score_logit = (
        -1.6
        + 0.55 * (gender == "女").astype(int)
        + 0.025 * (age - 65)
        + 0.35 * living_alone
        + 0.30 * (region == "农村").astype(int)
        - 0.30 * edu_num / 2
        - 0.30 * income_num
        + 0.35 * chronic_count
        - 0.40 * (adl_score - 12)
        - 0.30 * (sleep_hours - 6)
        - 0.20 * social_activity / 2
        - 0.05 * family_contact_per_month / 5
        + 0.18 * smoking
        + 0.10 * drinking
        + 0.05 * (bmi - 23.5)
        + RNG.normal(0, 0.55, size=n)
    )

    cesd = _phq9_from_factors(score_logit)
    depression_level = pd.cut(
        cesd,
        bins=[-1, 4, 9, 14, 19, 27],
        labels=["无", "轻度", "中度", "中重度", "重度"],
    )

    df = pd.DataFrame({
        "样本编号": [f"E{i:05d}" for i in range(1, n + 1)],
        "年龄": age,
        "性别": gender,
        "教育程度": education,
        "居住地区": region,
        "是否独居": living_alone,
        "经济收入": income_level,
        "慢性病数量": chronic_count,
        "ADL生活自理能力": adl_score,
        "睡眠时长_小时": sleep_hours,
        "社会活动参与度": social_activity,
        "子女月联系次数": family_contact_per_month,
        "吸烟": smoking,
        "饮酒": drinking,
        "BMI": bmi,
        "CESD分数": cesd,
        "抑郁分级": depression_level,
        "是否抑郁": (cesd >= 10).astype(int),
        "数据来源": "中老年群体仿真数据(参照CHARLS分布)",
    })
    return df


def generate_regional_summary() -> pd.DataFrame:
    """模拟天津各区抑郁筛查检出率（用于天津本地化叙事）。"""
    districts = [
        "和平区", "河东区", "河西区", "南开区", "河北区", "红桥区",
        "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区",
        "滨海新区", "宁河区", "静海区", "蓟州区"
    ]
    rng = np.random.default_rng(7)
    detection_rate = np.round(rng.uniform(8.5, 18.5, size=len(districts)), 2)
    elder_pct = np.round(rng.uniform(15, 32, size=len(districts)), 2)
    health_resource = np.round(rng.uniform(3.2, 9.8, size=len(districts)), 2)
    sample_size = rng.integers(200, 1200, size=len(districts))

    return pd.DataFrame({
        "区县": districts,
        "样本量": sample_size,
        "抑郁检出率_百分比": detection_rate,
        "60岁以上人口占比_百分比": elder_pct,
        "每千人精神卫生资源数": health_resource,
    })


def generate_province_summary() -> pd.DataFrame:
    """模拟全国 31 个省级行政区抑郁检出率（基于公开流行病学研究范围）。"""
    # 数据范围参考 Lu et al. 2021 Lancet Psychiatry 全国调查
    # 检出率范围 4.5% - 9.5%（成人）；本表演示用，按地理梯度构造
    provinces = [
        ("北京市", 8.2), ("天津市", 7.9), ("河北省", 7.1), ("山西省", 7.5),
        ("内蒙古自治区", 8.4), ("辽宁省", 8.8), ("吉林省", 9.1), ("黑龙江省", 9.6),
        ("上海市", 7.6), ("江苏省", 7.3), ("浙江省", 6.9), ("安徽省", 8.3),
        ("福建省", 6.7), ("江西省", 8.5), ("山东省", 7.4), ("河南省", 8.7),
        ("湖北省", 8.1), ("湖南省", 8.6), ("广东省", 6.5), ("广西壮族自治区", 7.8),
        ("海南省", 6.2), ("重庆市", 7.7), ("四川省", 7.9), ("贵州省", 8.9),
        ("云南省", 8.2), ("西藏自治区", 9.4), ("陕西省", 8.0), ("甘肃省", 9.2),
        ("青海省", 9.5), ("宁夏回族自治区", 8.6), ("新疆维吾尔自治区", 9.0),
        ("台湾省", 7.0), ("香港特别行政区", 7.8), ("澳门特别行政区", 7.4),
    ]
    rng = np.random.default_rng(11)
    df = pd.DataFrame(provinces, columns=["province", "rate"])
    df["rate"] = df["rate"] + rng.normal(0, 0.15, size=len(df))
    df["rate"] = df["rate"].round(2)
    df["sample_size"] = rng.integers(800, 8000, size=len(df))
    return df


def generate_yearly_trend() -> pd.DataFrame:
    """模拟近十年抑郁检出率趋势。"""
    years = list(range(2015, 2025))
    student = [12.1, 12.8, 13.4, 14.0, 14.9, 17.1, 18.6, 19.4, 20.2, 21.1]
    elderly = [22.5, 22.9, 23.4, 24.0, 24.5, 25.6, 26.4, 27.0, 27.5, 28.1]
    return pd.DataFrame({
        "年份": years,
        "大学生抑郁检出率_百分比": student,
        "中老年抑郁检出率_百分比": elderly,
    })


def main():
    student = generate_student_data(5000)
    elderly = generate_elderly_data(4000)
    regional = generate_regional_summary()
    trend = generate_yearly_trend()
    province = generate_province_summary()

    student.to_csv(DATA_DIR / "student_depression.csv", index=False, encoding="utf-8-sig")
    elderly.to_csv(DATA_DIR / "elderly_depression.csv", index=False, encoding="utf-8-sig")
    regional.to_csv(DATA_DIR / "tianjin_regional.csv", index=False, encoding="utf-8-sig")
    trend.to_csv(DATA_DIR / "yearly_trend.csv", index=False, encoding="utf-8-sig")
    province.to_csv(DATA_DIR / "china_province.csv", index=False, encoding="utf-8-sig")

    print(f"学生数据：{len(student)} 条 -> student_depression.csv")
    print(f"中老年数据：{len(elderly)} 条 -> elderly_depression.csv")
    print(f"天津区域数据：{len(regional)} 条 -> tianjin_regional.csv")
    print(f"全国省级：{len(province)} 条 -> china_province.csv")
    print(f"年度趋势：{len(trend)} 条 -> yearly_trend.csv")
    print("\n抑郁检出率（学生）：", student["是否抑郁"].mean())
    print("抑郁检出率（中老年）：", elderly["是否抑郁"].mean())


if __name__ == "__main__":
    main()
