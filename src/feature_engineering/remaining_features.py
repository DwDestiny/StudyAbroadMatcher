#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合特征工程模块 - 处理剩余的高级特征
=====================================

本模块实现以下功能：
1. 学术实力综合特征
2. 语言能力标准化特征  
3. 工作经验量化特征
4. 申请竞争度特征
5. 时间序列特征

作者: Claude
日期: 2025-08-15
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class RemainingFeaturesProcessor:
    """剩余特征处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 语言考试类型映射
        self.language_test_mapping = {
            'IELTS': 'IELTS',
            'TOEFL': 'TOEFL', 
            'PTE': 'PTE',
            'GMAT': 'GMAT',
            'GRE': 'GRE'
        }
        
        # 专业相关性关键词
        self.major_keywords = {
            'business': ['business', 'management', 'finance', 'economics', 'accounting', 'marketing'],
            'engineering': ['engineering', 'computer', 'software', 'mechanical', 'electrical', 'civil'],
            'science': ['science', 'biology', 'chemistry', 'physics', 'mathematics', 'statistics'],
            'humanities': ['english', 'literature', 'history', 'philosophy', 'linguistics', 'language'],
            'social_science': ['psychology', 'sociology', 'political', 'international', 'social'],
            'education': ['education', 'teaching', 'tesol', 'pedagogy'],
            'arts': ['art', 'design', 'music', 'media', 'film', 'creative'],
            'medicine': ['medicine', 'medical', 'health', 'nursing', 'pharmacy'],
            'law': ['law', 'legal', 'justice']
        }
        
    def process_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """批量处理所有剩余特征"""
        print("开始批量处理剩余特征...")
        
        # 创建数据副本
        df_processed = df.copy()
        
        # 1. 学术实力综合特征
        print("1. 处理学术实力综合特征...")
        df_processed = self._add_academic_strength_features(df_processed)
        
        # 2. 语言能力标准化特征
        print("2. 处理语言能力标准化特征...")
        df_processed = self._add_language_features(df_processed)
        
        # 3. 工作经验量化特征
        print("3. 处理工作经验量化特征...")
        df_processed = self._add_work_experience_features(df_processed)
        
        # 4. 申请竞争度特征
        print("4. 处理申请竞争度特征...")
        df_processed = self._add_competition_features(df_processed)
        
        # 5. 时间序列特征
        print("5. 处理时间序列特征...")
        df_processed = self._add_time_series_features(df_processed)
        
        print("所有特征处理完成！")
        return df_processed
    
    def _add_academic_strength_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加学术实力综合特征"""
        
        # GPA百分制分数（已存在，确保完整性）
        if '教育经历_GPA成绩_百分制_修复' in df.columns:
            df['gpa_percentile'] = df['教育经历_GPA成绩_百分制_修复']
        else:
            df['gpa_percentile'] = self._standardize_gpa(df['教育经历_GPA成绩'])
        
        # GPA相对排名（同背景学生中的位置）
        df['gpa_relative_rank'] = df.groupby(['source_university_tier', '教育经历_学历层次_标准化'])['gpa_percentile'].rank(pct=True)
        
        # 综合学术实力评分（0-100）
        df['academic_strength_score'] = self._calculate_academic_strength(df)
        
        return df
    
    def _add_language_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加语言能力标准化特征"""
        
        # 是否有语言成绩
        df['has_language_score'] = df['语言考试_考试成绩'].notna().astype(int)
        
        # 语言考试类型
        df['language_test_type'] = df['语言考试_考试类型'].apply(self._extract_test_type)
        
        # 标准化语言成绩（0-100）
        df['language_score_normalized'] = df.apply(self._normalize_language_score, axis=1)
        
        return df
    
    def _add_work_experience_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加工作经验量化特征"""
        
        # 是否有工作经验
        df['has_work_experience'] = (~df['工作经历_工作单位'].isin(['无工作经验', '无', '', np.nan])).astype(int)
        
        # 工作年限
        df['work_experience_years'] = df.apply(self._calculate_work_years, axis=1)
        
        # 工作相关度（基于专业匹配）
        df['work_relevance_score'] = df.apply(self._calculate_work_relevance, axis=1)
        
        return df
    
    def _add_competition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加申请竞争度特征"""
        
        # 目标院校竞争度（基于申请量和排名）
        df['target_university_competition'] = self._calculate_university_competition(df)
        
        # 目标专业热门度
        df['target_major_popularity'] = self._calculate_major_popularity(df)
        
        # 竞争等级分类
        df['competition_level_new'] = df.apply(self._classify_competition_level, axis=1)
        
        return df
    
    def _add_time_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加时间序列特征"""
        
        # 申请年份
        df['application_year'] = df['语言考试_考试时间'].apply(self._extract_year)
        
        # 申请季节
        df['application_season'] = df['语言考试_考试时间'].apply(self._extract_season)
        
        # 距离毕业时间（月）
        df['time_to_graduation'] = df.apply(self._calculate_time_to_graduation, axis=1)
        
        return df
    
    def _standardize_gpa(self, gpa_series: pd.Series) -> pd.Series:
        """标准化GPA成绩为百分制"""
        def convert_gpa(gpa_str):
            if pd.isna(gpa_str):
                return np.nan
            
            gpa_str = str(gpa_str).strip()
            
            # 匹配百分制 (如 85/100, 85)
            if '/100' in gpa_str:
                try:
                    return float(gpa_str.split('/100')[0])
                except:
                    return np.nan
            
            # 匹配4分制 (如 3.5/4)
            if '/4' in gpa_str:
                try:
                    score = float(gpa_str.split('/4')[0])
                    return score * 25  # 转换为百分制
                except:
                    return np.nan
            
            # 匹配5分制 (如 4.2/5)
            if '/5' in gpa_str:
                try:
                    score = float(gpa_str.split('/5')[0])
                    return score * 20  # 转换为百分制
                except:
                    return np.nan
            
            # 纯数字，判断范围
            try:
                score = float(gpa_str)
                if score <= 5:
                    return score * 20  # 5分制
                elif score <= 4:
                    return score * 25  # 4分制
                elif score <= 100:
                    return score  # 百分制
                else:
                    return np.nan
            except:
                return np.nan
        
        return gpa_series.apply(convert_gpa)
    
    def _calculate_academic_strength(self, df: pd.DataFrame) -> pd.Series:
        """计算综合学术实力评分"""
        # 基础GPA分数（权重50%）
        gpa_score = df['gpa_percentile'].fillna(df['gpa_percentile'].median())
        
        # 院校层次分数（权重30%）
        university_score = df['source_university_tier_score'].fillna(60)
        
        # 学历层次分数（权重20%）
        education_score = df['教育经历_学历层次_标准化'].map({
            '博士': 100,
            '硕士': 85,
            '本科': 70,
            '专科': 50
        }).fillna(70)
        
        # 综合评分
        academic_strength = (
            gpa_score * 0.5 + 
            university_score * 0.3 + 
            education_score * 0.2
        )
        
        return academic_strength.round(1)
    
    def _extract_test_type(self, test_info: str) -> str:
        """提取语言考试类型"""
        if pd.isna(test_info):
            return 'Unknown'
        
        test_info = str(test_info).upper()
        
        for test_type in self.language_test_mapping.keys():
            if test_type in test_info:
                return test_type
        
        return 'Other'
    
    def _normalize_language_score(self, row: pd.Series) -> float:
        """标准化语言成绩到0-100分"""
        if pd.isna(row['语言考试_考试成绩']):
            return np.nan
        
        score_str = str(row['语言考试_考试成绩']).strip()
        test_type = row.get('language_test_type', 'Unknown')
        
        # 提取数字分数
        numbers = re.findall(r'\d+\.?\d*', score_str)
        if not numbers:
            return np.nan
        
        try:
            score = float(numbers[0])
        except:
            return np.nan
        
        # 根据考试类型标准化
        if test_type == 'IELTS':
            # IELTS: 0-9分 -> 0-100
            return min(score / 9 * 100, 100)
        elif test_type == 'TOEFL':
            # TOEFL: 0-120分 -> 0-100
            return min(score / 120 * 100, 100)
        elif test_type == 'PTE':
            # PTE: 0-90分 -> 0-100
            return min(score / 90 * 100, 100)
        elif test_type in ['GMAT', 'GRE']:
            # GMAT/GRE 已经是较高分数，保持原值或按比例
            if score > 800:
                return min(score / 800 * 100, 100)
            else:
                return min(score / 340 * 100, 100)  # GRE范围
        else:
            # 默认处理：假设已经是百分制或接近
            if score <= 10:
                return score * 10  # 可能是10分制
            elif score <= 100:
                return score  # 已经是百分制
            else:
                return min(score / 120 * 100, 100)  # 按TOEFL处理
    
    def _calculate_work_years(self, row: pd.Series) -> float:
        """计算工作年限"""
        if pd.isna(row['工作经历_开始时间']) or pd.isna(row['工作经历_结束时间']):
            return 0.0
        
        if row['工作经历_工作单位'] in ['无工作经验', '无', '']:
            return 0.0
        
        try:
            start_date = pd.to_datetime(row['工作经历_开始时间'])
            end_date = pd.to_datetime(row['工作经历_结束时间'])
            
            # 计算年数差
            years = (end_date - start_date).days / 365.25
            return max(0, round(years, 1))
        except:
            return 0.0
    
    def _calculate_work_relevance(self, row: pd.Series) -> float:
        """计算工作相关度（0-1）"""
        if row.get('has_work_experience', 0) == 0:
            return 0.0
        
        # 获取目标专业和工作职责
        target_major = str(row.get('申请院校_专业名称_标准化', '')).lower()
        job_title = str(row.get('工作经历_职位名称', '')).lower()
        job_desc = str(row.get('工作经历_工作职责', '')).lower()
        
        work_text = f"{job_title} {job_desc}"
        
        # 计算专业相关度
        max_relevance = 0.0
        
        for category, keywords in self.major_keywords.items():
            # 检查目标专业是否属于此类别
            major_match = any(keyword in target_major for keyword in keywords)
            
            if major_match:
                # 检查工作内容匹配度
                work_matches = sum(1 for keyword in keywords if keyword in work_text)
                relevance = min(work_matches / len(keywords), 1.0)
                max_relevance = max(max_relevance, relevance)
        
        return round(max_relevance, 2)
    
    def _calculate_university_competition(self, df: pd.DataFrame) -> pd.Series:
        """计算目标院校竞争度"""
        # 基于现有的竞争度字段，如果存在的话
        if 'target_university_competitiveness' in df.columns:
            return df['target_university_competitiveness']
        
        # 否则基于QS排名和申请量计算
        competition = pd.Series(index=df.index, dtype=float)
        
        for idx, row in df.iterrows():
            qs_rank = row.get('target_university_qs_rank', 999)
            app_volume = row.get('target_university_application_volume', 1)
            
            # 排名越高（数值越小）竞争度越高
            rank_score = max(0, (1000 - min(qs_rank, 999)) / 1000 * 100)
            
            # 申请量越大竞争度越高
            volume_score = min(app_volume / 10000 * 100, 100)
            
            # 综合竞争度
            competition[idx] = (rank_score * 0.7 + volume_score * 0.3)
        
        return competition.round(1)
    
    def _calculate_major_popularity(self, df: pd.DataFrame) -> pd.Series:
        """计算目标专业热门度"""
        # 基于专业申请频次计算热门度
        major_counts = df['申请院校_专业名称_标准化'].value_counts()
        total_applications = len(df)
        
        popularity = df['申请院校_专业名称_标准化'].map(
            lambda x: (major_counts.get(x, 0) / total_applications * 100)
        ).round(2)
        
        return popularity
    
    def _classify_competition_level(self, row: pd.Series) -> str:
        """分类竞争等级"""
        competition = row.get('target_university_competition', 0)
        popularity = row.get('target_major_popularity', 0)
        
        # 综合竞争指数
        combined_index = competition * 0.6 + popularity * 0.4
        
        if combined_index >= 80:
            return '极高竞争'
        elif combined_index >= 60:
            return '高竞争'
        elif combined_index >= 40:
            return '中等竞争'
        elif combined_index >= 20:
            return '低竞争'
        else:
            return '极低竞争'
    
    def _extract_year(self, date_str: str) -> int:
        """提取年份"""
        if pd.isna(date_str):
            return 2023  # 默认年份
        
        try:
            # 尝试多种日期格式
            date_obj = pd.to_datetime(date_str)
            return date_obj.year
        except:
            # 尝试从字符串中提取年份
            years = re.findall(r'20\d{2}', str(date_str))
            if years:
                return int(years[0])
            return 2023
    
    def _extract_season(self, date_str: str) -> str:
        """提取申请季节"""
        if pd.isna(date_str):
            return 'Unknown'
        
        try:
            date_obj = pd.to_datetime(date_str)
            month = date_obj.month
            
            if month in [12, 1, 2]:
                return 'Winter'
            elif month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            elif month in [9, 10, 11]:
                return 'Fall'
        except:
            pass
        
        return 'Unknown'
    
    def _calculate_time_to_graduation(self, row: pd.Series) -> float:
        """计算距离毕业时间（月）"""
        if pd.isna(row['教育经历_毕业时间']) or pd.isna(row['语言考试_考试时间']):
            return np.nan
        
        try:
            grad_date = pd.to_datetime(row['教育经历_毕业时间'])
            test_date = pd.to_datetime(row['语言考试_考试时间'])
            
            # 计算月份差
            months_diff = (grad_date - test_date).days / 30.44  # 平均每月天数
            return round(months_diff, 1)
        except:
            return np.nan
    
    def generate_feature_summary(self, df: pd.DataFrame) -> Dict:
        """生成特征摘要报告"""
        summary = {
            'total_records': len(df),
            'new_features': [],
            'feature_statistics': {}
        }
        
        # 新增的特征列
        new_features = [
            'gpa_percentile', 'gpa_relative_rank', 'academic_strength_score',
            'has_language_score', 'language_test_type', 'language_score_normalized',
            'has_work_experience', 'work_experience_years', 'work_relevance_score',
            'target_university_competition', 'target_major_popularity', 'competition_level_new',
            'application_year', 'application_season', 'time_to_graduation'
        ]
        
        for feature in new_features:
            if feature in df.columns:
                summary['new_features'].append(feature)
                
                # 基础统计
                if df[feature].dtype in ['int64', 'float64']:
                    stats = {
                        'type': 'numeric',
                        'count': df[feature].count(),
                        'mean': round(df[feature].mean(), 2) if df[feature].count() > 0 else None,
                        'std': round(df[feature].std(), 2) if df[feature].count() > 0 else None,
                        'min': df[feature].min(),
                        'max': df[feature].max(),
                        'missing_rate': round(df[feature].isna().mean() * 100, 2)
                    }
                else:
                    stats = {
                        'type': 'categorical',
                        'count': df[feature].count(),
                        'unique_values': df[feature].nunique(),
                        'top_values': df[feature].value_counts().head(3).to_dict(),
                        'missing_rate': round(df[feature].isna().mean() * 100, 2)
                    }
                
                summary['feature_statistics'][feature] = stats
        
        return summary


