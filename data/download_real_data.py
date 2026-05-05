"""
真实公开数据集下载与对接脚本
==========================
本脚本支持下载以下真实公开数据集，作为演示数据的替代或补充：

✅ 完全免登录、零门槛（脚本一键下载）：
   1. NHANES 2017-2018 PHQ-9 数据 — 美国 CDC 公开
   2. Mendeley PHQ-9 学生抑郁数据集 — 682 条学生 PHQ-9 完整问卷数据

⏳ 需要注册账号（更具科学价值，时间足时建议申请）：
   3. CHARLS（中国健康与养老追踪调查）— 北京大学，charls.pku.edu.cn
   4. CFPS（中国家庭追踪调查）— 北大开放研究数据平台
   5. Kaggle Student Depression（28k 印度学生）— kaggle.com

使用方法：
   python data/download_real_data.py --source nhanes --convert
   python data/download_real_data.py --source mendeley --convert
   python data/download_real_data.py --source all --convert
"""

import argparse
import json
import sys
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REAL_DIR = DATA_DIR / "real"
REAL_DIR.mkdir(exist_ok=True)


# ============================================================
# 选项 1：NHANES PHQ-9（美国 CDC 公开）
# ============================================================
NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles"
NHANES_FILES = {
    "DPQ_J.XPT": f"{NHANES_BASE}/DPQ_J.xpt",
    "DEMO_J.XPT": f"{NHANES_BASE}/DEMO_J.xpt",
    "SLQ_J.XPT": f"{NHANES_BASE}/SLQ_J.xpt",
    "PAQ_J.XPT": f"{NHANES_BASE}/PAQ_J.xpt",
    "ALQ_J.XPT": f"{NHANES_BASE}/ALQ_J.xpt",
    "SMQ_J.XPT": f"{NHANES_BASE}/SMQ_J.xpt",
    "MCQ_J.XPT": f"{NHANES_BASE}/MCQ_J.xpt",
}


def download_nhanes() -> Path:
    print("📥 下载 NHANES 2017-2018 公开数据 …")
    nhanes_dir = REAL_DIR / "nhanes_2017_2018"
    nhanes_dir.mkdir(exist_ok=True)
    for fname, url in NHANES_FILES.items():
        out = nhanes_dir / fname
        if out.exists():
            print(f"  ✓ {fname} 已存在，跳过")
            continue
        try:
            print(f"  ⏳ {fname}")
            urllib.request.urlretrieve(url, out)
            print(f"  ✅ {fname} ({out.stat().st_size // 1024} KB)")
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
    return nhanes_dir


def convert_nhanes_to_platform() -> None:
    try:
        import pandas as pd
    except ImportError:
        print("❌ 需要安装 pandas")
        return
    nhanes_dir = REAL_DIR / "nhanes_2017_2018"
    if not (nhanes_dir / "DPQ_J.XPT").exists():
        return
    print("🔄 转换 NHANES .XPT → 平台 CSV …")
    dpq = pd.read_sas(nhanes_dir / "DPQ_J.XPT")
    demo = pd.read_sas(nhanes_dir / "DEMO_J.XPT")
    slq = pd.read_sas(nhanes_dir / "SLQ_J.XPT")
    smq = pd.read_sas(nhanes_dir / "SMQ_J.XPT")
    alq = pd.read_sas(nhanes_dir / "ALQ_J.XPT")

    phq_items = [f"DPQ0{i}0" for i in range(1, 10)]
    df = dpq[["SEQN"] + phq_items].copy()
    for col in phq_items:
        df.loc[df[col].isin([7, 9, 77, 99]), col] = pd.NA
    df = df.dropna(subset=phq_items)
    df["PHQ9分数"] = df[phq_items].sum(axis=1).astype(int)
    df["是否抑郁"] = (df["PHQ9分数"] >= 10).astype(int)

    demo_cols = {"SEQN": "SEQN", "RIDAGEYR": "年龄",
                 "RIAGENDR": "性别", "DMDEDUC2": "教育程度"}
    demo = demo[list(demo_cols)].rename(columns=demo_cols)
    demo["性别"] = demo["性别"].map({1.0: "男", 2.0: "女"})
    df = df.merge(demo, on="SEQN", how="left")

    if "SLD012" in slq.columns:
        df = df.merge(slq[["SEQN", "SLD012"]].rename(
            columns={"SLD012": "睡眠时长_小时"}), on="SEQN", how="left")
    if "SMQ020" in smq.columns:
        df = df.merge(smq[["SEQN", "SMQ020"]], on="SEQN", how="left")
        df["吸烟"] = (df["SMQ020"] == 1).astype(int)
        df = df.drop(columns=["SMQ020"])
    if "ALQ121" in alq.columns:
        df = df.merge(alq[["SEQN", "ALQ121"]], on="SEQN", how="left")
        df["饮酒"] = ((df["ALQ121"] >= 1) & (df["ALQ121"] <= 7)).astype(int)
        df = df.drop(columns=["ALQ121"])

    df["抑郁分级"] = pd.cut(
        df["PHQ9分数"],
        bins=[-1, 4, 9, 14, 19, 27],
        labels=["无", "轻度", "中度", "中重度", "重度"],
    )
    df["数据来源"] = "NHANES 2017-2018 (美国 CDC 公开)"
    out_path = REAL_DIR / "nhanes_phq9_processed.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ {out_path.name}（{len(df)} 条 / 检出率 {df['是否抑郁'].mean()*100:.1f}%）")


