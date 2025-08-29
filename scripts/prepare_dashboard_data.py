#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据看板聚合数据准备脚本

该脚本读取最终特征数据集，进行数据聚合和统计分析，生成看板所需的JSON数据。
主要功能包括：
1. 总体概览指标计算
2. 按目标院校和专业分组的统计分析
3. 全体数据的分布统计
4. 生成前端可直接使用的JSON格式数据
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')


def load_data(file_path):
    """
    加载数据集
    
    Args:
        file_path (str): 数据文件路径
        
    Returns:
        pd.DataFrame: 加载的数据集
    """
    print(f"正在加载数据: {file_path}")
    df = pd.read_csv(file_path)
    print(f"数据加载完成，共 {len(df)} 条记录")
    return df


def calculate_overview_metrics(df):
    """
    计算总体概览指标
    
    Args:
        df (pd.DataFrame): 原始数据集
        
    Returns:
        dict: 总体概览指标
    """
    print("正在计算总体概览指标...")
    
    # 总申请量
    total_applications = len(df)
    
    # TOP3院校（按申请量）
    top_universities = df['申请院校_院校名称_标准化'].value_counts().head(3).to_dict()
    
    # TOP3专业（按申请量）
    top_majors = df['申请院校_专业名称_标准化'].value_counts().head(3).to_dict()
    
    # 平均GPA（百分制）
    avg_gpa = df['gpa_percentile'].mean()
    
    # 院校提升度计算（目标院校评分 - 生源院校评分）
    df_with_scores = df.dropna(subset=['target_university_tier_score', 'source_university_tier_score'])
    avg_university_improvement = (df_with_scores['target_university_tier_score'] - 
                                 df_with_scores['source_university_tier_score']).mean()
    
    # 985/211学生占比
    ratio_985 = (df['source_is_985'] == 1).mean() * 100
    ratio_211 = (df['source_is_211'] == 1).mean() * 100
    
    # 有工作经验学生占比
    ratio_work_exp = (df['has_work_experience'] == 1).mean() * 100
    
    # 语言成绩平均分
    avg_language_score = df[df['has_language_score'] == 1]['language_score_normalized'].mean()
    
    # 专业匹配度统计
    if 'major_matching_score' in df.columns:
        avg_major_matching = df['major_matching_score'].mean()
        same_field_ratio = (df['is_same_field'] == 1).mean() * 100 if 'is_same_field' in df.columns else 0
    else:
        avg_major_matching = None
        same_field_ratio = 0
    
    overview = {
        "total_applications": int(total_applications),
        "top_universities": [{"name": k, "count": int(v)} for k, v in top_universities.items()],
        "top_majors": [{"name": k, "count": int(v)} for k, v in top_majors.items()],
        "avg_gpa": round(float(avg_gpa), 1) if not pd.isna(avg_gpa) else None,
        "avg_university_improvement": round(float(avg_university_improvement), 1),
        "avg_major_matching": round(float(avg_major_matching), 3) if avg_major_matching is not None else None,
        "same_field_ratio": round(same_field_ratio, 1),
        "student_backgrounds": {
            "ratio_985": round(ratio_985, 1),
            "ratio_211": round(ratio_211, 1),
            "ratio_work_experience": round(ratio_work_exp, 1)
        },
        "avg_language_score": round(float(avg_language_score), 1) if not pd.isna(avg_language_score) else None
    }
    
    print("总体概览指标计算完成")
    return overview


