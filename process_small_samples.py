"""
简化版小样本专业处理脚本
"""

import pandas as pd
import numpy as np
import json
import os

def safe_float(value):
    """安全转换为float，避免JSON序列化问题"""
    if pd.isna(value):
        return 0.0
    return float(value)

def safe_int(value):
    """安全转换为int，避免JSON序列化问题"""
    if pd.isna(value):
        return 0
    return int(value)

def analyze_small_sample_majors():
    """分析小样本专业"""
    
    print("=== 小样本专业分析 ===")
    
    # 加载数据
    df = pd.read_csv('data/processed/final_feature_dataset_latest.csv')
    target_col = "申请院校_专业名称"
    
    # 统计专业申请量
    major_counts = df[target_col].value_counts()
    
    # 分类专业
    large_sample = major_counts[major_counts >= 100]
    medium_sample = major_counts[(major_counts >= 50) & (major_counts < 100)]
    small_sample = major_counts[(major_counts >= 30) & (major_counts < 50)]
    tiny_sample = major_counts[major_counts < 30]
    
    print(f"大样本专业(≥100): {len(large_sample)}个，覆盖{large_sample.sum()}申请")
    print(f"中等样本专业(50-99): {len(medium_sample)}个，覆盖{medium_sample.sum()}申请")
    print(f"小样本专业(30-49): {len(small_sample)}个，覆盖{small_sample.sum()}申请") 
    print(f"微样本专业(<30): {len(tiny_sample)}个，覆盖{tiny_sample.sum()}申请")
    
    # 处理中等样本和小样本专业
    all_processable = pd.concat([medium_sample, small_sample])
    print(f"\n可处理的小样本专业总数: {len(all_processable)}个")
    print(f"新增覆盖申请量: {all_processable.sum()}个")
    
    # 识别特征列
    exclude_patterns = ['ID', 'id', '名称', '时间', '日期', '描述', '类型', '开始', '结束', '单位', '职位', '职责']
    feature_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            if not any(pattern in col for pattern in exclude_patterns):
                feature_cols.append(col)
    
    print(f"识别特征列: {len(feature_cols)}个")
    
    # 为前20个小样本专业创建简化画像
    small_profiles = {}
    processed_count = 0
    
    print("\\n=== 处理小样本专业画像 ===")
    
    for major_name, count in all_processable.head(20).items():
        try:
            print(f"处理: {major_name} ({count}个申请)")
            
            # 获取该专业数据
            major_data = df[df[target_col] == major_name]
            
            # 创建简化画像
            profile = {
                'major_name': major_name,
                'sample_size': safe_int(count),
                'profile_type': 'simplified',
                'key_features': {}
            }
            
            # 计算关键特征统计
            key_features = [
                'source_university_tier_score',
                'gpa_percentile', 
                'major_matching_score',
                'language_score_normalized',
                'work_experience_years'
            ]
            
            for feature in key_features:
                if feature in major_data.columns:
                    values = major_data[feature].dropna()
                    if len(values) > 0:
                        profile['key_features'][feature] = {
                            'mean': safe_float(values.mean()),
                            'std': safe_float(values.std()),
                            'median': safe_float(values.median()),
                            'count': safe_int(len(values))
                        }
            
            # 生成标签
            if 'source_university_tier_score' in profile['key_features']:
                tier_score = profile['key_features']['source_university_tier_score']['mean']
                if tier_score >= 85:
                    tier_label = '名校'
                elif tier_score >= 75:
                    tier_label = '211'
                else:
                    tier_label = '本科'
            else:
                tier_label = '混合'
            
            if 'gpa_percentile' in profile['key_features']:
                gpa = profile['key_features']['gpa_percentile']['mean']
                if gpa >= 80:
                    gpa_label = '高GPA'
                elif gpa >= 70:
                    gpa_label = '中GPA'
                else:
                    gpa_label = '一般GPA'
            else:
                gpa_label = '混合GPA'
            
            profile['label'] = f"{tier_label}-{gpa_label}-小样本({count})"
            
            # 计算置信度
            if count >= 50:
                profile['confidence'] = 0.7
            elif count >= 40:
                profile['confidence'] = 0.6
            else:
                profile['confidence'] = 0.5
            
            small_profiles[major_name] = profile
            processed_count += 1
            
        except Exception as e:
            print(f"处理专业 {major_name} 失败: {e}")
            continue
    
    print(f"成功处理 {processed_count} 个小样本专业")
    
    # 保存结果
    os.makedirs('data/small_sample_profiles', exist_ok=True)
    
    result = {
        'analysis_summary': {
            'large_sample_majors': safe_int(len(large_sample)),
            'medium_sample_majors': safe_int(len(medium_sample)), 
            'small_sample_majors': safe_int(len(small_sample)),
            'processable_majors': safe_int(len(all_processable)),
            'processed_majors': processed_count
        },
        'small_sample_profiles': small_profiles,
        'processing_info': {
            'method': 'simplified_statistical',
            'feature_count': len(feature_cols),
            'confidence_adjustment': 'sample_size_based'
        }
    }
    
    # 保存到文件
    output_file = 'data/small_sample_profiles/simplified_small_sample_profiles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\\n结果已保存至: {output_file}")
    
    return result

