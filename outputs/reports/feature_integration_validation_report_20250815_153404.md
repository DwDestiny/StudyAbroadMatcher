# 特征整合和验证报告

生成时间: 2025-08-15 15:34:05

## 1. 数据基本信息

- 总记录数: 72,395
- 总特征数: 64
- 内存使用: 162.24 MB
- 重复记录数: 0

## 2. 特征分类字典

### 基础信息

**描述**: 申请的目标院校和专业基础信息

**包含字段**:
- 申请院校_院校ID (缺失: 0.0%)
- 申请院校_专业ID (缺失: 0.0%)
- 申请院校_院校名称 (缺失: 0.0%)
- 申请院校_专业名称 (缺失: 0.0%)
- 申请院校_课程类型 (缺失: 0.0%)

### 教育背景

**描述**: 申请者的教育背景信息

**包含字段**:
- 教育经历_毕业院校 (缺失: 0.0%)
- 教育经历_所学专业 (缺失: 0.0%)
- 教育经历_学历层次 (缺失: 0.0%)
- 教育经历_就读国家 (缺失: 0.0%)
- 教育经历_入学时间 (缺失: 0.0%)
- 教育经历_毕业时间 (缺失: 0.1%)

### 学术表现

**描述**: 申请者的学术成绩和相对排名

**包含字段**:
- 教育经历_GPA成绩 (缺失: 1.3%)
- 教育经历_GPA成绩_百分制 (缺失: 5.9%)
- 教育经历_GPA成绩_百分制_修复 (缺失: 5.8%)
- gpa_percentile (缺失: 5.8%)
- gpa_relative_rank (缺失: 5.8%)
- academic_strength_score (缺失: 0.0%)

### 语言能力

**描述**: 申请者的语言考试成绩

**包含字段**:
- 语言考试_考试类型 (缺失: 0.0%)
- 语言考试_考试成绩 (缺失: 0.1%)
- 语言考试_考试时间 (缺失: 93.2%)
- has_language_score (缺失: 0.0%)
- language_test_type (缺失: 0.0%)
- language_score_normalized (缺失: 93.3%)

### 工作经验

**描述**: 申请者的工作经验和相关性评分

**包含字段**:
- 工作经历_开始时间 (缺失: 88.2%)
- 工作经历_结束时间 (缺失: 88.3%)
- 工作经历_工作单位 (缺失: 0.0%)
- 工作经历_职位名称 (缺失: 0.0%)
- 工作经历_工作职责 (缺失: 91.7%)
- has_work_experience (缺失: 0.0%)
- work_experience_years (缺失: 0.0%)
- work_relevance_score (缺失: 0.0%)

### 院校层次

**描述**: 申请者毕业院校和目标院校的层次分类

**包含字段**:
- source_university_tier (缺失: 0.0%)
- source_university_tier_desc (缺失: 0.0%)
- source_is_985 (缺失: 0.0%)
- source_is_211 (缺失: 0.0%)
- source_is_double_first_class (缺失: 0.0%)
- source_university_tier_score (缺失: 0.0%)
- target_university_tier (缺失: 0.0%)
- target_university_tier_desc (缺失: 0.0%)
- target_university_tier_score (缺失: 0.0%)

### 院校竞争

**描述**: 目标院校的竞争性和热门程度指标

**包含字段**:
- target_university_qs_rank (缺失: 0.0%)
- target_university_application_volume (缺失: 0.0%)
- target_university_avg_applicant_gpa (缺失: 0.0%)
- target_university_competitiveness (缺失: 0.0%)
- target_university_competition (缺失: 0.0%)
- target_major_popularity (缺失: 0.0%)

### 匹配评估

**描述**: 申请者与目标院校的匹配度评估

**包含字段**:
- university_tier_gap (缺失: 0.0%)
- university_score_gap (缺失: 0.0%)
- university_matching_score (缺失: 0.0%)
- university_matching_level (缺失: 0.0%)
- competition_index (缺失: 0.0%)
- competition_level (缺失: 0.0%)
- competition_level_new (缺失: 0.0%)

### 综合评估

**描述**: 申请者综合实力和成功概率评估

**包含字段**:
- applicant_comprehensive_strength (缺失: 0.0%)
- estimated_success_probability (缺失: 0.0%)
- success_probability_level (缺失: 0.0%)

### 时间特征

**描述**: 申请时间相关的特征

**包含字段**:
- application_year (缺失: 0.0%)
- application_season (缺失: 0.0%)
- time_to_graduation (缺失: 93.2%)

### 标准化字段

**描述**: 经过标准化处理的文本字段