def calculate_university_groups(df):
    """
    按目标院校分组统计
    
    Args:
        df (pd.DataFrame): 原始数据集
        
    Returns:
        list: 按目标院校分组的统计数据
    """
    print("正在计算按目标院校分组的统计数据...")
    
    university_groups = []
    
    # 只选择申请量较多的院校（至少50个申请）
    university_counts = df['申请院校_院校名称_标准化'].value_counts()
    popular_universities = university_counts[university_counts >= 50].index.tolist()
    
    for university in popular_universities[:20]:  # 取前20个热门院校
        uni_data = df[df['申请院校_院校名称_标准化'] == university].copy()
        
        # 基本信息
        application_count = len(uni_data)
        
        # 五个维度的统计（排除缺失值）
        # 专业匹配度需要转换为0-100分制以便与其他维度统一显示
        major_matching_data = uni_data['major_matching_score'].dropna() * 100 if 'major_matching_score' in uni_data.columns else pd.Series([])
        
        dimensions = {
            'source_university_score': uni_data['source_university_tier_score'].dropna(),
            'academic_strength': uni_data['academic_strength_score'].dropna(),
            'language_ability': uni_data[uni_data['has_language_score'] == 1]['language_score_normalized'].dropna(),
            'major_matching': major_matching_data,
            'work_experience': uni_data['work_experience_years'].dropna()
        }
        
        # 计算均值和中位数
        stats = {}
        for dim_name, dim_data in dimensions.items():
            if len(dim_data) > 0:
                stats[dim_name] = {
                    'mean': round(float(dim_data.mean()), 1),
                    'median': round(float(dim_data.median()), 1),
                    'count': int(len(dim_data))
                }
            else:
                stats[dim_name] = {'mean': None, 'median': None, 'count': 0}
        
        # GPA和院校背景评分分布（用于散点图）
        scatter_data = uni_data[['gpa_percentile', 'source_university_tier_score']].dropna()
        scatter_points = []
        if len(scatter_data) > 0:
            # 随机采样最多100个点以减少数据量
            if len(scatter_data) > 100:
                scatter_sample = scatter_data.sample(n=100, random_state=42)
            else:
                scatter_sample = scatter_data
            
            for _, row in scatter_sample.iterrows():
                scatter_points.append({
                    'gpa': round(float(row['gpa_percentile']), 1),
                    'university_score': round(float(row['source_university_tier_score']), 1)
                })
        
        # 关键统计指标
        key_indicators = {
            'ratio_985': round((uni_data['source_is_985'] == 1).mean() * 100, 1),
            'ratio_211': round((uni_data['source_is_211'] == 1).mean() * 100, 1),
            'ratio_work_experience': round((uni_data['has_work_experience'] == 1).mean() * 100, 1),
            'avg_gpa': round(float(uni_data['gpa_percentile'].mean()), 1) if not uni_data['gpa_percentile'].isna().all() else None,
            'target_university_tier': uni_data['target_university_tier_desc'].iloc[0] if len(uni_data) > 0 else None,
            'avg_competition_index': round(float(uni_data['competition_index'].mean()), 1) if not uni_data['competition_index'].isna().all() else None
        }
        
        university_group = {
            'university_name': university,
            'application_count': application_count,
            'dimension_stats': stats,
            'scatter_data': scatter_points,
            'key_indicators': key_indicators
        }
        
        university_groups.append(university_group)
    
    print(f"院校分组统计完成，共处理 {len(university_groups)} 个院校")
    return university_groups


def calculate_major_groups(df):
    """
    按目标专业分组统计
    
    Args:
        df (pd.DataFrame): 原始数据集
        
    Returns:
        list: 按目标专业分组的统计数据
    """
    print("正在计算按目标专业分组的统计数据...")
    
    major_groups = []
    
    # 只选择申请量较多的专业（至少30个申请）
    major_counts = df['申请院校_专业名称_标准化'].value_counts()
    popular_majors = major_counts[major_counts >= 30].index.tolist()
    
    for major in popular_majors[:20]:  # 取前20个热门专业
        major_data = df[df['申请院校_专业名称_标准化'] == major].copy()
        
        # 基本信息
        application_count = len(major_data)
        
        # 五个维度的统计（排除缺失值）
        # 专业匹配度需要转换为0-100分制以便与其他维度统一显示
        major_matching_data = major_data['major_matching_score'].dropna() * 100 if 'major_matching_score' in major_data.columns else pd.Series([])
        
        dimensions = {
            'source_university_score': major_data['source_university_tier_score'].dropna(),
            'academic_strength': major_data['academic_strength_score'].dropna(),
            'language_ability': major_data[major_data['has_language_score'] == 1]['language_score_normalized'].dropna(),
            'major_matching': major_matching_data,
            'work_experience': major_data['work_experience_years'].dropna()
        }
        
        # 计算均值和中位数
        stats = {}
        for dim_name, dim_data in dimensions.items():
            if len(dim_data) > 0:
                stats[dim_name] = {
                    'mean': round(float(dim_data.mean()), 1),
                    'median': round(float(dim_data.median()), 1),
                    'count': int(len(dim_data))
                }
            else:
                stats[dim_name] = {'mean': None, 'median': None, 'count': 0}
        
        # 关键统计指标
        key_indicators = {
            'ratio_985': round((major_data['source_is_985'] == 1).mean() * 100, 1),
            'ratio_211': round((major_data['source_is_211'] == 1).mean() * 100, 1),
            'ratio_work_experience': round((major_data['has_work_experience'] == 1).mean() * 100, 1),
            'avg_gpa': round(float(major_data['gpa_percentile'].mean()), 1) if not major_data['gpa_percentile'].isna().all() else None,
            'avg_competition_index': round(float(major_data['competition_index'].mean()), 1) if not major_data['competition_index'].isna().all() else None
        }
        
        major_group = {
            'major_name': major,
            'application_count': application_count,
            'dimension_stats': stats,
            'key_indicators': key_indicators
        }
        
        major_groups.append(major_group)
    
    print(f"专业分组统计完成，共处理 {len(major_groups)} 个专业")
    return major_groups