def test_small_sample_matching():
    """测试小样本专业匹配"""
    
    print("\\n=== 小样本专业匹配测试 ===")
    
    # 加载小样本专业数据
    profiles_file = 'data/small_sample_profiles/simplified_small_sample_profiles.json'
    if not os.path.exists(profiles_file):
        print("小样本专业数据不存在，请先运行分析")
        return
    
    with open(profiles_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    small_profiles = data['small_sample_profiles']
    
    # 测试学生
    test_student = {
        'source_university_tier_score': 75,
        'gpa_percentile': 75,
        'major_matching_score': 0.7,
        'language_score_normalized': 70,
        'work_experience_years': 1
    }
    
    print(f"测试学生背景: 211院校，75%GPA，中等专业匹配")
    print(f"可测试的小样本专业数: {len(small_profiles)}")
    
    # 测试前5个专业
    matches = []
    
    for major_name, profile in list(small_profiles.items())[:5]:
        
        similarity_score = 0.0
        feature_count = 0
        
        # 计算简单相似度
        for feature, student_val in test_student.items():
            if feature in profile['key_features']:
                profile_mean = profile['key_features'][feature]['mean']
                profile_std = max(profile['key_features'][feature]['std'], 1.0)
                
                # 标准化差距
                z_score = abs(student_val - profile_mean) / profile_std
                
                # 转换为相似度
                if z_score <= 0.5:
                    feature_sim = 0.9
                elif z_score <= 1.0:
                    feature_sim = 0.7
                elif z_score <= 2.0:
                    feature_sim = 0.5
                else:
                    feature_sim = 0.3
                
                similarity_score += feature_sim
                feature_count += 1
        
        if feature_count > 0:
            avg_similarity = similarity_score / feature_count
            
            # 考虑置信度调整
            confidence = profile['confidence']
            final_score = int((avg_similarity * confidence) * 100)
            
            matches.append({
                'major': major_name,
                'score': final_score,
                'sample_size': profile['sample_size'],
                'label': profile['label'],
                'confidence': confidence
            })
    
    # 按分数排序
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    print("\\n小样本专业匹配结果:")
    for i, match in enumerate(matches):
        print(f"{i+1}. {match['major']}: {match['score']}分")
        print(f"   样本数: {match['sample_size']}, 标签: {match['label']}")
        print(f"   置信度: {match['confidence']:.1f}")

def main():
    """主函数"""
    
    # 1. 分析和处理小样本专业
    result = analyze_small_sample_majors()
    
    # 2. 测试小样本匹配
    test_small_sample_matching()
    
    # 3. 输出总结
    print("\\n=== 小样本专业处理总结 ===")
    analysis = result['analysis_summary']
    print(f"系统可处理专业数扩展:")
    print(f"  原有大样本专业: {analysis['large_sample_majors']}个")
    print(f"  新增中等样本: {analysis['medium_sample_majors']}个")  
    print(f"  新增小样本: {analysis['small_sample_majors']}个")
    print(f"  总覆盖专业数: {analysis['large_sample_majors'] + analysis['processable_majors']}个")
    print(f"  本次处理完成: {analysis['processed_majors']}个样例")

if __name__ == "__main__":
    main()