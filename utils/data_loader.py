"""数据与模型加载工具。"""

from pathlib import Path
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
REAL_DIR = DATA_DIR / "real"


@st.cache_data(show_spinner=False)
def load_nhanes_real() -> pd.DataFrame:
    """如果已下载真实 NHANES 数据，则返回；否则返回空表。"""
    p = REAL_DIR / "nhanes_phq9_processed.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_mendeley_real() -> pd.DataFrame:
    """Mendeley 学生 PHQ-9 真实数据（682 条）。"""
    p = REAL_DIR / "mendeley_phq9_processed.csv"
    if p.exists():
        return pd.read_csv(p)
    return pd.DataFrame()


def is_real_data_available() -> bool:
    return (REAL_DIR / "nhanes_phq9_processed.csv").exists() or \
           (REAL_DIR / "mendeley_phq9_processed.csv").exists()


def data_sources_summary() -> dict:
    """返回所有数据源摘要，供"数据来源透明化"组件使用。"""
    sources = []
    p = REAL_DIR / "nhanes_phq9_processed.csv"
    if p.exists():
        df = pd.read_csv(p)
        sources.append({
            "name": "NHANES 2017-2018",
            "type": "real",
            "country": "🇺🇸 美国",
            "n": len(df),
            "rate": float(df["是否抑郁"].mean() * 100),
            "publisher": "美国疾控中心 (CDC)",
            "url": "https://wwwn.cdc.gov/nchs/nhanes/",
            "note": "全国营养与健康调查，含完整 PHQ-9 量表",
        })
    p = REAL_DIR / "mendeley_phq9_processed.csv"
    if p.exists():
        df = pd.read_csv(p)
        sources.append({
            "name": "Mendeley 学生 PHQ-9 数据集",
            "type": "real",
            "country": "🌏 学生群体",
            "n": len(df),
            "rate": float(df["是否抑郁"].mean() * 100),
            "publisher": "Mendeley Data (kkzjk253cy)",
            "url": "https://data.mendeley.com/datasets/kkzjk253cy/6",
            "note": "学术公开 PHQ-9 完整问卷数据集",
        })
    # 仿真数据
    p = DATA_DIR / "student_depression.csv"
    if p.exists():
        df = pd.read_csv(p)
        sources.append({
            "name": "中国大学生仿真数据",
            "type": "simulated",
            "country": "🇨🇳 中国",
            "n": len(df),
            "rate": float(df["是否抑郁"].mean() * 100),
            "publisher": "基于 Gao L et al. (2020) Sci Rep Meta 分析参数生成",
            "url": "https://doi.org/10.1038/s41598-020-72998-1",
            "note": "依据已发表中国大学生抑郁流行病学分布构造",
        })
    p = DATA_DIR / "elderly_depression.csv"
    if p.exists():
        df = pd.read_csv(p)
        sources.append({
            "name": "中国中老年仿真数据",
            "type": "simulated",
            "country": "🇨🇳 中国",
            "n": len(df),
            "rate": float(df["是否抑郁"].mean() * 100),
            "publisher": "基于 CHARLS 文献分布参数生成",
            "url": "https://charls.pku.edu.cn/",
            "note": "参照 Lei et al. (2014) 与 CHARLS 量表设计",
        })
    return {"sources": sources, "total_real": sum(s["n"] for s in sources if s["type"] == "real"),
            "total_sim": sum(s["n"] for s in sources if s["type"] == "simulated")}


@st.cache_data(show_spinner=False)
def load_student_data() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "student_depression.csv")


@st.cache_data(show_spinner=False)
def load_elderly_data() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "elderly_depression.csv")


@st.cache_data(show_spinner=False)
def load_regional_data() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "tianjin_regional.csv")


@st.cache_data(show_spinner=False)
def load_trend_data() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "yearly_trend.csv")


@st.cache_data(show_spinner=False)
def load_metrics() -> pd.DataFrame:
    p = MODEL_DIR / "model_metrics.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_importance(group: str) -> pd.DataFrame:
    p = MODEL_DIR / f"{group}_importance.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_resource(show_spinner=False)
def load_model_bundle(group: str) -> dict:
    return {
        "rf": joblib.load(MODEL_DIR / f"{group}_rf.pkl"),
        "gb": joblib.load(MODEL_DIR / f"{group}_gb.pkl"),
        "lr": joblib.load(MODEL_DIR / f"{group}_lr.pkl"),
        "scaler": joblib.load(MODEL_DIR / f"{group}_scaler.pkl"),
        "features": joblib.load(MODEL_DIR / f"{group}_features.pkl"),
    }