def calculate_global_distributions(df):
    """
    计算全体数据的分布统计
    
    Args:
        df (pd.DataFrame): 原始数据集
        
    Returns:
        dict: 全体分布统计数据
    """
    print("正在计算全体数据分布统计...")
    
    distributions = {}
    
    # 院校层次分布
    university_tier_dist = df['source_university_tier_desc'].value_counts().to_dict()
    distributions['university_tier_distribution'] = [
        {'tier': k, 'count': int(v)} for k, v in university_tier_dist.items()
    ]
    
    # 专业TOP10
    major_top10 = df['申请院校_专业名称_标准化'].value_counts().head(10).to_dict()
    distributions['major_top10'] = [
        {'major': k, 'count': int(v)} for k, v in major_top10.items()
    ]
    
    # GPA分布（分区间统计）
    gpa_data = df['gpa_percentile'].dropna()
    if len(gpa_data) > 0:
        gpa_bins = [0, 60, 70, 80, 85, 90, 95, 100]
        gpa_labels = ['<60', '60-70', '70-80', '80-85', '85-90', '90-95', '95-100']
        gpa_dist = pd.cut(gpa_data, bins=gpa_bins, labels=gpa_labels, include_lowest=True).value_counts()
        distributions['gpa_distribution'] = [
            {'range': str(k), 'count': int(v)} for k, v in gpa_dist.items()
        ]
    else:
        distributions['gpa_distribution'] = []
    
    # 目标院校层次分布
    target_tier_dist = df['target_university_tier_desc'].value_counts().to_dict()
    distributions['target_university_tier_distribution'] = [
        {'tier': k, 'count': int(v)} for k, v in target_tier_dist.items()
    ]
    
    # 语言考试类型分布
    language_type_dist = df[df['has_language_score'] == 1]['language_test_type'].value_counts().to_dict()
    distributions['language_test_type_distribution'] = [
        {'type': k, 'count': int(v)} for k, v in language_type_dist.items()
    ]
    
    # 申请年份分布
    year_dist = df['application_year'].value_counts().sort_index().to_dict()
    distributions['application_year_distribution'] = [
        {'year': int(k), 'count': int(v)} for k, v in year_dist.items()
    ]
    
    # 专业匹配度等级分布
    if 'major_matching_level' in df.columns:
        matching_level_dist = df['major_matching_level'].value_counts().to_dict()
        distributions['major_matching_level_distribution'] = [
            {'level': k, 'count': int(v)} for k, v in matching_level_dist.items()
        ]
    
    # 专业匹配度分数分布（分区间）
    if 'major_matching_score' in df.columns:
        matching_score_data = df['major_matching_score'].dropna()
        if len(matching_score_data) > 0:
            score_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
            score_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
            score_dist = pd.cut(matching_score_data, bins=score_bins, labels=score_labels, include_lowest=True).value_counts()
            distributions['major_matching_score_distribution'] = [
                {'range': str(k), 'count': int(v)} for k, v in score_dist.items()
            ]
        else:
            distributions['major_matching_score_distribution'] = []
    
    # 跨专业类型分布
    if 'cross_major_type' in df.columns:
        cross_type_dist = df['cross_major_type'].value_counts().to_dict()
        distributions['cross_major_type_distribution'] = [
            {'type': k, 'count': int(v)} for k, v in cross_type_dist.items()
        ]
    
    print("全体数据分布统计完成")
    return distributions


def main():
    """
    主函数：执行数据聚合和JSON生成
    """
    print("开始准备数据看板聚合数据...")
    print("=" * 50)
    
    # 文件路径 - 使用包含专业匹配度特征的最新数据集
    input_file = 'data/processed/final_feature_dataset_latest.csv'
    output_file = 'dashboard/data.json'
    
    try:
        # 1. 加载数据
        df = load_data(input_file)
        
        # 2. 计算总体概览指标
        overview = calculate_overview_metrics(df)
        
        # 3. 计算按院校分组统计
        university_groups = calculate_university_groups(df)
        
        # 4. 计算按专业分组统计
        major_groups = calculate_major_groups(df)
        
        # 5. 计算全体分布统计
        distributions = calculate_global_distributions(df)
        
        # 6. 汇总所有数据
        dashboard_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': len(df),
                'data_source': input_file,
                'version': '1.0'
            },
            'overview': overview,
            'university_groups': university_groups,
            'major_groups': major_groups,
            'distributions': distributions
        }
        
        # 7. 保存JSON文件
        print(f"正在保存聚合数据到: {output_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        print("=" * 50)
        print("数据看板聚合数据准备完成！")
        print(f"输出文件: {output_file}")
        print(f"数据概览:")
        print(f"  - 总申请记录数: {dashboard_data['metadata']['total_records']:,}")
        print(f"  - 处理的院校数: {len(university_groups)}")
        print(f"  - 处理的专业数: {len(major_groups)}")
        print(f"  - 生成时间: {dashboard_data['metadata']['generated_at']}")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        raise


if __name__ == '__main__':
    main()