#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生信息特征化转换器
将原始学生信息自动转换为系统需要的75维标准化特征向量
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class StudentFeatureConverter:
    """学生信息特征化转换器"""
    
    def __init__(self, data_path: str = None):
        """
        初始化转换器
        
        Args:
            data_path: 外部数据文件路径，用于统计参考
        """
        self.data_path = data_path or 'data/external'
        self.university_tier_map = {}
        self.major_classification_map = {}
        self.language_score_stats = {}
        
        # 加载映射数据
        self._load_mapping_data()
    
    def _load_mapping_data(self):
        """加载映射数据"""
        try:
            # 加载院校层次映射
            china_uni_path = os.path.join(self.data_path, 'china_university_tiers.csv')
            if os.path.exists(china_uni_path):
                china_uni_df = pd.read_csv(china_uni_path)
                self.university_tier_map = dict(zip(
                    china_uni_df['院校名称'], 
                    china_uni_df['tier_score']
                ))
            
            # 加载海外院校映射
            overseas_uni_path = os.path.join(self.data_path, 'overseas_university_features.csv')
            if os.path.exists(overseas_uni_path):
                overseas_uni_df = pd.read_csv(overseas_uni_path)
                overseas_tier_map = dict(zip(
                    overseas_uni_df['university_name'],
                    overseas_uni_df['tier_score']
                ))
                self.university_tier_map.update(overseas_tier_map)
                
            print(f"加载院校映射: {len(self.university_tier_map)}所院校")
            
        except Exception as e:
            print(f"加载映射数据时出错: {e}")
            print("将使用默认映射规则")
    
    def convert_raw_student_info(self, raw_student_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始学生信息转换为标准化特征
        
        Args:
            raw_student_info: 原始学生信息字典
            
        Returns:
            标准化特征字典
        """
        features = {}
        
        try:
            # 1. 教育背景特征转换
            features.update(self._convert_education_features(raw_student_info))
            
            # 2. 院校特征转换
            features.update(self._convert_university_features(raw_student_info))
            
            # 3. 语言成绩特征转换
            features.update(self._convert_language_features(raw_student_info))
            
            # 4. 工作经验特征转换
            features.update(self._convert_work_features(raw_student_info))
            
            # 5. 专业匹配度特征转换
            features.update(self._convert_major_matching_features(raw_student_info))
            
            # 6. 学术实力特征转换
            features.update(self._convert_academic_features(raw_student_info))
            
            # 7. 竞争度和其他特征
            features.update(self._convert_other_features(raw_student_info))
            
            return features
            
        except Exception as e:
            print(f"特征转换时出错: {e}")
            return self._get_default_features()
    
    def _convert_education_features(self, student_info: Dict) -> Dict:
        """转换教育背景特征"""
        features = {}
        
        # GPA转换和标准化
        gpa = student_info.get('gpa')
        gpa_scale = student_info.get('gpa_scale', 4.0)  # 默认4.0制
        
        if gpa is not None:
            # 转换为百分制
            if gpa_scale == 4.0:
                gpa_100 = (gpa / 4.0) * 100
            elif gpa_scale == 5.0:
                gpa_100 = (gpa / 5.0) * 100
            elif gpa_scale == 100:
                gpa_100 = gpa
            else:
                gpa_100 = (gpa / gpa_scale) * 100
            
            features['教育经历_GPA成绩_百分制'] = min(100, max(0, gpa_100))
            
            # 计算GPA百分位（基于经验分布）
            features['gpa_percentile'] = self._calculate_gpa_percentile(gpa_100)
        else:
            features['教育经历_GPA成绩_百分制'] = 70.0  # 默认值
            features['gpa_percentile'] = 50.0
        
        # 学历层次标准化
        degree_level = student_info.get('degree_level', '本科')
        degree_mapping = {
            '专科': 1, '大专': 1,
            '本科': 2, '学士': 2,
            '硕士': 3, '研究生': 3,
            '博士': 4, '博士研究生': 4
        }
        features['教育经历_学历层次_标准化'] = degree_mapping.get(degree_level, 2)
        
        return features
    
    def _convert_university_features(self, student_info: Dict) -> Dict:
        """转换院校特征"""
        features = {}
        
        # 源院校处理
        source_university = student_info.get('university', '')
        source_tier_score = self._get_university_tier_score(source_university)
        
        features['source_university_tier_score'] = source_tier_score
        
        # 判断院校类型
        features['source_is_985'] = 1 if source_tier_score >= 90 else 0
        features['source_is_211'] = 1 if source_tier_score >= 80 else 0
        features['source_is_double_first_class'] = 1 if source_tier_score >= 70 else 0
        
        # 目标院校处理（如果提供）
        target_university = student_info.get('target_university', '')
        if target_university:
            target_tier_score = self._get_university_tier_score(target_university)
            features['target_university_tier_score'] = target_tier_score
            
            # 院校匹配度计算
            tier_gap = target_tier_score - source_tier_score
            features['university_tier_gap'] = tier_gap
            features['university_score_gap'] = abs(tier_gap)
            
            # 院校匹配评分
            if abs(tier_gap) <= 10:
                features['university_matching_score'] = 0.9
            elif abs(tier_gap) <= 20:
                features['university_matching_score'] = 0.7
            else:
                features['university_matching_score'] = 0.5
        else:
            # 默认目标院校特征
            features['target_university_tier_score'] = source_tier_score + 10
            features['university_tier_gap'] = 10
            features['university_score_gap'] = 10
            features['university_matching_score'] = 0.7
        
        return features
    
    def _convert_language_features(self, student_info: Dict) -> Dict:
        """转换语言成绩特征"""
        features = {}
        
        # 语言成绩处理
        language_test = student_info.get('language_test', {})
        if isinstance(language_test, dict) and language_test:
            test_type = language_test.get('type', '').upper()
            score = language_test.get('score', 0)
            
            features['has_language_score'] = 1
            features['language_test_type'] = test_type
            
            # 标准化语言成绩到0-100
            if test_type == 'IELTS':
                normalized_score = (score / 9.0) * 100
            elif test_type == 'TOEFL':
                normalized_score = (score / 120.0) * 100
            elif test_type == 'PTE':
                normalized_score = (score / 90.0) * 100
            elif test_type == 'DUOLINGO':
                normalized_score = (score / 160.0) * 100
            else:
                normalized_score = score  # 假设已经是0-100制
            
            features['language_score_normalized'] = min(100, max(0, normalized_score))
        else:
            features['has_language_score'] = 0
            features['language_test_type'] = 'NONE'
            features['language_score_normalized'] = 60.0  # 默认值
        
        return features
    
    def _convert_work_features(self, student_info: Dict) -> Dict:
        """转换工作经验特征"""
        features = {}
        
        work_experience = student_info.get('work_experience', [])
        if work_experience and len(work_experience) > 0:
            features['has_work_experience'] = 1
            
            # 计算总工作年限
            total_years = 0
            relevance_scores = []
            
            for work in work_experience:
                if isinstance(work, dict):
                    duration = work.get('duration_years', 0)
                    relevance = work.get('relevance_to_major', 0.5)  # 0-1评分
                    
                    total_years += duration
                    relevance_scores.append(relevance)
            
            features['work_experience_years'] = total_years
            features['work_relevance_score'] = np.mean(relevance_scores) if relevance_scores else 0.3
        else:
            features['has_work_experience'] = 0
            features['work_experience_years'] = 0
            features['work_relevance_score'] = 0.0
        
        return features
    
    def _convert_major_matching_features(self, student_info: Dict) -> Dict:
        """转换专业匹配度特征"""
        features = {}
        
        current_major = student_info.get('current_major', '')
        target_major = student_info.get('target_major', '')
        
        if current_major and target_major:
            # 计算专业匹配度（简化版）
            matching_score = self._calculate_major_similarity(current_major, target_major)
            features['major_matching_score'] = matching_score
            
            # 判断是否同领域
            features['is_same_field'] = 1 if matching_score > 0.7 else 0
            
            # 跨专业类型
            if matching_score > 0.8:
                cross_type = '同专业'
            elif matching_score > 0.5:
                cross_type = '相关专业'
            else:
                cross_type = '跨专业'
            features['cross_major_type'] = cross_type
        else:
            features['major_matching_score'] = 0.5
            features['is_same_field'] = 0
            features['cross_major_type'] = '未知'
        
        return features
    
    def _convert_academic_features(self, student_info: Dict) -> Dict:
        """转换学术实力特征"""
        features = {}
        
        gpa_percentile = student_info.get('gpa_percentile', 50)
        university_tier_score = student_info.get('source_university_tier_score', 60)
        language_score = student_info.get('language_score_normalized', 60)
        
        # 综合学术实力评分
        academic_strength = (
            gpa_percentile * 0.4 +
            university_tier_score * 0.3 + 
            language_score * 0.3
        )
        features['academic_strength_score'] = academic_strength
        
        # 申请者综合实力
        work_experience_years = student_info.get('work_experience_years', 0)
        work_bonus = min(10, work_experience_years * 2)  # 工作经验加分
        
        comprehensive_strength = min(100, academic_strength + work_bonus)
        features['applicant_comprehensive_strength'] = comprehensive_strength
        
        # 估算成功概率（基于经验公式）
        success_probability = self._estimate_success_probability(
            gpa_percentile, university_tier_score, language_score
        )
        features['estimated_success_probability'] = success_probability
        
        return features
    
    def _convert_other_features(self, student_info: Dict) -> Dict:
        """转换其他特征"""
        features = {}
        
        # 竞争指数（基于目标专业热度）
        target_major = student_info.get('target_major', '')
        competition_index = self._get_major_competition_index(target_major)
        features['competition_index'] = competition_index
        
        # 时间特征
        current_year = datetime.now().year
        application_year = student_info.get('application_year', current_year)
        features['application_year'] = application_year
        
        # 毕业时间距离
        graduation_date = student_info.get('graduation_date')
        if graduation_date:
            try:
                grad_year = int(graduation_date[:4])
                time_to_graduation = (grad_year - current_year) * 12
                features['time_to_graduation'] = max(0, time_to_graduation)
            except:
                features['time_to_graduation'] = 6  # 默认6个月
        else:
            features['time_to_graduation'] = 6
        
        return features
    
    def _get_university_tier_score(self, university_name: str) -> float:
        """获取院校层次评分"""
        if not university_name:
            return 60.0
        
        # 首先查找映射表
        if university_name in self.university_tier_map:
            return float(self.university_tier_map[university_name])
        
        # 基于关键词的经验评分
        university_upper = university_name.upper()
        
        # 985院校关键词
        if any(keyword in university_upper for keyword in [
            'TSINGHUA', 'PEKING', 'FUDAN', 'SHANGHAI JIAO TONG',
            '清华', '北大', '复旦', '上海交大', '浙大', '中科大'
        ]):
            return 95.0
        
        # 211院校关键词
        elif any(keyword in university_upper for keyword in [
            '北京理工', '华中科技', '西安交通', '哈尔滨工业',
            '同济', '南京大学', '东南大学'
        ]):
            return 85.0
        
        # 海外知名院校
        elif any(keyword in university_upper for keyword in [
            'HARVARD', 'MIT', 'STANFORD', 'CAMBRIDGE', 'OXFORD',
            'MELBOURNE', 'SYDNEY', 'ANU', 'UNSW'
        ]):
            return 95.0
        
        # 默认评分
        else:
            return 60.0
    
    def _calculate_gpa_percentile(self, gpa_100: float) -> float:
        """计算GPA百分位"""
        # 基于经验分布的百分位计算
        if gpa_100 >= 90:
            return 95.0
        elif gpa_100 >= 85:
            return 85.0
        elif gpa_100 >= 80:
            return 75.0
        elif gpa_100 >= 75:
            return 65.0
        elif gpa_100 >= 70:
            return 50.0
        elif gpa_100 >= 65:
            return 35.0
        else:
            return 20.0
    
    def _calculate_major_similarity(self, major1: str, major2: str) -> float:
        """计算专业相似度"""
        if not major1 or not major2:
            return 0.5
        
        major1_lower = major1.lower()
        major2_lower = major2.lower()
        
        # 完全匹配
        if major1_lower == major2_lower:
            return 1.0
        
        # 关键词匹配
        keywords_map = {
            'computer': ['computer', 'computing', 'cs', 'software', 'it'],
            'business': ['business', 'commerce', 'management', 'mba', 'finance'],
            'engineering': ['engineering', 'engineer', 'technology', 'tech'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'math'],
            'arts': ['arts', 'literature', 'language', 'history', 'philosophy']
        }
        
        for category, keywords in keywords_map.items():
            major1_match = any(keyword in major1_lower for keyword in keywords)
            major2_match = any(keyword in major2_lower for keyword in keywords)
            
            if major1_match and major2_match:
                return 0.8
        
        # 部分匹配
        common_words = set(major1_lower.split()) & set(major2_lower.split())
        if common_words:
            return 0.6
        
        return 0.3
    
    def _estimate_success_probability(self, gpa_percentile: float, 
                                    university_score: float, 
                                    language_score: float) -> float:
        """估算申请成功概率"""
        # 基于加权平均的成功概率估算
        weighted_score = (
            gpa_percentile * 0.4 +
            university_score * 0.3 +
            language_score * 0.3
        )
        
        # 转换为概率 (0-1)
        probability = weighted_score / 100.0
        
        return min(0.95, max(0.05, probability))
    
    def _get_major_competition_index(self, major: str) -> float:
        """获取专业竞争指数"""
        if not major:
            return 5.0
        
        major_lower = major.lower()
        
        # 高竞争专业
        if any(keyword in major_lower for keyword in [
            'computer', 'cs', 'data science', 'ai', 'finance', 'mba'
        ]):
            return 8.0
        
        # 中等竞争专业
        elif any(keyword in major_lower for keyword in [
            'business', 'management', 'engineering', 'medicine'
        ]):
            return 6.0
        
        # 低竞争专业
        else:
            return 4.0
    
    def _get_default_features(self) -> Dict:
        """获取默认特征值"""
        return {
            # 教育背景
            '教育经历_GPA成绩_百分制': 70.0,
            'gpa_percentile': 50.0,
            '教育经历_学历层次_标准化': 2,
            
            # 院校特征
            'source_university_tier_score': 60.0,
            'source_is_985': 0,
            'source_is_211': 0,
            'source_is_double_first_class': 0,
            'target_university_tier_score': 70.0,
            'university_tier_gap': 10.0,
            'university_score_gap': 10.0,
            'university_matching_score': 0.7,
            
            # 语言特征
            'has_language_score': 0,
            'language_test_type': 'NONE',
            'language_score_normalized': 60.0,
            
            # 工作经验
            'has_work_experience': 0,
            'work_experience_years': 0,
            'work_relevance_score': 0.0,
            
            # 专业匹配
            'major_matching_score': 0.5,
            'is_same_field': 0,
            'cross_major_type': '未知',
            
            # 学术实力
            'academic_strength_score': 60.0,
            'applicant_comprehensive_strength': 60.0,
            'estimated_success_probability': 0.6,
            
            # 其他特征
            'competition_index': 5.0,
            'application_year': datetime.now().year,
            'time_to_graduation': 6
        }
    
    def get_raw_student_schema(self) -> Dict:
        """获取原始学生信息的输入格式说明"""
        return {
            "required_fields": {
                "university": "毕业院校名称 (string)",
                "gpa": "GPA成绩 (float)",
                "gpa_scale": "GPA满分 (float, 默认4.0)",
                "current_major": "当前专业名称 (string)",
                "target_major": "目标专业名称 (string)"
            },
            "optional_fields": {
                "degree_level": "学历层次 (string): 本科/硕士/博士",
                "target_university": "目标院校名称 (string)",
                "language_test": {
                    "type": "考试类型 (string): IELTS/TOEFL/PTE/DUOLINGO",
                    "score": "考试分数 (float)"
                },
                "work_experience": [
                    {
                        "duration_years": "工作年限 (float)",
                        "relevance_to_major": "与专业相关性 (float, 0-1)"
                    }
                ],
                "application_year": "申请年份 (int)",
                "graduation_date": "毕业日期 (string, YYYY-MM-DD)"
            },
            "example": {
                "university": "北京理工大学",
                "gpa": 3.5,
                "gpa_scale": 4.0,
                "current_major": "计算机科学与技术",
                "target_major": "Master of Computer Science",
                "degree_level": "本科",
                "target_university": "University of Melbourne",
                "language_test": {
                    "type": "IELTS",
                    "score": 7.0
                },
                "work_experience": [
                    {
                        "duration_years": 1.5,
                        "relevance_to_major": 0.8
                    }
                ],
                "application_year": 2024,
                "graduation_date": "2024-06-30"
            }
        }


# 使用示例
if __name__ == "__main__":
    converter = StudentFeatureConverter()
    
    # 示例原始学生信息
    raw_student = {
        "university": "北京理工大学",
        "gpa": 3.5,
        "gpa_scale": 4.0,
        "current_major": "计算机科学与技术", 
        "target_major": "Master of Computer Science",
        "degree_level": "本科",
        "language_test": {
            "type": "IELTS",
            "score": 7.0
        },
        "work_experience": [
            {
                "duration_years": 1.0,
                "relevance_to_major": 0.7
            }
        ]
    }
    
    # 转换为标准化特征
    features = converter.convert_raw_student_info(raw_student)
    
    print("转换结果:")
    for key, value in features.items():
        print(f"  {key}: {value}")