# ============================================================
# 选项 2：Mendeley PHQ-9 学生抑郁数据集（学术公开，免登录）
# ============================================================
MENDELEY_DOWNLOAD = (
    "https://data.mendeley.com/public-files/datasets/kkzjk253cy/files/"
    "9cef8428-3ca8-41c8-93db-7bd4e8855add/file_downloaded"
)


def download_mendeley_phq9() -> None:
    print("📥 下载 Mendeley PHQ-9 学生抑郁数据集 …")
    out = REAL_DIR / "mendeley_phq9_students_raw.csv"
    # 兼容已经手动下载的文件名
    alt = REAL_DIR / "PHQ-9_Dataset_Mendeley.csv"
    if alt.exists() and not out.exists():
        out.write_bytes(alt.read_bytes())
        print(f"  ✓ 复用已有文件 {alt.name}")
        return
    if out.exists():
        print(f"  ✓ {out.name} 已存在，跳过")
        return
    try:
        # Mendeley 需要带 User-Agent 才能下载
        req = urllib.request.Request(
            MENDELEY_DOWNLOAD,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            out.write_bytes(resp.read())
        print(f"  ✅ {out.name} ({out.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"  ❌ 下载失败：{e}")
        print("  请手动从 https://data.mendeley.com/datasets/kkzjk253cy/6 下载")
        print(f"  并保存为 {out}")


def convert_mendeley_to_platform() -> None:
    try:
        import pandas as pd
    except ImportError:
        return
    src = REAL_DIR / "mendeley_phq9_students_raw.csv"
    if not src.exists():
        return
    print("🔄 转换 Mendeley → 平台 CSV …")
    df = pd.read_csv(src)
    # 答题选项映射到 0-3 分
    score_map = {
        "Not at all": 0, "Several days": 1,
        "More than half the days": 2, "Nearly every day": 3,
    }
    quality_map = {"Worst": 0, "Bad": 1, "Average": 2, "Good": 3, "Best": 4}

    phq_q_cols = [c for c in df.columns
                  if c not in ("Age", "Gender", "PHQ_Total", "PHQ_Severity",
                              "Sleep Quality", "Study Pressure", "Financial Pressure")]
    # 9 道 PHQ-9 题目（保持原始顺序）
    out = pd.DataFrame()
    out["年龄"] = df["Age"]
    out["性别"] = df["Gender"].map({"Male": "男", "Female": "女"})
    for i, c in enumerate(phq_q_cols, 1):
        out[f"PHQ9_Q{i}"] = df[c].map(score_map)
    out["PHQ9分数"] = df["PHQ_Total"]
    severity_map = {
        "Minimal": "无", "Mild": "轻度", "Moderate": "中度",
        "Moderately severe": "中重度", "Severe": "重度",
    }
    out["抑郁分级"] = df["PHQ_Severity"].map(severity_map)
    out["是否抑郁"] = (out["PHQ9分数"] >= 10).astype(int)
    out["睡眠质量"] = df["Sleep Quality"].map(quality_map)
    out["学业压力等级"] = df["Study Pressure"].map(
        {"Worst": 4, "Bad": 3, "Average": 2, "Good": 1, "Best": 0})
    out["经济压力等级"] = df["Financial Pressure"].map(
        {"Worst": 4, "Bad": 3, "Average": 2, "Good": 1, "Best": 0})
    out["数据来源"] = "Mendeley Data (kkzjk253cy) 学生 PHQ-9 公开数据集"

    out_path = REAL_DIR / "mendeley_phq9_processed.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    rate = out["是否抑郁"].mean() * 100
    print(f"✅ {out_path.name}（{len(out)} 条 / 检出率 {rate:.1f}%）")


# ============================================================
# 选项 3：Kaggle 数据集（28k 印度学生抑郁）
# ============================================================
def download_kaggle_student_depression() -> None:
    import subprocess
    print("📥 准备下载 Kaggle Student Depression Dataset …")
    print("  ⚠️  需要先：")
    print("    1. 注册 Kaggle  https://www.kaggle.com")
    print("    2. Settings → API → Create New Token，下载 kaggle.json")
    print("    3. 放置到 ~/.kaggle/kaggle.json")
    print("    4. pip install kaggle")
    out_dir = REAL_DIR / "kaggle_student_depression"
    out_dir.mkdir(exist_ok=True)
    try:
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", "hopesb/student-depression-dataset",
             "-p", str(out_dir), "--unzip"],
            check=True,
        )
        print(f"  ✅ 下载完成 → {out_dir}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ❌ 自动下载失败：{e}")
        print(f"  请手动从 https://www.kaggle.com/datasets/hopesb/student-depression-dataset 下载")


# ============================================================
# 主入口
# ============================================================
def main():
    p = argparse.ArgumentParser(description="真实公开数据集下载工具")
    p.add_argument("--source", choices=["nhanes", "mendeley", "kaggle", "all"],
                   default="all", help="数据源")
    p.add_argument("--convert", action="store_true",
                   help="下载完成后立即转换为平台兼容 CSV")
    args = p.parse_args()

    if args.source in ("nhanes", "all"):
        download_nhanes()
        if args.convert or args.source == "all":
            convert_nhanes_to_platform()
        print()
    if args.source in ("mendeley", "all"):
        download_mendeley_phq9()
        if args.convert or args.source == "all":
            convert_mendeley_to_platform()
        print()
    if args.source in ("kaggle", "all"):
        download_kaggle_student_depression()

    print("\n========================================")
    print("✅ 完成。所有真实数据已保存到 data/real/")
    print("   平台启动后会自动检测并接入这些数据。")
    print("========================================")


if __name__ == "__main__":
    main()
