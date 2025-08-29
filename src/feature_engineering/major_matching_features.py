#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业匹配度特征工程模块
基于专业分类体系计算申请专业与教育背景专业的匹配度
生成专业匹配度相关特征用于后续分析和建模

匹配度评分规则：
- 完全匹配（1.0）：同专业直升
- 高度相关（0.8）：同领域细分专业
- 相关匹配（0.6）：同一级分类内
- 合理跨领域（0.4）：有逻辑关联
- 完全跨领域（0.2）：无关联
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MajorMatchingFeatures:
    """专业匹配度特征工程器"""
    
    def __init__(self):
        """初始化匹配规则"""
        self.matching_rules = self._build_matching_rules()
        self.cross_field_relationships = self._build_cross_field_relationships()
        
    def _build_matching_rules(self) -> Dict:
        """构建专业匹配规则"""
        return {
            # 完全匹配（1.0）：同专业直升
            'exact_match': {
                'score': 1.0,
                'description': '完全匹配',
                'criteria': 'same_major_name'
            },
            
            # 高度相关（0.8）：同领域细分专业
            'highly_related': {
                'score': 0.8,
                'description': '高度相关',
                'criteria': 'same_subcategory'
            },
            
            # 相关匹配（0.6）：同一级分类内
            'related': {
                'score': 0.6,
                'description': '相关匹配',
                'criteria': 'same_main_category'
            },
            
            # 合理跨领域（0.4）：有逻辑关联
            'reasonable_cross': {
                'score': 0.4,
                'description': '合理跨领域',
                'criteria': 'logical_relationship'
            },
            
            # 完全跨领域（0.2）：无关联
            'completely_cross': {
                'score': 0.2,
                'description': '完全跨领域',
                'criteria': 'no_relationship'
            }
        }
    
    def _build_cross_field_relationships(self) -> Dict:
        """构建跨领域逻辑关联关系"""
        return {
            # 商科可以接受的背景
            '商科': {
                'highly_compatible': ['商科'],  # 高度兼容
                'moderately_compatible': ['工科', '理科', '法学'],  # 中度兼容
                'low_compatible': ['文科', '艺术'],  # 低度兼容
                'incompatible': ['医学']  # 不兼容
            },
            
            # 工科可以接受的背景
            '工科': {
                'highly_compatible': ['工科', '理科'],
                'moderately_compatible': ['商科'],
                'low_compatible': ['文科'],
                'incompatible': ['法学', '艺术', '医学']
            },
            
            # 理科可以接受的背景
            '理科': {
                'highly_compatible': ['理科', '工科'],
                'moderately_compatible': ['商科', '医学'],
                'low_compatible': ['文科'],
                'incompatible': ['法学', '艺术']
            },
            
            # 文科可以接受的背景
            '文科': {
                'highly_compatible': ['文科'],
                'moderately_compatible': ['商科', '法学', '艺术'],
                'low_compatible': ['理科'],
                'incompatible': ['工科', '医学']
            },
            
            # 法学可以接受的背景
            '法学': {
                'highly_compatible': ['法学'],
                'moderately_compatible': ['商科', '文科'],
                'low_compatible': ['理科'],
                'incompatible': ['工科', '艺术', '医学']
            },
            
            # 艺术可以接受的背景
            '艺术': {
                'highly_compatible': ['艺术'],
                'moderately_compatible': ['文科'],
                'low_compatible': ['商科'],
                'incompatible': ['工科', '理科', '法学', '医学']
            },
            
            # 医学可以接受的背景
            '医学': {
                'highly_compatible': ['医学'],
                'moderately_compatible': ['理科'],
                'low_compatible': [],
                'incompatible': ['商科', '工科', '文科', '法学', '艺术']
            }
        }
    
    def _normalize_major_name(self, major_name: str) -> str:
        """标准化专业名称用于比较"""
        if pd.isna(major_name) or not major_name:
            return ''
        
        # 转换为字符串并清理
        major_name = str(major_name).strip().lower()
        
        # 移除常见的学位词汇
        degree_words = ['master', 'bachelor', 'of', 'in', 'and', 'the', '硕士', '学士', '学', '专业']
        words = major_name.split()
        filtered_words = [word for word in words if word not in degree_words]
        
        return ' '.join(filtered_words)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算专业名称相似度"""
        if not name1 or not name2:
            return 0.0
        
        # 标准化名称
        norm_name1 = self._normalize_major_name(name1)
        norm_name2 = self._normalize_major_name(name2)
        
        if not norm_name1 or not norm_name2:
            return 0.0
        
        # 完全匹配
        if norm_name1 == norm_name2:
            return 1.0
        
        # 包含关系
        if norm_name1 in norm_name2 or norm_name2 in norm_name1:
            return 0.8
        
        # 计算词汇重叠率
        words1 = set(norm_name1.split())
        words2 = set(norm_name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def calculate_major_matching_score(self, 
                                     target_main_category: str, 
                                     target_sub_category: str,
                                     target_major_name: str,
                                     education_main_category: str, 
                                     education_sub_category: str,
                                     education_major_name: str) -> Tuple[float, str, str]:
        """
        计算专业匹配度分数
        
        Args:
            target_main_category: 申请专业主分类
            target_sub_category: 申请专业子分类
            target_major_name: 申请专业名称
            education_main_category: 教育专业主分类
            education_sub_category: 教育专业子分类
            education_major_name: 教育专业名称
        
        Returns:
            (匹配度分数, 匹配类型, 匹配描述)
        """
        
        # 处理缺失值
        target_main = str(target_main_category) if pd.notna(target_main_category) else '未知'
        target_sub = str(target_sub_category) if pd.notna(target_sub_category) else '未知'
        target_name = str(target_major_name) if pd.notna(target_major_name) else ''
        
        education_main = str(education_main_category) if pd.notna(education_main_category) else '未知'
        education_sub = str(education_sub_category) if pd.notna(education_sub_category) else '未知'
        education_name = str(education_major_name) if pd.notna(education_major_name) else ''
        
        # 如果任一分类为未知，返回最低分
        if target_main == '未知' or education_main == '未知':
            return 0.2, 'completely_cross', '信息不完整'
        
        # 1. 完全匹配：专业名称高度相似
        name_similarity = self._calculate_name_similarity(target_name, education_name)
        if name_similarity >= 0.8:
            return 1.0, 'exact_match', '专业名称高度相似'
        
        # 2. 高度相关：同子分类
        if target_main == education_main and target_sub == education_sub:
            return 0.8, 'highly_related', '同领域细分专业'
        
        # 3. 相关匹配：同主分类
        if target_main == education_main:
            return 0.6, 'related', '同一级分类内'
        
        # 4. 合理跨领域：有逻辑关联
        if target_main in self.cross_field_relationships:
            relationships = self.cross_field_relationships[target_main]
            
            if education_main in relationships.get('highly_compatible', []):
                return 0.5, 'reasonable_cross', '高度兼容的跨领域'
            elif education_main in relationships.get('moderately_compatible', []):
                return 0.4, 'reasonable_cross', '中度兼容的跨领域'
            elif education_main in relationships.get('low_compatible', []):
                return 0.3, 'reasonable_cross', '低度兼容的跨领域'
        
        # 5. 完全跨领域：无关联
        return 0.2, 'completely_cross', '完全不相关领域'
    
    def generate_major_matching_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为数据框生成专业匹配度特征
        
        Args:
            df: 包含专业分类信息的数据框
        
        Returns:
            添加了匹配度特征的数据框
        """
        df_result = df.copy()
        
        # 计算每条记录的专业匹配度
        matching_results = []
        for idx, row in df_result.iterrows():
            score, match_type, description = self.calculate_major_matching_score(
                row.get('申请专业主分类', ''),
                row.get('申请专业子分类', ''),
                row.get('申请院校_专业名称', ''),
                row.get('教育专业主分类', ''),
                row.get('教育专业子分类', ''),
                row.get('教育经历_所学专业', '')
            )
            matching_results.append((score, match_type, description))
        
        # 添加匹配度特征
        df_result['major_matching_score'] = [r[0] for r in matching_results]
        df_result['cross_major_type'] = [r[1] for r in matching_results]
        df_result['major_matching_description'] = [r[2] for r in matching_results]
        
        # 生成二分类特征：是否同领域
        df_result['is_same_field'] = (df_result['申请专业主分类'] == df_result['教育专业主分类']).astype(int)
        
        # 生成匹配度等级
        def get_matching_level(score):
            if score >= 0.8:
                return '高匹配度'
            elif score >= 0.6:
                return '中等匹配度'
            elif score >= 0.4:
                return '低匹配度'
            else:
                return '不匹配'
        
        df_result['major_matching_level'] = df_result['major_matching_score'].apply(get_matching_level)
        
        logger.info(f"专业匹配度特征生成完成，处理了 {len(df_result)} 条记录")
        return df_result
    
    def analyze_major_matching_distribution(self, df: pd.DataFrame) -> Dict:
        """分析专业匹配度分布"""
        if 'major_matching_score' not in df.columns:
            return {"error": "数据中未找到专业匹配度特征"}
        
        analysis = {}
        
        # 基本统计
        analysis['basic_stats'] = {
            '记录总数': len(df),
            '平均匹配度': df['major_matching_score'].mean(),
            '匹配度标准差': df['major_matching_score'].std(),
            '最高匹配度': df['major_matching_score'].max(),
            '最低匹配度': df['major_matching_score'].min()
        }
        
        # 匹配度等级分布
        if 'major_matching_level' in df.columns:
            analysis['matching_level_distribution'] = df['major_matching_level'].value_counts().to_dict()
        
        # 跨专业类型分布
        if 'cross_major_type' in df.columns:
            analysis['cross_major_type_distribution'] = df['cross_major_type'].value_counts().to_dict()
        
        # 同领域比例
        if 'is_same_field' in df.columns:
            same_field_ratio = df['is_same_field'].mean()
            analysis['same_field_ratio'] = same_field_ratio
            analysis['cross_field_ratio'] = 1 - same_field_ratio
        
        # 主分类匹配度分布
        if '申请专业主分类' in df.columns:
            category_matching = df.groupby('申请专业主分类')['major_matching_score'].agg([
                'count', 'mean', 'std'
            ]).round(3)
            analysis['category_matching_stats'] = category_matching.to_dict()
        
        # 高低匹配度样本
        high_matching = df[df['major_matching_score'] >= 0.8]
        low_matching = df[df['major_matching_score'] <= 0.3]
        
        analysis['high_matching_samples'] = len(high_matching)
        analysis['low_matching_samples'] = len(low_matching)
        
        if len(high_matching) > 0:
            analysis['high_matching_categories'] = high_matching['申请专业主分类'].value_counts().head(5).to_dict()
        
        if len(low_matching) > 0:
            analysis['low_matching_patterns'] = low_matching[['申请专业主分类', '教育专业主分类']].value_counts().head(5).to_dict()
        
        return analysis
    
    def generate_matching_report(self, df: pd.DataFrame, output_dir: str = None) -> str:
        """生成专业匹配度分析报告"""
        
        if output_dir is None:
            output_dir = "E:\\小希\\python脚本\\定校数据支撑方案\\outputs\\reports"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 进行分析
        analysis = self.analyze_major_matching_distribution(df)
        
        # 生成报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"major_matching_analysis_report_{timestamp}.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 专业匹配度分析报告\n\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 基本统计
            f.write("## 1. 基本统计信息\n\n")
            if 'basic_stats' in analysis:
                for key, value in analysis['basic_stats'].items():
                    if isinstance(value, float):
                        f.write(f"- **{key}**: {value:.3f}\n")
                    else:
                        f.write(f"- **{key}**: {value}\n")
            f.write("\n")
            
            # 匹配度等级分布
            f.write("## 2. 匹配度等级分布\n\n")
            if 'matching_level_distribution' in analysis:
                total = sum(analysis['matching_level_distribution'].values())
                f.write("| 匹配度等级 | 数量 | 占比 |\n")
                f.write("|-----------|------|------|\n")
                for level, count in analysis['matching_level_distribution'].items():
                    percentage = (count / total) * 100
                    f.write(f"| {level} | {count} | {percentage:.1f}% |\n")
            f.write("\n")
            
            # 跨专业类型分布
            f.write("## 3. 跨专业类型分布\n\n")
            if 'cross_major_type_distribution' in analysis:
                f.write("| 跨专业类型 | 数量 | 说明 |\n")
                f.write("|-----------|------|------|\n")
                type_descriptions = {
                    'exact_match': '完全匹配',
                    'highly_related': '高度相关',
                    'related': '相关匹配',
                    'reasonable_cross': '合理跨领域',
                    'completely_cross': '完全跨领域'
                }
                for type_name, count in analysis['cross_major_type_distribution'].items():
                    desc = type_descriptions.get(type_name, type_name)
                    f.write(f"| {type_name} | {count} | {desc} |\n")
            f.write("\n")
            
            # 同领域统计
            f.write("## 4. 同领域统计\n\n")
            if 'same_field_ratio' in analysis:
                f.write(f"- **同领域申请比例**: {analysis['same_field_ratio']:.1%}\n")
                f.write(f"- **跨领域申请比例**: {analysis['cross_field_ratio']:.1%}\n")
            f.write("\n")
            
            # 各主分类匹配度统计
            f.write("## 5. 各专业大类匹配度统计\n\n")
            if 'category_matching_stats' in analysis:
                f.write("| 专业大类 | 申请数量 | 平均匹配度 | 匹配度标准差 |\n")
                f.write("|---------|----------|------------|-------------|\n")
                for category in analysis['category_matching_stats']['count'].keys():
                    count = analysis['category_matching_stats']['count'][category]
                    mean_score = analysis['category_matching_stats']['mean'][category]
                    std_score = analysis['category_matching_stats']['std'].get(category, 0)
                    f.write(f"| {category} | {count} | {mean_score:.3f} | {std_score:.3f} |\n")
            f.write("\n")
            
            # 高匹配度案例
            f.write("## 6. 高匹配度案例分析\n\n")
            if 'high_matching_samples' in analysis:
                f.write(f"**高匹配度样本数量**: {analysis['high_matching_samples']} (匹配度≥0.8)\n\n")
                if 'high_matching_categories' in analysis:
                    f.write("**高匹配度专业分布**:\n")
                    for category, count in analysis['high_matching_categories'].items():
                        f.write(f"- {category}: {count}次\n")
            f.write("\n")
            
            # 低匹配度模式
            f.write("## 7. 低匹配度模式分析\n\n")
            if 'low_matching_samples' in analysis:
                f.write(f"**低匹配度样本数量**: {analysis['low_matching_samples']} (匹配度≤0.3)\n\n")
                if 'low_matching_patterns' in analysis:
                    f.write("**常见跨领域模式**:\n")
                    for pattern, count in analysis['low_matching_patterns'].items():
                        edu_cat, target_cat = pattern
                        f.write(f"- {edu_cat} → {target_cat}: {count}次\n")
            f.write("\n")
            
            # 结论与建议
            f.write("## 8. 结论与建议\n\n")
            f.write("### 主要发现\n\n")
            
            if 'basic_stats' in analysis:
                avg_score = analysis['basic_stats']['平均匹配度']
                if avg_score >= 0.7:
                    f.write("- 整体专业匹配度较高，大多数申请者选择了与背景相关的专业\n")
                elif avg_score >= 0.5:
                    f.write("- 整体专业匹配度中等，存在一定比例的跨领域申请\n")
                else:
                    f.write("- 整体专业匹配度较低，跨领域申请比例较高\n")
            
            if 'same_field_ratio' in analysis:
                same_ratio = analysis['same_field_ratio']
                if same_ratio >= 0.7:
                    f.write("- 大部分申请者倾向于在同一专业领域内申请\n")
                elif same_ratio >= 0.5:
                    f.write("- 同领域和跨领域申请比例相对均衡\n")
                else:
                    f.write("- 跨领域申请较为普遍，需要关注背景转换的合理性\n")
            
            f.write("\n### 数据质量建议\n\n")
            f.write("- 对于低匹配度的申请案例，建议人工审核专业分类是否准确\n")
            f.write("- 可以利用专业匹配度特征作为申请成功率预测的重要指标\n")
            f.write("- 建议进一步分析不同匹配度等级下的申请成功率差异\n")
            
        logger.info(f"专业匹配度分析报告已生成：{report_path}")
        return report_path


