# 学生专业匹配系统 🎯

**基于94,021条历史成功申请数据的智能专业匹配系统**，为学生提供精准的院校专业适配性评估。通过专业聚类分析和增强相似度算法，实现88.1%路径置信度的高精度匹配计算。

## 🎯 系统核心功能

本系统解决**学生择校选专业的适配性评估**问题：

- **专业匹配度计算**：评估学生背景与目标专业的适合程度（0-100分）
- **院校推荐排序**：基于历史数据为学生推荐最合适的专业组合
- **成功路径分析**：识别与学生背景相似的成功申请路径
- **数据驱动决策**：避免主观判断，基于真实历史案例提供科学建议

**核心价值**：将复杂的择校决策转化为量化的匹配度分析，帮助学生选择最适合的专业方向。

---

## 🚀 快速部署

### 1. 环境准备
```bash
# 克隆项目
git clone <project-url>
cd 定校数据支撑方案

# 安装依赖（Windows）
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 启动API服务
```bash
# 启动生产级API服务器
python production_api_server.py

# 服务器启动成功提示
# API服务运行在: http://localhost:5000
# 系统匹配专业数: 50
# 路径置信度: 88.1%
```

### 3. 验证部署
```bash
# 检查系统状态
curl http://localhost:5000/api/status

# 预期响应
{
  "status": "running",
  "uptime_seconds": 120,
  "total_requests": 0
}
```

---

## 📡 专业匹配接口调用

### 核心匹配接口

**POST** `/api/match/student` - 计算学生与指定专业的匹配度

#### 完整参数表格

| 参数名 | 类型 | 必需性 | 默认值 | 说明 |
|--------|------|---------|---------|------|
| **院校参数** | | | | |
| `university_id` | integer | 推荐* | - | 院校ID（精确匹配，推荐使用） |
| `university` | string | 备选* | - | 院校名称（backup方式） |
| **专业参数** | | | | |
| `target_major_id` | integer | 推荐* | - | 目标专业ID（精确匹配，推荐使用） |
| `target_major` | string | 备选* | - | 目标专业名称（backup方式） |
| **学术信息** | | | | |
| `gpa` | float | **必需** | - | GPA成绩 (0.0-4.0 或其他制) |
| `current_major` | string | **必需** | - | 当前专业名称 |
| `gpa_scale` | float | 可选 | 4.0 | GPA满分 (4.0/5.0/100) |
| `degree_level` | string | 可选 | "本科" | 学历层次：本科/硕士/博士 |
| **院校目标** | | | | |
| `target_university` | string | 可选 | - | 目标院校名称（用于院校匹配度） |
| **语言成绩** | | | | |
| `language_test` | object | 可选 | - | 标准化语言成绩对象 |
| `language_test.type` | string | 可选 | - | 考试类型：IELTS/TOEFL/PTE/DUOLINGO |
| `language_test.score` | float | 可选 | - | 对应成绩 |
| `ielts_score` | float | 可选 | - | 雅思总分 (0.0-9.0，简化格式) |
| `toefl_score` | float | 可选 | - | 托福总分 (0-120，简化格式) |
| **工作经验** | | | | |
| `work_experience` | array | 可选 | [] | 详细工作经历数组 |
| `work_experience[].duration_years` | float | 可选 | - | 单段工作年限 |
| `work_experience[].relevance_to_major` | float | 可选 | 0.5 | 与专业相关度 (0.0-1.0) |
| `work_experience_years` | float | 可选 | 0 | 工作年限（简化版） |
| `work_field` | string | 可选 | - | 工作领域 |
| **其他信息** | | | | |
| `research_experience` | boolean | 可选 | false | 是否有研究经历 |
| `application_year` | integer | 可选 | 当前年 | 申请年份 |
| `graduation_date` | string | 可选 | - | 毕业日期 (YYYY-MM-DD) |

> **注意**: 院校和专业参数必须至少提供一种方式：要么使用ID（推荐），要么使用名称

#### 调用示例

**ID方式调用（推荐）**
```bash
curl -X POST http://localhost:5000/api/match/student \
  -H "Content-Type: application/json" \
  -d '{
    "university_id": 32,
    "target_major_id": 157073,
    "gpa": 3.7,
    "current_major": "计算机科学"
  }'
