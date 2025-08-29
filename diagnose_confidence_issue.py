"""
诊断路径置信度计算精度问题
分析特征维度、数值范围、相似度计算等关键问题
"""

import pandas as pd
import numpy as np
import json
from src.matching_engine.matching_system import StudentMajorMatchingSystem

def analyze_feature_dimensions():
    """分析特征维度匹配问题"""
    
    print("=== 特征维度分析 ===")
    
    # 加载系统
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    # 查看特征列信息
    feature_cols = system.matching_calculator.feature_cols
    print(f"系统识别的特征列数量: {len(feature_cols)}")
    print("前10个特征列:", feature_cols[:10])
    
    # 查看聚类中心维度
    first_major = list(system.matching_calculator.path_profiles.keys())[0]
    first_path = list(system.matching_calculator.path_profiles[first_major]['paths'].values())[0]
    cluster_center = first_path['cluster_center']
    
    print(f"聚类中心维度: {len(cluster_center)}")
    print(f"特征列与聚类中心维度{'匹配' if len(feature_cols) == len(cluster_center) else '不匹配'}")
    
    # 测试学生特征
    test_student = {
        'source_university_tier_score': 85,
        'gpa_percentile': 78,
        'major_matching_score': 0.8,
        'language_score_normalized': 75,
        'work_experience_years': 1,
        'work_relevance_score': 0.6,
        'target_university_tier_score': 90,
        'university_matching_score': 0.85,
        'competition_index': 6.5,
        'academic_strength_score': 80,
        'applicant_comprehensive_strength': 75
    }
    
    # 标准化学生特征
    normalized_features = system.matching_calculator.normalize_student_features(test_student)
    student_vector = [normalized_features.get(feature, 0.0) for feature in feature_cols]
    
    print(f"学生特征向量维度: {len(student_vector)}")
    print(f"学生提供的非零特征数: {sum(1 for v in student_vector if v != 0)}")
    print(f"学生特征值范围: [{min(student_vector):.2f}, {max(student_vector):.2f}]")
    
    return {
        'feature_cols_count': len(feature_cols),
        'cluster_center_dim': len(cluster_center),
        'student_vector_dim': len(student_vector),
        'student_nonzero_features': sum(1 for v in student_vector if v != 0),
        'student_vector': student_vector,
        'cluster_center': cluster_center
    }

def analyze_feature_ranges():
    """分析特征值范围差异"""
    
    print("\n=== 特征值范围分析 ===")
    
    # 加载原始数据
    df = pd.read_csv('data/processed/final_feature_dataset_latest.csv')
    
    # 识别数值特征
    exclude_patterns = ['ID', 'id', '名称', '时间', '日期', '描述', '类型', '开始', '结束', '单位', '职位', '职责']
    numeric_features = []
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            if not any(pattern in col for pattern in exclude_patterns):
                numeric_features.append(col)
    
    print(f"数值特征总数: {len(numeric_features)}")
    
    # 分析前15个特征的范围
    feature_analysis = {}
    
    for feature in numeric_features[:15]:
        values = df[feature].dropna()
        if len(values) > 0:
            feature_analysis[feature] = {
                'min': float(values.min()),
                'max': float(values.max()),
                'mean': float(values.mean()),
                'std': float(values.std()),
                'range_span': float(values.max() - values.min())
            }
            
            print(f"{feature}:")
            print(f"  范围: [{values.min():.2f}, {values.max():.2f}]")
            print(f"  均值±标准差: {values.mean():.2f}±{values.std():.2f}")
            print(f"  跨度: {values.max() - values.min():.2f}")
    
    return feature_analysis