def main():
    """主函数：演示专业匹配度特征生成"""
    # 读取已分类的数据
    data_path = "E:\\小希\\python脚本\\定校数据支撑方案\\data\\processed\\enhanced_major_classified_data_20250815_140107.csv"
    
    try:
        df = pd.read_csv(data_path, encoding='utf-8')
        logger.info(f"读取数据成功，共 {len(df)} 条记录")
        
        # 创建特征生成器
        feature_generator = MajorMatchingFeatures()
        
        # 生成专业匹配度特征
        df_with_features = feature_generator.generate_major_matching_features(df)
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"E:\\小希\\python脚本\\定校数据支撑方案\\data\\processed\\data_with_major_matching_features_{timestamp}.csv"
        df_with_features.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"带有专业匹配度特征的数据已保存：{output_path}")
        
        # 生成分析报告
        report_path = feature_generator.generate_matching_report(df_with_features)
        
        # 显示基本统计
        print("\n=== 专业匹配度特征生成完成 ===")
        print(f"处理记录数：{len(df_with_features)}")
        print(f"平均匹配度：{df_with_features['major_matching_score'].mean():.3f}")
        print(f"同领域申请比例：{df_with_features['is_same_field'].mean():.1%}")
        print(f"\n匹配度等级分布：")
        print(df_with_features['major_matching_level'].value_counts())
        print(f"\n数据保存路径：{output_path}")
        print(f"报告保存路径：{report_path}")
        
    except Exception as e:
        logger.error(f"处理过程中出现错误：{str(e)}")
        raise


if __name__ == "__main__":
    main()