"""
抑郁风险预测模型训练
==================
- 学生群体：随机森林 + 逻辑回归（双模型对照）
- 中老年群体：随机森林 + 逻辑回归
- 输出：模型 .pkl，特征重要性，性能报告
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, roc_auc_score, classification_report,
                             confusion_matrix, precision_score, recall_score, f1_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)


STUDENT_FEATURES = [
    "年龄", "性别_女", "睡眠时长_小时", "每周运动次数",
    "学业压力", "经济压力", "亲密关系质量", "社会支持",
    "家族史", "童年不良经历", "慢性疾病", "吸烟", "饮酒",
    "日均屏幕时长_小时", "年级_大四", "年级_研究生"
]

ELDERLY_FEATURES = [
    "年龄", "性别_女", "教育年数", "是否独居", "收入_数值",
    "慢性病数量", "ADL生活自理能力", "睡眠时长_小时",
    "社会活动参与度", "子女月联系次数", "吸烟", "饮酒", "BMI",
    "城乡_农村"
]


def prepare_student(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["性别_女"] = (df["性别"] == "女").astype(int)
    df["年级_大四"] = (df["年级"] == "大四").astype(int)
    df["年级_研究生"] = (df["年级"] == "研究生").astype(int)
    X = df[STUDENT_FEATURES]
    y = df["是否抑郁"]
    return X, y


def prepare_elderly(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["性别_女"] = (df["性别"] == "女").astype(int)
    df["教育年数"] = df["教育程度"].map(
        {"未上学": 0, "小学": 6, "初中": 9, "高中": 12, "大专及以上": 15}
    )
    df["收入_数值"] = df["经济收入"].map({"低": 0, "中": 1, "高": 2})
    df["城乡_农村"] = (df["居住地区"] == "农村").astype(int)
    X = df[ELDERLY_FEATURES]
    y = df["是否抑郁"]
    return X, y


def train_one_group(X: pd.DataFrame, y: pd.Series, group: str) -> dict:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s = scaler.transform(X_test)

    rf = RandomForestClassifier(
        n_estimators=400, max_depth=10, min_samples_leaf=8,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    gb = GradientBoostingClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42
    )
    gb.fit(X_train, y_train)

    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr.fit(X_train_s, y_train)

    results = {}
    for name, model, X_eval in [
        ("随机森林", rf, X_test),
        ("梯度提升", gb, X_test),
        ("逻辑回归", lr, X_test_s),
    ]:
        y_pred = model.predict(X_eval)
        y_proba = model.predict_proba(X_eval)[:, 1]
        results[name] = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
            "auc": roc_auc_score(y_test, y_proba),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }

    importances = pd.DataFrame({
        "特征": X.columns,
        "随机森林重要性": rf.feature_importances_,
        "梯度提升重要性": gb.feature_importances_,
        "逻辑回归系数": lr.coef_[0],
    }).sort_values("随机森林重要性", ascending=False)

    joblib.dump(rf, MODEL_DIR / f"{group}_rf.pkl")
    joblib.dump(gb, MODEL_DIR / f"{group}_gb.pkl")
    joblib.dump(lr, MODEL_DIR / f"{group}_lr.pkl")
    joblib.dump(scaler, MODEL_DIR / f"{group}_scaler.pkl")
    joblib.dump(list(X.columns), MODEL_DIR / f"{group}_features.pkl")
    importances.to_csv(MODEL_DIR / f"{group}_importance.csv",
                       index=False, encoding="utf-8-sig")

    return {"metrics": results, "importance": importances, "n_test": len(y_test)}


def main():
    student_df = pd.read_csv(DATA_DIR / "student_depression.csv")
    elderly_df = pd.read_csv(DATA_DIR / "elderly_depression.csv")

    print("=" * 60)
    print("【学生群体模型】")
    print("=" * 60)
    Xs, ys = prepare_student(student_df)
    s_res = train_one_group(Xs, ys, "student")
    for name, m in s_res["metrics"].items():
        print(f"  {name:6s}  ACC={m['accuracy']:.3f}  AUC={m['auc']:.3f}  "
              f"Recall={m['recall']:.3f}  F1={m['f1']:.3f}")
    print("\n  Top 8 特征：")
    print(s_res["importance"].head(8).to_string(index=False))

    print("\n" + "=" * 60)
    print("【中老年群体模型】")
    print("=" * 60)
    Xe, ye = prepare_elderly(elderly_df)
    e_res = train_one_group(Xe, ye, "elderly")
    for name, m in e_res["metrics"].items():
        print(f"  {name:6s}  ACC={m['accuracy']:.3f}  AUC={m['auc']:.3f}  "
              f"Recall={m['recall']:.3f}  F1={m['f1']:.3f}")
    print("\n  Top 8 特征：")
    print(e_res["importance"].head(8).to_string(index=False))

    metrics_df = []
    for group, res in [("学生", s_res), ("中老年", e_res)]:
        for model_name, m in res["metrics"].items():
            metrics_df.append({
                "群体": group,
                "模型": model_name,
                "准确率": round(m["accuracy"], 4),
                "精确率": round(m["precision"], 4),
                "召回率": round(m["recall"], 4),
                "F1": round(m["f1"], 4),
                "AUC": round(m["auc"], 4),
            })
    pd.DataFrame(metrics_df).to_csv(MODEL_DIR / "model_metrics.csv",
                                    index=False, encoding="utf-8-sig")
    print(f"\n所有模型已保存到 {MODEL_DIR}")


if __name__ == "__main__":
    main()
