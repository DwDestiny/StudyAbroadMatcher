#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业匹配度特征集成脚本
将专业匹配度特征合并到最终特征数据集中
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

def integrate_major_matching_features():
    """整合专业匹配度特征到最终数据集"""
    
    print("=== 开始集成专业匹配度特征 ===")
    
    # 读取当前最终数据集
    final_data_path = "data/processed/final_feature_dataset_20250815_153405.csv"
    print(f"读取最终数据集: {final_data_path}")
    df_final = pd.read_csv(final_data_path, encoding='utf-8-sig')
    print(f"最终数据集: {len(df_final)}行 {len(df_final.columns)}列")
    
    # 读取专业匹配度特征数据
    matching_data_path = "data/processed/data_with_major_matching_features_20250815_141023.csv"
    print(f"读取专业匹配度特征数据: {matching_data_path}")
    df_matching = pd.read_csv(matching_data_path, encoding='utf-8')
    print(f"专业匹配度数据集: {len(df_matching)}行 {len(df_matching.columns)}列")
    
    # 确定合并的键值
    # 使用多个字段组合作为唯一标识符
    key_columns = ['申请院校_院校ID', '申请院校_专业ID', '教育经历_毕业院校', 
                  '教育经历_所学专业', '教育经历_GPA成绩']
    
    print(f"使用合并键: {key_columns}")
    
    # 检查键值的唯一性
    final_keys = df_final[key_columns].drop_duplicates()
    matching_keys = df_matching[key_columns].drop_duplicates()
    print(f"最终数据集唯一键: {len(final_keys)}")
    print(f"匹配数据集唯一键: {len(matching_keys)}")
    
    # 提取专业匹配度特征列
    matching_feature_columns = [
        'major_matching_score', 'cross_major_type', 'major_matching_description',
        'is_same_field', 'major_matching_level'
    ]
    
    # 检查专业分类列是否存在
    classification_columns = []
    potential_class_columns = ['申请专业主分类', '申请专业子分类', '申请专业分类置信度', 
                              '教育专业主分类', '教育专业子分类', '教育专业分类置信度']
    for col in potential_class_columns:
        if col in df_matching.columns:
            classification_columns.append(col)
    
    all_matching_columns = key_columns + matching_feature_columns + classification_columns
    
    print(f"专业匹配度特征列: {matching_feature_columns}")
    print(f"专业分类列: {classification_columns}")
    
    # 准备合并数据
    df_matching_subset = df_matching[all_matching_columns].copy()
    
    # 合并数据集
    print("开始合并数据集...")
    df_integrated = pd.merge(
        df_final, 
        df_matching_subset, 
        on=key_columns, 
        how='left',
        suffixes=('', '_matching')
    )
    
    print(f"合并后数据集: {len(df_integrated)}行 {len(df_integrated.columns)}列")
    
    # 检查合并结果
    missing_matching = df_integrated['major_matching_score'].isnull().sum()
    print(f"缺失专业匹配度的记录: {missing_matching} ({missing_matching/len(df_integrated)*100:.1f}%)")
    
    if missing_matching > 0:
        print("为缺失的专业匹配度记录填充默认值...")
        df_integrated['major_matching_score'].fillna(0.2, inplace=True)
        df_integrated['cross_major_type'].fillna('unknown', inplace=True)
        df_integrated['major_matching_description'].fillna('信息不完整', inplace=True)
        df_integrated['is_same_field'].fillna(0, inplace=True)
        df_integrated['major_matching_level'].fillna('不匹配', inplace=True)
        
        for col in classification_columns:
            if col in df_integrated.columns:
                if '置信度' in col:
                    df_integrated[col].fillna(0.0, inplace=True)
                else:
                    df_integrated[col].fillna('未知', inplace=True)
    
    # 验证数据质量
    print("\n=== 数据质量验证 ===")
    print(f"专业匹配度分布:")
    print(df_integrated['major_matching_level'].value_counts())
    print(f"\n平均专业匹配度: {df_integrated['major_matching_score'].mean():.3f}")
    print(f"同领域申请比例: {df_integrated['is_same_field'].mean():.1%}")
    
    # 保存整合后的数据集
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/processed/final_feature_dataset_with_major_matching_{timestamp}.csv"
    
    df_integrated.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n完整特征数据集已保存到: {output_path}")
    
    # 更新为最新的最终数据集
    latest_final_path = "data/processed/final_feature_dataset_latest.csv"
    df_integrated.to_csv(latest_final_path, index=False, encoding='utf-8-sig')
    print(f"最新数据集副本: {latest_final_path}")
    
    print("\n=== 集成完成 ===")
    return df_integrated, output_path

def main():
    """主函数"""
    try:
        df_integrated, output_path = integrate_major_matching_features()
        return df_integrated, output_path
    except Exception as e:
        print(f"集成过程中出现错误: {str(e)}")
        raise

if __name__ == "__main__":
    df_integrated, output_path = main()