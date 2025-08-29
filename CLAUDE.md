# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于成功申请数据的学生-专业匹配度计算系统，服务于澳洲、英国留学的互联网平台。项目基于94,021条成功申请记录，通过路径聚类和相似度计算，为新学生提供精准的专业匹配度评估。

## 项目结构

```
定校数据支撑方案/
├── data/                    # 数据目录
│   ├── raw/                # 原始数据
│   │   └── 近3年offer数据_整理表头.csv
│   ├── processed/          # 处理后的数据
│   │   ├── final_feature_dataset_latest.csv          # 最终特征数据集
│   │   └── final_feature_dataset_with_major_matching_*.csv  # 完整特征数据集
│   ├── clustering_results/ # 聚类结果存储
│   ├── path_profiles/      # 路径画像数据
│   └── external/           # 外部数据源
├── src/                    # 源代码
│   ├── data_processing/    # 数据预处理模块
│   ├── feature_engineering/ # 特征工程模块
│   ├── matching_engine/    # 匹配度计算引擎（核心模块）
│   ├── analysis/           # 数据分析脚本
│   └── utils/              # 工具函数
├── dashboard/              # 数据看板
│   ├── index.html          # 数据分析看板
│   └── data.json          # 看板数据文件
├── config/                 # 配置文件
│   └── config.py           # 项目主配置文件
├── docs/                   # 文档
├── outputs/                # 输出结果
│   ├── reports/            # 分析报告
│   └── visualizations/     # 可视化图表
├── scripts/                # 核心脚本
│   ├── integrate_major_matching_features.py  # 特征集成
│   └── prepare_dashboard_data.py             # 看板数据准备
├── tests/                  # 测试代码
├── venv/                   # 虚拟环境
├── requirements.txt        # Python依赖包
└── CLAUDE.md              # 项目指导文档
```

## 核心数据概况

### **历史成功申请数据**
- **数据规模**：94,021条成功申请记录
- **院校覆盖**：486所院校（澳洲383所、英国38所、美国9所等）
- **专业覆盖**：7,113个不同专业
- **院校-专业组合**：10,170个独特组合
- **热门组合（≥10申请）**：1,229个，覆盖76.7%申请量

### **特征工程成果**
- **75维标准化特征向量**：包含院校背景、学术实力、专业匹配度、语言能力、工作经验等
- **专业匹配度系统**：7大类46子类专业分类，智能跨领域兼容性评估
- **院校评分体系**：中国985/211/双一流 + 海外QS排名统一评分
- **数据质量**：100%特征完整性，平均专业匹配度0.527，同领域申请52%

## 开发环境

- Python 3.13.1
- Windows 11 PowerShell环境
- 虚拟环境：venv

## 当前开发阶段

### **第一阶段：核心匹配算法实现**（✅ 已完成并优化）
1. ✅ **专业路径聚类分析** - 对申请量≥100的专业执行聚类，识别不同成功路径
2. ✅ **路径画像构建系统** - 为每个聚类路径构建详细的申请者画像  
3. ✅ **匹配度计算引擎** - 实现两阶段匹配（路径归属+相似度计算）

### **系统优化阶段**（✅ 已完成）
4. ✅ **数据质量优化** - 自动异常值检测，清洗75万+异常数据点
5. ✅ **匹配算法增强** - 鲁棒统计归一化，增强余弦相似度计算
6. ✅ **小样本处理** - 扩展支持357个专业（含30-99申请量专业）
7. ✅ **系统验证测试** - 抽取多元化样本，验证业务逻辑和性能指标

### **关键成果指标**
- **路径置信度提升**：1.2% → 88.1%（73倍改善）
- **匹配准确率提升**：43分 → 90分（+47分）
- **专业覆盖扩展**：50个 → 357个（7倍扩展）
- **数据质量改善**：自动清洗异常值，100%特征完整性
- **系统稳定性**：100%匹配成功率，生产级可靠性

### **第二阶段：生产级部署**（准备中）
8. 📋 完整系统验证报告编写
9. 📋 生产部署和后续优化建议制定
10. 📋 用户培训文档和API接口规范

### 常用命令

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# === 核心系统使用 ===
# 使用增强系统（推荐生产环境）
python -c "from src.matching_engine.enhanced_matching_system import EnhancedStudentMajorMatchingSystem; system = EnhancedStudentMajorMatchingSystem(); system.initialize_system()"

# === 数据处理和看板 ===
# 生成看板数据
python scripts/prepare_dashboard_data.py

# 集成专业匹配度特征
python scripts/integrate_major_matching_features.py

# === 验证和测试 ===
# 运行全面效果验证
python comprehensive_validation.py

# 测试匹配逻辑
python test_matching_logic.py

# 查看验证报告
ls validation_reports/
```

## 数据看板

项目包含一个交互式数据分析看板，位于 `dashboard/` 目录：

### 启动看板
```bash
# 方法1：使用Python内置服务器
cd dashboard
python -m http.server 8000

# 方法2：直接在浏览器中打开index.html文件
```

### 看板功能
1. **概览指标**：总申请量、热门院校/专业、平均GPA等关键数据
2. **核心画像分析**：
   - 院校/专业筛选器，支持多选
   - 申请者分布散点图（GPA vs 院校背景）
   - 能力维度雷达图（均值vs中位数对比）
3. **群体统计**：筛选后群体的关键指标展示
4. **辅助分析**：院校层次分布、专业TOP10、GPA分布图表

### 技术栈
- 单页HTML应用
- Bootstrap 5（样式框架）
- Chart.js（图表库）
- 原生JavaScript（交互逻辑）

## 匹配系统技术规格

### 核心算法逻辑
1. **数据基础**：基于94,021条成功申请记录，所有数据均为获得offer的成功案例
2. **聚类策略**：对申请量≥100的专业执行K-means聚类，识别不同成功路径
3. **匹配模式**：两阶段匹配（路径归属判断 + 加权余弦相似度计算）
4. **输出结果**：0-100分匹配度分数，表示新学生与某专业成功申请者的相似程度

### 第一阶段实现模块

#### 1. 专业路径聚类分析（clustering_analysis.py）
- 筛选申请量≥100的专业（预计300+个专业）
- 使用K-means算法进行聚类（k=2~5）
- 评估聚类效果，确定最优聚类数
- 输出聚类标签和中心点数据

#### 2. 路径画像构建系统（path_profile_builder.py）
- 为每个聚类路径构建详细画像（均值、标准差、分布特征）
- 计算路径代表性和覆盖度指标
- 生成路径标签和描述
- 输出结构化画像数据

#### 3. 匹配度计算引擎（matching_calculator.py）
- 实现路径归属判断算法
- 实现加权余弦相似度计算
- 集成特征权重调整机制
- 提供标准化的匹配度评分接口

## 开发约束

- 基于现有75维特征向量，不新增特征维度
- 保持与现有数据格式的兼容性
- 确保算法的可解释性和业务可理解性
- 每次策略调整需与用户确认后实施