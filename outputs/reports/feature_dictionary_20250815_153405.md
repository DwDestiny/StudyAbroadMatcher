# 特征字典

生成时间: 2025-08-15 15:34:05
数据集维度: (72395, 64)

## 特征分类总览

| 特征类别 | 特征数量 |
|----------|----------|
| 基础信息 | 5 |
| 教育背景 | 6 |
| 学术表现 | 6 |
| 语言能力 | 6 |
| 工作经验 | 8 |
| 院校层次 | 9 |
| 院校竞争 | 6 |
| 匹配评估 | 7 |
| 综合评估 | 3 |
| 时间特征 | 3 |
| 标准化字段 | 4 |

**总特征数**: 63

## 基础信息

**描述**: 申请的目标院校和专业基础信息

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 申请院校_院校ID | int64 | 0.0% | 目标院校的唯一标识 |
| 申请院校_专业ID | int64 | 0.0% | 目标专业的唯一标识 |
| 申请院校_院校名称 | object | 0.0% | 目标院校名称 |
| 申请院校_专业名称 | object | 0.0% | 目标专业名称 |
| 申请院校_课程类型 | object | 0.0% | 课程类型(Master/Bachelor等) |

## 教育背景

**描述**: 申请者的教育背景信息

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 教育经历_毕业院校 | object | 0.0% | 申请者毕业院校名称 |
| 教育经历_所学专业 | object | 0.0% | 申请者所学专业 |
| 教育经历_学历层次 | object | 0.0% | 申请者学历层次 |
| 教育经历_就读国家 | object | 0.0% | 申请者就读国家 |
| 教育经历_入学时间 | object | 0.0% | 入学日期 |
| 教育经历_毕业时间 | object | 0.1% | 毕业日期 |

## 学术表现

**描述**: 申请者的学术成绩和相对排名

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 教育经历_GPA成绩 | object | 1.3% | 原始GPA成绩 |
| 教育经历_GPA成绩_百分制 | float64 | 5.9% | 转换为百分制的GPA |
| 教育经历_GPA成绩_百分制_修复 | float64 | 5.8% | 修复后的百分制GPA |
| gpa_percentile | float64 | 5.8% | GPA在同类申请者中的百分位排名 |
| gpa_relative_rank | float64 | 5.8% | GPA相对排名(0-1) |
| academic_strength_score | float64 | 0.0% | 学术实力综合得分 |

## 语言能力

**描述**: 申请者的语言考试成绩

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 语言考试_考试类型 | object | 0.0% | 语言考试类型 |
| 语言考试_考试成绩 | object | 0.1% | 语言考试成绩 |
| 语言考试_考试时间 | object | 93.2% | 语言考试时间 |
| has_language_score | int64 | 0.0% | 是否有语言成绩 |
| language_test_type | object | 0.0% | 标准化语言考试类型 |
| language_score_normalized | float64 | 93.3% | 标准化语言成绩(0-100) |

## 工作经验

**描述**: 申请者的工作经验和相关性评分

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 工作经历_开始时间 | object | 88.2% | 待补充说明 |
| 工作经历_结束时间 | object | 88.3% | 待补充说明 |
| 工作经历_工作单位 | object | 0.0% | 待补充说明 |
| 工作经历_职位名称 | object | 0.0% | 待补充说明 |
| 工作经历_工作职责 | object | 91.7% | 待补充说明 |
| has_work_experience | int64 | 0.0% | 是否有工作经验 |
| work_experience_years | float64 | 0.0% | 工作经验年限 |
| work_relevance_score | float64 | 0.0% | 工作相关性评分(0-1) |

## 院校层次

**描述**: 申请者毕业院校和目标院校的层次分类

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| source_university_tier | int64 | 0.0% | 毕业院校层次等级 |
| source_university_tier_desc | object | 0.0% | 毕业院校层次描述 |
| source_is_985 | int64 | 0.0% | 是否985院校 |
| source_is_211 | int64 | 0.0% | 是否211院校 |
| source_is_double_first_class | int64 | 0.0% | 是否双一流院校 |
| source_university_tier_score | int64 | 0.0% | 毕业院校层次得分 |
| target_university_tier | int64 | 0.0% | 目标院校层次等级 |
| target_university_tier_desc | object | 0.0% | 目标院校层次描述 |
| target_university_tier_score | int64 | 0.0% | 目标院校层次得分 |

## 院校竞争

**描述**: 目标院校的竞争性和热门程度指标

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| target_university_qs_rank | int64 | 0.0% | 目标院校QS排名 |
| target_university_application_volume | int64 | 0.0% | 目标院校申请量 |
| target_university_avg_applicant_gpa | float64 | 0.0% | 目标院校平均申请者GPA |
| target_university_competitiveness | int64 | 0.0% | 目标院校竞争激烈程度 |
| target_university_competition | int64 | 0.0% | 目标院校竞争指数 |
| target_major_popularity | float64 | 0.0% | 目标专业热门程度 |

## 匹配评估

**描述**: 申请者与目标院校的匹配度评估

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| university_tier_gap | int64 | 0.0% | 院校层次差距 |
| university_score_gap | int64 | 0.0% | 院校得分差距 |
| university_matching_score | int64 | 0.0% | 院校匹配得分 |
| university_matching_level | object | 0.0% | 院校匹配等级 |
| competition_index | float64 | 0.0% | 竞争指数 |
| competition_level | object | 0.0% | 竞争等级 |
| competition_level_new | object | 0.0% | 新竞争等级 |

## 综合评估

**描述**: 申请者综合实力和成功概率评估

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| applicant_comprehensive_strength | float64 | 0.0% | 申请者综合实力得分 |
| estimated_success_probability | float64 | 0.0% | 预估成功概率 |
| success_probability_level | object | 0.0% | 成功概率等级 |

## 时间特征

**描述**: 申请时间相关的特征

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| application_year | int64 | 0.0% | 申请年份 |
| application_season | object | 0.0% | 申请季节 |
| time_to_graduation | float64 | 93.2% | 距离毕业时间(月) |

## 标准化字段

**描述**: 经过标准化处理的文本字段

| 字段名 | 数据类型 | 缺失率 | 说明 |
|--------|----------|--------|------|
| 教育经历_学历层次_标准化 | object | 0.0% | 标准化学历层次 |
| 申请院校_院校名称_标准化 | object | 0.0% | 标准化目标院校名称 |
| 申请院校_专业名称_标准化 | object | 0.0% | 标准化目标专业名称 |
| 教育经历_所学专业_标准化 | object | 0.0% | 标准化所学专业名称 |

