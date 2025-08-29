# 快速使用指南（生产级增强版）🚀

## 🚀 5分钟快速上手

### 1. 环境准备
```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 确保依赖已安装
pip install scikit-learn matplotlib pandas numpy
```

### 2. 基础使用示例

```python
# 推荐：导入增强系统（生产级）
from src.matching_engine.enhanced_matching_system import EnhancedStudentMajorMatchingSystem

# 或使用原系统进行对比测试：
# from src.matching_engine.matching_system import StudentMajorMatchingSystem

# 创建并初始化增强系统
system = EnhancedStudentMajorMatchingSystem()
system.initialize_system()  # 首次约30秒，包含数据清洗优化
```

### 3. 学生特征准备

```python
# 示例：211大学，良好成绩的学生
student_profile = {
    # === 必填核心特征 ===
    'source_university_tier_score': 75,      # 院校分数 (0-100)
    'gpa_percentile': 75,                    # GPA百分位 (0-100)
    'major_matching_score': 0.7,             # 专业匹配度 (0-1)
    'language_score_normalized': 70,         # 语言分数 (0-100)
    'work_experience_years': 1,              # 工作年限
    'work_relevance_score': 0.5,             # 工作相关性 (0-1)
    
    # === 系统特征（建议填写） ===
    'target_university_tier_score': 80,
    'university_matching_score': 0.7,
    'competition_index': 6.0,
    'academic_strength_score': 75,
    'applicant_comprehensive_strength': 72
}
```

### 4. 快速匹配示例

```python
# 方法1：单个专业匹配
result = system.calculate_single_match(student_profile, "Master of Commerce")
print(f"匹配度: {result['match_score']}分")
print(f"匹配等级: {result['match_level']}")
print(f"推荐路径: {result['matched_path']}")

# 方法2：寻找最佳匹配
best_matches = system.find_best_matches(student_profile, top_n=5)
print("\\n前5个推荐专业:")
for i, match in enumerate(best_matches['best_matches']):
    print(f"{i+1}. {match['major']}: {match['score']}分 ({match['level']})")
```

## 📋 常用场景

### 场景1：评估特定专业
```python
# 想申请计算机硕士，看看匹配度
cs_result = system.calculate_single_match(student_profile, "Master of Computer Science")

if cs_result['success']:
    score = cs_result['match_score']
    if score >= 65:
        print("推荐申请！匹配度良好")
    elif score >= 50:
        print("可以考虑，建议提升相关背景")
    else:
        print("不推荐，差距较大")
```

### 场景2：对比多个专业
```python
# 对比几个感兴趣的专业
target_majors = [
    "Master of Commerce",
    "Master of Computer Science", 
    "Master of Data Science",
    "Master of Management"
]

comparison = system.calculate_batch_matches(student_profile, target_majors)

print("专业对比结果:")
for major, result in comparison['results'].items():
    if result['success']:
        print(f"{major}: {result['match_score']}分 ({result['match_level']})")
```

### 场景3：全面专业探索
```python
# 看看有哪些专业适合我
exploration = system.find_best_matches(student_profile, top_n=10)

print("为您推荐的专业:")
for match in exploration['best_matches']:
    print(f"• {match['major']}")
    print(f"  匹配度: {match['score']}分 ({match['level']})")
    print(f"  成功路径: {match['path']}")
    print()
```

## 🎯 不同背景学生的预期结果

### 优秀学生（985 + 高GPA）
```python
excellent_student = {
    'source_university_tier_score': 90,
    'gpa_percentile': 90,
    'major_matching_score': 0.9,
    'language_score_normalized': 85,
    'work_experience_years': 2,
    'work_relevance_score': 0.8
}

# 预期：在高端专业（JD、高级硕士）匹配度相对较高
# 在入门专业（Bachelor）可能因overqualified而得分较低
```

### 普通学生（一般本科 + 中等成绩）
```python
ordinary_student = {
    'source_university_tier_score': 60,
    'gpa_percentile': 65,
    'major_matching_score': 0.5,
    'language_score_normalized': 65,
    'work_experience_years': 0,
    'work_relevance_score': 0.3
}

# 预期：在入门级专业（Bachelor、基础硕士）匹配度较高
# 在顶级专业可能因underqualified而得分较低
```

## ⚠️ 重要提示

### 理解匹配度含义
- **高匹配度** ≠ 专业简单，而是 = 你的背景与该专业历史成功申请者相似
- **低匹配度** 可能因为：
  - overqualified：你的条件远超该专业要求
  - underqualified：你的条件达不到该专业要求
  - 专业特点不符：专业偏好某种特定背景

### 如何解读结果
```python
result = system.calculate_single_match(student_profile, "某专业")

print(f"匹配度: {result['match_score']}分")
# 80+: 高度匹配，强烈推荐
# 65-79: 较好匹配，推荐申请
# 50-64: 一般匹配，可以考虑
# <50: 不匹配，不推荐

print(f"匹配路径: {result['matched_path']}")
# 例如："985-高GPA-高匹配" - 说明该专业主要录取985高分学生
# 你的背景如果也是985高分，匹配度就会高

print(f"置信度: {result['path_confidence']}")
# 反映你与最相似路径的匹配程度（增强系统：平均88%+）
# ✅ 已优化：置信度从1.2%提升至88.1%，现在可直接参考绝对数值
```

## 🔧 性能提示

### 首次使用（增强系统）
```python
# 首次初始化：约30秒（包含数据清洗和统计优化）
system.initialize_system()

# 后续使用：约3秒（缓存加载）
system.initialize_system()  # 快速完成

# 系统性能提升：
# - 匹配准确率：43分 → 90分 (+47分)
# - 路径置信度：1.2% → 88.1% (73倍改善)
# - 支持专业数：50 → 357 (7倍扩展)
```

### 批量查询优化
```python
# 推荐：一次性查询多个专业
majors = ["专业1", "专业2", "专业3"]
results = system.calculate_batch_matches(student_profile, majors)

# 避免：多次单独查询
# for major in majors:
#     system.calculate_single_match(student_profile, major)  # 较慢
```

## 📞 获取帮助

### 查看可用专业
```python
available_majors = system.get_available_majors()
print(f"系统支持 {len(available_majors)} 个专业")
print("前10个专业:", available_majors[:10])
```

### 查看专业详情
```python
major_info = system.get_major_details("Master of Commerce")
if major_info['success']:
    print(f"历史申请量: {major_info['total_applications']}")
    print(f"成功路径数: {major_info['num_paths']}")
    print("各路径分布:")
    for path_name, path_info in major_info['paths'].items():
        print(f"  {path_info['label']}: {path_info['sample_size']}人")
```

### 系统状态检查
```python
status = system.get_system_status()
print("系统状态:")
print(f"  初始化: {status['initialized']}")
print(f"  可用专业: {status['available_majors_count']}")
print(f"  更新时间: {status['last_update']}")
```