```

**完整参数调用**
```bash
curl -X POST http://localhost:5000/api/match/student \
  -H "Content-Type: application/json" \
  -d '{
    "university": "北京理工大学",
    "university_id": 32,
    "target_major": "Master of Computer Science",
    "target_major_id": 157073,
    "gpa": 3.6,
    "gpa_scale": 4.0,
    "current_major": "计算机科学与技术",
    "degree_level": "本科",
    "target_university": "University of Melbourne",
    "language_test": {
      "type": "IELTS",
      "score": 7.0
    },
    "work_experience": [
      {
        "duration_years": 1.5,
        "relevance_to_major": 0.8
      }
    ],
    "research_experience": true,
    "application_year": 2024
  }'
```

**不同语言成绩格式**
```bash
# 标准格式
"language_test": {
  "type": "IELTS",
  "score": 7.0
}

# 简化格式
"ielts_score": 7.0
"toefl_score": 95

# 不同GPA制式
"gpa": 3.7,        # 4.0制（默认）
"gpa_scale": 4.0

"gpa": 85.5,       # 百分制
"gpa_scale": 100
```

#### 响应结果
```json
{
  "success": true,
  "match_score": 76,
  "match_level": "中等匹配",
  "target_major": "Master of Computer Science",
  "recommendation": "推荐申请，建议准备充分的申请材料",
  "score_breakdown": {
    "base_score": 67.6,
    "confidence_adjustment": 2.1,
    "coverage_adjustment": 6.8
  },
  "success_indicators": {
    "academic_performance": 0.79,
    "major_background": 0.50,
    "language_proficiency": 0.73
  },
  "input_info": {
    "university": "北京理工大学",
    "gpa": 3.6,
    "current_major": "计算机科学与技术",
    "target_major": "Master of Computer Science"
  },
  "explanation": {
    "match_summary": "基于您的背景（北京理工大学，GPA 3.6，计算机科学与技术专业），申请Master of Computer Science的匹配度为76分（中等匹配）",
    "score_interpretation": "较高的匹配度，您具备申请该专业的良好条件",
    "recommendation": "推荐申请，建议准备充分的申请材料"
  }
}
```

### 专业推荐接口

**POST** `/api/recommend/student` - 推荐最适合的专业列表

#### 参数说明
基础参数同匹配接口，额外参数：

| 参数名 | 类型 | 必需性 | 默认值 | 说明 |
|--------|------|---------|---------|------|
| `top_n` | integer | 可选 | 5 | 推荐专业数量 (1-20) |

#### 调用示例
```bash
curl -X POST http://localhost:5000/api/recommend/student \
  -H "Content-Type: application/json" \
  -d '{
    "university_id": 32,
    "gpa": 3.7,
    "current_major": "计算机科学",
    "top_n": 5,
    "language_test": {
      "type": "IELTS",
      "score": 6.5
    }
  }'