def test_similarity_calculation():
    """测试相似度计算过程"""
    
    print("\n=== 相似度计算测试 ===")
    
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    # 测试学生
    test_student = {
        'source_university_tier_score': 75,    # 中等院校
        'gpa_percentile': 75,                  # 中等GPA
        'major_matching_score': 0.7,           # 中等匹配
        'language_score_normalized': 70,       # 中等语言
        'work_experience_years': 1,            
        'work_relevance_score': 0.5,           
        'target_university_tier_score': 80,
        'university_matching_score': 0.7,
        'competition_index': 6.0,
        'academic_strength_score': 75,
        'applicant_comprehensive_strength': 72
    }
    
    # 测试专业
    test_major = "Master of Commerce"
    
    # 获取专业路径数据
    major_data = system.matching_calculator.path_profiles[test_major]
    major_paths = major_data['paths']
    
    # 标准化学生特征
    normalized_features = system.matching_calculator.normalize_student_features(test_student)
    
    print(f"测试专业: {test_major}")
    print(f"可用路径数: {len(major_paths)}")
    
    # 测试每个路径的相似度
    for path_key, path_info in major_paths.items():
        print(f"\n路径: {path_info['label']}")
        print(f"路径样本数: {path_info['sample_size']}")
        
        # 获取聚类中心
        cluster_center = path_info['cluster_center']
        print(f"聚类中心维度: {len(cluster_center)}")
        
        # 构建学生向量
        feature_cols = system.matching_calculator.feature_cols
        student_vector = [normalized_features.get(feature, 0.0) for feature in feature_cols]
        
        print(f"学生向量维度: {len(student_vector)}")
        print(f"学生非零特征: {sum(1 for v in student_vector if v != 0)}/{len(student_vector)}")
        
        # 手动计算余弦相似度
        min_dim = min(len(student_vector), len(cluster_center))
        s_vec = np.array(student_vector[:min_dim])
        c_vec = np.array(cluster_center[:min_dim])
        
        print(f"实际计算维度: {min_dim}")
        print(f"学生向量范围: [{s_vec.min():.3f}, {s_vec.max():.3f}]")
        print(f"聚类中心范围: [{c_vec.min():.3f}, {c_vec.max():.3f}]")
        
        # 计算余弦相似度
        dot_product = np.dot(s_vec, c_vec)
        norm_s = np.linalg.norm(s_vec)
        norm_c = np.linalg.norm(c_vec)
        
        print(f"点积: {dot_product:.6f}")
        print(f"学生向量模长: {norm_s:.6f}")
        print(f"聚类中心模长: {norm_c:.6f}")
        
        if norm_s > 0 and norm_c > 0:
            cosine_sim = dot_product / (norm_s * norm_c)
            print(f"余弦相似度: {cosine_sim:.6f}")
        else:
            print("余弦相似度: 无法计算（零向量）")
        
        # 使用系统方法计算
        system_sim = system.matching_calculator.calculate_cosine_similarity(student_vector, cluster_center)
        print(f"系统计算结果: {system_sim:.6f}")

def propose_solutions():
    """提出解决方案"""
    
    print("\n=== 问题诊断与解决方案 ===")
    
    # 运行诊断
    dim_analysis = analyze_feature_dimensions()
    range_analysis = analyze_feature_ranges()
    
    print("\n--- 诊断结果 ---")
    
    # 问题1：维度匹配
    if dim_analysis['feature_cols_count'] == dim_analysis['cluster_center_dim']:
        print("✓ 特征维度匹配正常")
    else:
        print(f"✗ 特征维度不匹配：特征列{dim_analysis['feature_cols_count']}维 vs 聚类中心{dim_analysis['cluster_center_dim']}维")
    
    # 问题2：特征稀疏性
    sparsity = 1 - (dim_analysis['student_nonzero_features'] / dim_analysis['student_vector_dim'])
    print(f"{'✗' if sparsity > 0.7 else '✓'} 学生特征稀疏度: {sparsity:.1%}")
    
    # 问题3：特征范围差异
    max_range_span = max(info['range_span'] for info in range_analysis.values())
    min_range_span = min(info['range_span'] for info in range_analysis.values())
    range_ratio = max_range_span / max(min_range_span, 1e-6)
    print(f"{'✗' if range_ratio > 1000 else '✓'} 特征范围差异比: {range_ratio:.1f}倍")
    
    print("\n--- 解决方案 ---")
    
    solutions = []
    
    if dim_analysis['feature_cols_count'] != dim_analysis['cluster_center_dim']:
        solutions.append("1. 修复特征维度匹配：确保学生输入特征与聚类中心维度一致")
    
    if sparsity > 0.7:
        solutions.append("2. 优化特征填充策略：使用特征均值而非0填充缺失值")
    
    if range_ratio > 1000:
        solutions.append("3. 改进特征标准化：使用RobustScaler处理不同范围的特征")
    
    solutions.append("4. 替换相似度算法：考虑使用加权欧氏距离或马哈拉诺比斯距离")
    solutions.append("5. 重新设计置信度计算：基于分位数而非绝对相似度")
    
    for solution in solutions:
        print(f"  {solution}")
    
    return solutions

def main():
    """主诊断流程"""
    
    print("=== 路径置信度计算精度问题诊断 ===")
    
    # 运行各项分析
    analyze_feature_dimensions()
    analyze_feature_ranges()
    test_similarity_calculation()
    
    # 提出解决方案
    solutions = propose_solutions()
    
    return solutions

if __name__ == "__main__":
    main()