def main():
    """主函数：批量处理所有剩余特征"""
    # 读取数据
    input_file = 'data/processed/cleaned_offer_data_with_comprehensive_university_features.csv'
    output_file = f'data/processed/data_with_all_features_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print(f"读取数据: {input_file}")
    df = pd.read_csv(input_file)
    print(f"原始数据形状: {df.shape}")
    
    # 初始化处理器
    processor = RemainingFeaturesProcessor()
    
    # 批量处理所有特征
    df_enhanced = processor.process_all_features(df)
    
    # 保存处理后的数据
    df_enhanced.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"增强数据已保存: {output_file}")
    print(f"处理后数据形状: {df_enhanced.shape}")
    
    # 生成特征摘要
    summary = processor.generate_feature_summary(df_enhanced)
    
    print("\n=== 特征处理摘要 ===")
    print(f"总记录数: {summary['total_records']:,}")
    print(f"新增特征数: {len(summary['new_features'])}")
    print(f"新增特征: {', '.join(summary['new_features'])}")
    
    print("\n=== 特征统计 ===")
    for feature, stats in summary['feature_statistics'].items():
        print(f"\n{feature}:")
        if stats['type'] == 'numeric':
            print(f"  类型: 数值型 | 有效值: {stats['count']:,} | 缺失率: {stats['missing_rate']}%")
            if stats['mean'] is not None:
                print(f"  均值: {stats['mean']} | 标准差: {stats['std']} | 范围: [{stats['min']}, {stats['max']}]")
        else:
            print(f"  类型: 分类型 | 有效值: {stats['count']:,} | 唯一值: {stats['unique_values']} | 缺失率: {stats['missing_rate']}%")
            print(f"  热门值: {stats['top_values']}")
    
    return df_enhanced, summary


if __name__ == "__main__":
    df_result, summary_result = main()