**包含字段**:
- 教育经历_学历层次_标准化 (缺失: 0.0%)
- 申请院校_院校名称_标准化 (缺失: 0.0%)
- 申请院校_专业名称_标准化 (缺失: 0.0%)
- 教育经历_所学专业_标准化 (缺失: 0.0%)

## 3. 数据质量评估

### 3.1 缺失值分析

缺失值最多的前20个字段:

| 字段名 | 缺失数量 | 缺失百分比 |
|--------|----------|------------|
| language_score_normalized | 67,544.0 | 93.30% |
| time_to_graduation | 67,466.0 | 93.19% |
| 语言考试_考试时间 | 67,453.0 | 93.17% |
| 工作经历_工作职责 | 66,374.0 | 91.68% |
| 工作经历_结束时间 | 63,927.0 | 88.30% |
| 工作经历_开始时间 | 63,818.0 | 88.15% |
| 教育经历_GPA成绩_百分制 | 4,270.0 | 5.90% |
| 教育经历_GPA成绩_百分制_修复 | 4,221.0 | 5.83% |
| gpa_relative_rank | 4,221.0 | 5.83% |
| gpa_percentile | 4,221.0 | 5.83% |
| 教育经历_GPA成绩 | 947.0 | 1.31% |
| 教育经历_毕业时间 | 106.0 | 0.15% |
| 语言考试_考试成绩 | 49.0 | 0.07% |
| target_university_avg_applicant_gpa | 22.0 | 0.03% |
| 教育经历_就读国家 | 2.0 | 0.00% |

### 3.2 关键特征完整性

| 特征 | 完整性 |
|------|--------|
| 申请院校_院校名称 | 100.0% |
| 申请院校_专业名称 | 100.0% |
| 教育经历_毕业院校 | 100.0% |
| 教育经历_所学专业 | 100.0% |

### 3.3 数据类型分布

| 数据类型 | 字段数量 |
|----------|----------|
| object | 31 |
| int64 | 19 |
| float64 | 14 |

## 4. 数值特征范围验证

| 特征 | 预期范围 | 实际范围 | 状态 | 异常值数量 |
|------|----------|----------|------|------------|
| gpa_percentile | [0, 100] | [0.00, 100.00] | ✅ | 0 |
| gpa_relative_rank | [0, 1] | [0.00, 1.00] | ✅ | 0 |
| academic_strength_score | [0, 100] | [28.00, 95.50] | ✅ | 0 |
| language_score_normalized | [0, 100] | [0.00, 100.00] | ✅ | 0 |
| work_experience_years | [0, 50] | [0.00, 18.10] | ✅ | 0 |
| work_relevance_score | [0, 1] | [0.00, 0.67] | ✅ | 0 |
| target_university_tier_score | [0, 100] | [65.00, 100.00] | ✅ | 0 |
| university_matching_score | [0, 100] | [30.00, 100.00] | ✅ | 0 |
| competition_index | [0, 10] | [4.83, 9.18] | ✅ | 0 |
| applicant_comprehensive_strength | [0, 100] | [35.50, 93.00] | ✅ | 0 |
| estimated_success_probability | [0, 100] | [5.00, 95.00] | ✅ | 0 |
| application_year | [2020, 2025] | [2000.00, 2026.00] | ❌ | 14 |

## 5. 分类特征验证

### 教育经历_学历层次_标准化

- 预期类别数: 5
- 实际类别数: 45
- ❌ 未预期的值: ['高中', 'other', 'Diploma', 'High School', 'Undergraduate/Bachelor', 'Bachelor of arts', 'UNDERGRADUATE COURSE', 'Bachelor of Arts', 'postgraduate', 'bachelor degree', 'Bachelor degree', 'bachlor', 'Bachelor of Laws', 'senior high school', 'bachelor', 'Bachelor’s Degree', 'Bachelor’s degree', '预科', 'Undergraduate course', "BACHELOR'S", 'Bachelor of Commerce', 'BSc', "Bachelor's degree", '大专', 'BA', 'Bachelor of Engineering', 'undergraduate course', '学士', 'High school', 'Bachelor’s Degree of Law', 'Regular college course', 'Full-time undergraduate', "Bachelor's Degree", 'Master’s Degree', 'Msc.', "bachelor's degree program", "bachelor's degree", 'Bachelor of Accounting', 'high school', 'Secondary School']

