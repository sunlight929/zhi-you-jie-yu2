"""关于项目：技术栈、数据来源、团队介绍、参考文献。"""

import streamlit as st

from utils.test_mode import redirect_if_test_mode_non_assessment

st.set_page_config(page_title="关于项目 | 知忧·解郁", page_icon="📚", layout="wide")

# 测试模式：自动跳转评估页（完整版下零影响）
redirect_if_test_mode_non_assessment()

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1100px;}
h2, h3 {color: #5BC8FF !important;}
code {color: #FBA94C !important; background: rgba(91,200,255,0.1) !important;}
table {background: rgba(91,127,255,0.04) !important;}
table th {background: rgba(91,200,255,0.15) !important; color: #5BC8FF !important;}
</style>
""", unsafe_allow_html=True)

st.title("📚 关于项目")
st.caption("项目背景、技术架构、AI 工具使用、参考文献与团队")

st.markdown("""
## 🌟 项目背景

抑郁症已成为全球第二大致残原因，**WHO 预计 2030 年将位居疾病负担之首**。
我国流行病学数据显示：
- 大学生抑郁检出率约 **20-30%**（Gao L et al., 2020，*Scientific Reports*，DOI: 10.1038/s41598-020-72998-1）
- 中老年（≥45 岁）抑郁症状检出率约 **15-30%**（CHARLS 历年调查数据）

然而精神卫生资源**长期短缺**且**分布不均**：截至 2022 年，我国精神科医师密度仅约 **3.4 / 10 万人**，
远低于发达国家平均水平。**早期识别、分层干预、资源精准投放**成为公共卫生体系建设的核心议题。

本平台基于这一现实需求，整合多源公开数据，构建面向大学生与中老年两大重点人群的
**抑郁风险大数据分析与早期识别决策支持系统**。

---

## 🧱 系统架构
""")

st.code("""
┌─────────────────────────────────────────────────────────────┐
│                    用户层                                    │
│  ├─ 个人用户：自评工具 + 个性化建议                         │
│  ├─ 学校 / 社区心理工作者：群体筛查 + 风险分层               │
│  └─ 公共卫生决策者：区域可视化 + 资源配置建议                │
├─────────────────────────────────────────────────────────────┤
│                    应用层 (Streamlit)                        │
│  ├─ 数据全景大屏      ├─ 风险因素分析                        │
│  ├─ 智能评估工具      └─ 区域决策支持                        │
├─────────────────────────────────────────────────────────────┤
│                    模型层 (scikit-learn)                     │
│  ├─ Random Forest    ├─ Gradient Boosting                    │
│  ├─ Logistic Regr.   └─ 集成 + 可解释性                      │
├─────────────────────────────────────────────────────────────┤
│                    数据层                                    │
│  ├─ 学生群体仿真数据 (5000 条)                               │
│  ├─ 中老年仿真数据   (4000 条)                               │
│  ├─ 天津 16 区县区域数据                                     │
│  └─ 近 10 年趋势数据                                         │
└─────────────────────────────────────────────────────────────┘
""", language="text")


st.markdown("""
---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|---|---|---|
| 数据处理 | Pandas, NumPy | 数据清洗、特征工程 |
| 机器学习 | scikit-learn | RF + GBDT + LR 三模型集成 |
| 可解释性 | LR 系数 × 标准化特征 | 轻量化局部贡献分解 |
| 可视化 | Plotly, ECharts | 交互式图表 + 大屏组件 |
| Web 框架 | Streamlit | 多页面应用快速开发 |
| 部署 | Streamlit Cloud / Docker | Web 端一键部署 |

---

## 🤖 AI 工具协作策略

依据大赛规定的 **15 款合规 AI 工具清单**，本团队采用"任务-工具"匹配策略：

| 任务 | 主用工具 | 辅用工具 | 应用方式 |
|---|---|---|---|
| 代码生成 | DeepSeek | 通义灵码 | 数据预处理与可视化代码 |
| 文档撰写 | Kimi | 智谱 AI | 研究报告结构化撰写 |
| 数据分析探索 | 通义千问 | DeepSeek | EDA 思路与统计方法选型 |
| 量表设计 | 智谱 AI | Kimi | PHQ-9 题项中文表达优化 |
| 演示素材 | 即梦 / 豆包 | 稿定设计 | 项目封面图与演示动画 |

> 评审重点关注**作者对 AI 工具的驾驭能力**，本项目所有 AI 输出经团队成员**人工核验、修订与整合**，
> 确保医学专业表达准确、统计方法严谨、代码可复现。

---

## 📚 数据来源与参考文献

### 数据集（真实部署可接入）
- **CHARLS（中国健康与养老追踪调查）**：北京大学国家发展研究院主持，含 CES-D 抑郁量表数据
- **NHANES（美国国家健康与营养调查）**：含 PHQ-9 量表数据
- **CFPS（中国家庭追踪调查）**：北京大学中国社会科学调查中心
- **Kaggle - Student Mental Health 系列**：多个大学生心理健康公开数据集

### 量表
- **PHQ-9（Patient Health Questionnaire-9）**：抑郁症筛查金标准之一，9 项条目，0-27 分
- **CES-D（Center for Epidemiologic Studies Depression Scale）**：流行病学常用，CHARLS 采用 10 项简版

### 关键参考文献
1. Lei X, Sun X, Strauss J, Zhang P, Zhao Y. *Depressive symptoms and SES among the mid-aged and elderly in China.* **Soc Sci Med**. 2014;120:224-32.
2. Gao L, Xie Y, Jia C, Wang W. *Prevalence of depression among Chinese university students: a systematic review and meta-analysis.* **Scientific Reports**. 2020;10:15897. (DOI: 10.1038/s41598-020-72998-1)
3. Lu J, et al. *Prevalence of depressive disorders and treatment in China: a cross-sectional epidemiological study.* **Lancet Psychiatry**. 2021;8(11):981-990.
4. Kroenke K, et al. *The PHQ-9: validity of a brief depression severity measure.* **J Gen Intern Med**. 2001;16(9):606-13.
5. WHO. *Depression and Other Common Mental Disorders: Global Health Estimates.* 2017.
6. 中华医学会精神医学分会. **抑郁障碍防治指南（第二版）**. 2015.

---

## ⚖️ 数据合规与伦理

- 本平台演示阶段使用基于**已发表流行病学研究分布参数**生成的合成数据，**不包含任何真实个体信息**
- 真实数据接入必须经过**伦理审查**与**数据脱敏**
- 严格遵守《数据安全法》《个人信息保护法》《医疗卫生机构网络安全管理办法》
- 平台输出仅作辅助参考，**不替代临床医师诊断**
- 数据来源与处理流程在 `/report/研究报告.md` 中完整说明

---

## 👥 团队介绍

### 学生作者
**天津大学医学院 · 临床医学专业 · 本科生**

| 角色 | 主要职责 |
|---|---|
| 队长 | 选题立项、医学专业表达、量表选型、研究报告撰写、模型训练、Web 平台开发 |
| 队员 | 临床场景分析、风险因素解读、天津本地化策略、文档与演示 |

### 指导教师（双导师 · 医工交叉）

- **张小臣 副研究员**　天津大学医学院
  - 负责医学专业方向指导（量表合规性、临床建议合规性）

- **张淑芳 副教授**　天津大学电气自动化与信息工程学院
  - 负责 AI 技术与 Web 平台架构方向指导

依托双导师的医工交叉指导，确保项目在临床合规性与技术实现上均符合规范。

---

## 🔗 项目链接

- 📦 **本地运行**：`streamlit run app.py`
- 📄 **研究报告**：见 `report/研究报告.md`
- 📘 **用户手册**：见 `docs/用户手册.md`
- ⚙️ **技术文档**：见 `docs/技术文档.md`

---

## 💌 致谢

感谢中国大学生计算机设计大赛组委会提供的赛事平台，
感谢指导教师对本项目医学专业方向的把关，
感谢公开数据集（CHARLS、NHANES 等）背后的科研机构与数据贡献者，
感谢所有为精神卫生事业默默耕耘的医生、心理工作者与患者家属。

> "每一个数据点背后都是一个真实的人。愿我们能用数据的力量，让被忧愁笼罩的人，看见一束光。"
""")
