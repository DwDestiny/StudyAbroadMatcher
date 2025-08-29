# 第一阶段实现规划

## 模块1：专业路径聚类分析（clustering_analysis.py）

### 功能目标
对申请量≥100的专业进行K-means聚类，识别不同的成功申请路径。

### 输入规格
- **数据源**：`data/processed/final_feature_dataset_latest.csv`
- **筛选条件**：申请量≥100的专业（预估300+个专业）
- **特征维度**：75维标准化特征向量

### 核心逻辑
1. **数据预处理**
   - 按target_major_name分组统计申请量
   - 筛选申请量≥100的专业
   - 提取对应的75维特征数据

2. **聚类参数优化**
   ```python
   # 聚类数范围：k=2~5
   # 评估指标：轮廓系数(silhouette_score)、肘部法则、Davies-Bouldin指数
   # 选择标准：轮廓系数>0.3且样本分布相对均衡
   ```

3. **聚类执行**
   - 对每个专业独立执行聚类分析
   - 记录聚类中心、标签分配、评估指标
   - 保存聚类结果到`data/clustering_results/`

### 输出格式
```json
{
  "专业名称": {
    "total_applications": 156,
    "optimal_k": 3,
    "silhouette_score": 0.42,
    "clusters": {
      "cluster_0": {
        "size": 67,
        "percentage": 0.43,
        "center": [0.23, -0.45, ...],  // 75维中心点
        "description": "高GPA理工科背景"
      },
      "cluster_1": {...},
      "cluster_2": {...}
    },
    "feature_importance": {
      "source_university_score": 0.15,
      "gpa_percentile": 0.18,
      "major_matching_score": 0.12,
      ...
    }
  }
}
```

---

## 模块2：路径画像构建系统（path_profile_builder.py）

### 功能目标
基于聚类结果，为每个路径构建详细的申请者画像。

### 输入规格
- **聚类结果**：`data/clustering_results/`下的JSON文件
- **原始数据**：`data/processed/final_feature_dataset_latest.csv`

### 核心逻辑
1. **画像统计特征**
   ```python
   # 对每个聚类路径计算：
   # - 均值、标准差、中位数、四分位数
   # - 关键特征的分布特征
   # - 路径代表性指标（聚类内相似度）
   ```

2. **路径标签生成**
   - 基于特征权重自动生成路径描述
   - 识别每个路径的核心特征组合
   - 生成业务可理解的标签

3. **覆盖度分析**
   - 计算每个路径的样本覆盖率
   - 评估路径的代表性和稳定性

### 输出格式
```json
{
  "专业名称": {
    "paths": {
      "path_0": {
        "label": "985高GPA理工背景",
        "sample_size": 67,
        "coverage": 0.43,
        "representativeness": 0.78,
        "profile": {
          "source_university_score": {
            "mean": 88.5, "std": 6.2, "median": 89.0,
            "q25": 85.0, "q75": 92.0
          },
          "gpa_percentile": {
            "mean": 82.3, "std": 8.1, "median": 83.0,
            "q25": 78.0, "q75": 87.0
          },
          ...
        },
        "key_features": ["source_university_score", "gpa_percentile", "major_matching_score"],
        "success_indicators": {
          "high_university_background": 0.85,
          "strong_academic_performance": 0.78,
          "relevant_major_background": 0.67
        }
      }
    }
  }
}
```

---

## 模块3：匹配度计算引擎（matching_calculator.py）

### 功能目标
实现两阶段匹配算法，为新学生计算与特定专业的匹配度。

### 核心算法设计

#### 阶段1：路径归属判断
```python
def assign_path(student_vector, major_paths):
    """
    计算学生向量与各路径中心的距离
    返回最相似的路径和置信度
    """
    distances = []
    for path in major_paths:
        dist = cosine_distance(student_vector, path['center'])
        distances.append(dist)
    
    best_path_idx = np.argmin(distances)
    confidence = 1 - distances[best_path_idx]
    
    return best_path_idx, confidence
```

#### 阶段2：相似度计算
```python
def calculate_similarity(student_vector, path_profile, feature_weights):
    """
    基于路径画像计算加权余弦相似度
    考虑特征分布和权重
    """
    weighted_similarity = 0
    total_weight = 0
    
    for feature, weight in feature_weights.items():
        student_val = student_vector[feature]
        path_mean = path_profile[feature]['mean']
        path_std = path_profile[feature]['std']
        
        # 标准化距离
        normalized_diff = abs(student_val - path_mean) / (path_std + 1e-6)
        feature_sim = max(0, 1 - normalized_diff)
        
        weighted_similarity += feature_sim * weight
        total_weight += weight
    
    return weighted_similarity / total_weight
```

### 特征权重策略
```python
FEATURE_WEIGHTS = {
    'source_university_score': 0.20,    # 院校背景
    'gpa_percentile': 0.18,             # 学术成绩  
    'major_matching_score': 0.15,       # 专业匹配度
    'language_score_normalized': 0.12,   # 语言能力
    'work_experience_years': 0.10,      # 工作经验
    'work_relevance_score': 0.08,       # 工作相关性
    # 其他特征权重递减...
}
```

### 接口设计
```python
class MatchingCalculator:
    def calculate_match_score(self, student_features, target_major):
        """
        输入：学生特征向量(75维)，目标专业名称
        输出：匹配度分数(0-100)，路径标签，置信度
        """
        # 1. 获取专业路径数据
        major_paths = self.load_major_paths(target_major)
        
        # 2. 路径归属判断
        best_path, confidence = self.assign_path(student_features, major_paths)
        
        # 3. 相似度计算
        similarity = self.calculate_similarity(
            student_features, 
            major_paths[best_path]['profile'],
            self.feature_weights
        )
        
        # 4. 最终分数计算
        match_score = int(similarity * confidence * 100)
        
        return {
            'match_score': match_score,
            'matched_path': major_paths[best_path]['label'],
            'confidence': confidence,
            'path_coverage': major_paths[best_path]['coverage']
        }
```

---

## 实施时间线

### Week 1: 聚类分析模块
- [x] 数据筛选和预处理逻辑
- [x] K-means聚类参数优化
- [x] 结果评估和存储

### Week 2: 画像构建模块  
- [x] 统计特征计算
- [x] 路径标签生成
- [x] 画像数据结构设计

### Week 3: 匹配计算模块
- [x] 路径归属算法实现
- [x] 相似度计算逻辑
- [x] 接口封装和测试

---

## 质量控制标准

1. **数据一致性**：确保所有模块使用相同的特征定义和数据格式
2. **算法稳定性**：聚类结果在多次运行中保持一致
3. **性能要求**：单次匹配计算在100ms内完成
4. **可解释性**：每个匹配结果都能提供清晰的路径解释

## 评估指标

1. **聚类质量**：平均轮廓系数>0.35，路径分布相对均衡
2. **画像准确性**：路径特征与实际申请者分布吻合度>0.8  
3. **匹配合理性**：专家评估匹配结果的业务合理性>85%