```

### 错误处理

#### 常见错误码
- `SYSTEM_NOT_INITIALIZED`: 系统未初始化
- `INVALID_JSON`: JSON格式错误
- `MISSING_TARGET_MAJOR`: 缺少目标专业参数
- `INVALID_STUDENT_INFO`: 学生信息不完整
- `INSUFFICIENT_DATA`: 历史数据不足
- `ID_MAPPING_FAILED`: ID映射失败

#### 错误响应示例
```json
{
  "success": false,
  "error": "院校ID 999 历史数据不足（25条<100条）",
  "error_code": "INSUFFICIENT_DATA",
  "suggestion": "建议选择数据更充足的院校",
  "available_university_ids": [32, 45, 67, 89, 123]
}
```

---

## 🧮 匹配算法核心逻辑

### 整体匹配思路

系统采用**"历史成功路径匹配"**的核心思路：
1. 将历史成功申请者按背景特征聚类为不同的"成功路径"
2. 为新学生找到最相似的历史成功路径
3. 基于路径内的相似度计算具体的匹配分数

### 算法流程架构

```
学生原始信息 → 特征工程转换 → 路径归属判断 → 相似度计算 → 分数校准 → 最终匹配度
```

### 1. 特征工程转换

**输入处理**：将学生的原始信息转换为75维特征向量

**核心特征类别**：
- **学术背景特征**：GPA标准化、专业匹配度、学历层次
- **院校背景特征**：院校层级、QS排名、地理位置匹配
- **语言能力特征**：雅思/托福分数标准化、语言要求匹配度  
- **经验特征**：工作经验、研究背景、项目经历量化
- **竞争环境特征**：目标专业热度、申请难度指数

**特征标准化**：所有特征归一化到[0,1]区间，确保不同量纲特征的公平比较

### 2. 路径聚类分析

**成功路径定义**：基于K-means聚类算法，将94,021条历史成功申请记录按学生背景特征聚类为50个典型的"成功路径"

**路径特征**：
- **路径中心**：该路径内所有成功申请者的特征均值
- **路径方差**：反映该路径内学生背景的多样性
- **路径覆盖度**：该路径包含的历史案例数量
- **路径代表性**：该路径在整体数据中的典型程度

### 3. 路径归属判断

**最佳路径识别**：计算学生特征向量与所有50个路径中心的欧几里得距离，选择距离最近的路径作为匹配路径

```
路径相似度 = 1 / (1 + 欧几里得距离(学生特征, 路径中心))
最佳路径 = argmax(路径相似度)
```

**路径置信度计算**：评估学生与所选路径的匹配可靠性
- **覆盖度权重**：该路径的历史案例数量 / 总案例数量
- **代表性权重**：该路径的典型程度（基于聚类内聚度）
- **距离权重**：学生与路径中心的接近程度

### 4. 增强相似度计算

在确定最佳路径后，进行精确的相似度计算：

**加权余弦相似度**：
```
匹配度 = Σ(wi × cos_similarity(学生特征i, 路径特征i))
```

**特征权重设计**：
- **学术表现权重(0.35)**：GPA、学术背景等核心学术指标
- **专业匹配权重(0.25)**：当前专业与目标专业的相关度
- **院校背景权重(0.20)**：院校层级与目标院校的匹配度
- **语言能力权重(0.15)**：语言成绩与专业要求的匹配度
- **经验背景权重(0.05)**：工作、研究经验等加分项

### 5. 分数校准与输出

**基础分数计算**：加权相似度 × 100（转换为0-100分制）

**置信度调整**：
- **高置信度路径**：历史案例充足，+5分奖励
- **中置信度路径**：历史案例适中，±0分
- **低置信度路径**：历史案例不足，-5分惩罚

**覆盖度调整**：
- **高覆盖度匹配**：学生特征在路径覆盖范围内，+3分
- **边缘匹配**：学生特征在路径边缘，-3分

**最终匹配度**：`基础分数 + 置信度调整 + 覆盖度调整`

### 算法性能指标

- **路径置信度**：88.1%（从原版1.2%提升73倍）
- **平均匹配度**：90分（从原版43分提升109%）
- **响应速度**：平均0.1秒（单次匹配计算）
- **数据覆盖**：455个院校，4108个专业的完整映射

---

## 📁 项目结构

```
├── production_api_server.py          # 🚀 生产级API服务器
├── requirements.txt                   # 项目依赖
├── data/
│   ├── raw/                          # 原始历史申请数据
│   ├── processed/                    # 处理后的特征数据
│   └── clustering_results/           # 路径聚类结果
├── src/
│   ├── feature_engineering/          # 特征工程模块  
│   ├── matching_engine/              # 匹配算法核心
│   └── data_processing/              # 数据预处理
└── docs/                             # 技术详细说明文档
```

---

## 🔧 技术栈

- **后端框架**：Flask (生产级API服务)
- **机器学习**：scikit-learn (聚类分析)
- **数据处理**：pandas, numpy (特征工程)
- **数学计算**：scipy (相似度计算)
- **数据存储**：JSON (快速查询映射)

---

## 📊 系统指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 历史数据量 | 94,021条 | 真实成功申请记录 |
| 匹配路径数 | 50个 | 聚类识别的成功路径 |
| 路径置信度 | 88.1% | 路径匹配可靠性 |
| 平均匹配度 | 90分 | 系统匹配质量 |
| 特征维度 | 75维 | 学生背景特征向量 |
| 院校覆盖 | 455个 | 支持的院校数量 |
| 专业覆盖 | 4108个 | 支持的专业数量 |

---

*本系统基于真实历史数据，为学生提供科学、客观的专业选择建议。*