**值分布**:
- 本科: 62,933 (86.9%)
- 硕士: 4,267 (5.9%)
- 高中: 2,062 (2.8%)
- 其他: 1,616 (2.2%)
- 专科: 1,341 (1.9%)
- 博士: 19 (0.0%)
- BSc: 15 (0.0%)
- bachelor: 12 (0.0%)
- Bachelor of Arts: 12 (0.0%)
- bachelor degree: 10 (0.0%)
- Undergraduate/Bachelor: 9 (0.0%)
- Bachelor’s Degree: 8 (0.0%)
- Bachelor degree: 7 (0.0%)
- Bachelor's Degree: 6 (0.0%)
- Bachelor’s degree: 6 (0.0%)
- 预科: 6 (0.0%)
- undergraduate course: 6 (0.0%)
- Undergraduate course: 5 (0.0%)
- high school: 4 (0.0%)
- other: 3 (0.0%)
- High School: 3 (0.0%)
- Full-time undergraduate: 3 (0.0%)
- Bachelor of arts: 3 (0.0%)
- Diploma: 3 (0.0%)
- BACHELOR'S: 3 (0.0%)
- bachlor: 3 (0.0%)
- senior high school: 3 (0.0%)
- Master’s Degree: 3 (0.0%)
- UNDERGRADUATE COURSE: 2 (0.0%)
- Secondary School: 2 (0.0%)
- bachelor's degree: 2 (0.0%)
- Bachelor of Engineering: 2 (0.0%)
- BA: 2 (0.0%)
- Bachelor's degree: 2 (0.0%)
- Msc.: 2 (0.0%)
- postgraduate: 1 (0.0%)
- Bachelor of Laws: 1 (0.0%)
- 大专: 1 (0.0%)
- Bachelor of Commerce: 1 (0.0%)
- High school: 1 (0.0%)
- 学士: 1 (0.0%)
- Regular college course: 1 (0.0%)
- Bachelor’s Degree of Law: 1 (0.0%)
- bachelor's degree program: 1 (0.0%)
- Bachelor of Accounting: 1 (0.0%)

### language_test_type

- 预期类别数: 4
- 实际类别数: 4
- ❌ 未预期的值: ['Other']
- ⚠️ 缺少的预期值: ['none']

**值分布**:
- Other: 67,499 (93.2%)
- IELTS: 3,705 (5.1%)
- PTE: 758 (1.0%)
- TOEFL: 433 (0.6%)

### application_season

- 预期类别数: 4
- 实际类别数: 5
- ❌ 未预期的值: ['Unknown']

**值分布**:
- Unknown: 67,453 (93.2%)
- Summer: 1,778 (2.5%)
- Fall: 1,199 (1.7%)
- Spring: 1,038 (1.4%)
- Winter: 927 (1.3%)

### university_matching_level

- 预期类别数: 3
- 实际类别数: 4
- ❌ 未预期的值: ['极低匹配度']

**值分布**:
- 高匹配度: 55,216 (76.3%)
- 中等匹配度: 16,664 (23.0%)
- 低匹配度: 444 (0.6%)
- 极低匹配度: 71 (0.1%)

### competition_level

- 预期类别数: 3
- 实际类别数: 3
- ❌ 未预期的值: ['极高竞争']
- ⚠️ 缺少的预期值: ['低竞争']

**值分布**:
- 极高竞争: 32,819 (45.3%)
- 高竞争: 20,341 (28.1%)
- 中等竞争: 19,235 (26.6%)

### success_probability_level

- 预期类别数: 5
- 实际类别数: 5
- ✅ 所有值都在预期范围内

**值分布**:
- 很低: 32,073 (44.3%)
- 较低: 21,395 (29.6%)
- 中等: 9,520 (13.2%)
- 较高: 8,395 (11.6%)
- 很高: 1,012 (1.4%)


## 6. 特征相关性分析

### 高相关性特征对 (|相关系数| > 0.8)

| 特征1 | 特征2 | 相关系数 |
|-------|-------|----------|
| gpa_percentile | academic_strength_score | 0.902 |
| gpa_percentile | applicant_comprehensive_strength | 0.824 |
| academic_strength_score | applicant_comprehensive_strength | 0.943 |
| target_university_tier_score | estimated_success_probability | -0.904 |
| competition_index | estimated_success_probability | -0.812 |

## 7. 总体评估和建议

### 数据完整性得分: 76.6/100

⚠️ **良好**: 数据完整性较好，建议处理缺失值后使用

### 改进建议:

1. **缺失值处理**:
   - language_score_normalized: 93.3%缺失，建议考虑是否删除或填充
   - time_to_graduation: 93.2%缺失，建议考虑是否删除或填充
   - 语言考试_考试时间: 93.2%缺失，建议考虑是否删除或填充
   - 工作经历_工作职责: 91.7%缺失，建议考虑是否删除或填充
   - 工作经历_结束时间: 88.3%缺失，建议考虑是否删除或填充

2. **数据范围检查**:
   - application_year: 值超出预期范围，需要检查数据质量

3. **特征冗余**:
   - 发现高相关性特征对，建议在建模时考虑特征选择
   - 可以使用PCA或其他降维方法处理共线性问题

