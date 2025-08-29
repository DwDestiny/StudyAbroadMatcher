"""
小样本专业处理策略
为申请量较少的专业提供简化但有效的匹配算法
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class SmallSampleProcessor:
    def __init__(self, data_path: str, output_path: str):
        """
        初始化小样本专业处理器
        
        Args:
            data_path: 特征数据文件路径
            output_path: 输出路径
        """
        self.data_path = data_path
        self.output_path = output_path
        self.df = None
        self.feature_cols = None
        self.target_major_col = "申请院校_专业名称"
        
        # 小样本处理阈值
        self.small_sample_min = 30   # 最小样本数量
        self.small_sample_max = 99   # 最大样本数量
        self.medium_sample_min = 50  # 中等样本最小数量
        
        # 加载数据
        self.load_data()
    
    def load_data(self):
        """加载和预处理数据"""
        print("加载数据用于小样本分析...")
        self.df = pd.read_csv(self.data_path)
        print(f"数据形状: {self.df.shape}")
        
        # 识别特征列
        exclude_patterns = ['ID', 'id', '名称', '时间', '日期', '描述', '类型', '开始', '结束', '单位', '职位', '职责']
        self.feature_cols = []
        
        for col in self.df.columns:
            if self.df[col].dtype in ['int64', 'float64']:
                if not any(pattern in col for pattern in exclude_patterns):
                    self.feature_cols.append(col)
        
        print(f"识别到 {len(self.feature_cols)} 个特征列")
    
    def analyze_small_sample_majors(self) -> Dict[str, Any]:
        """分析小样本专业的分布和特点"""
        print("分析小样本专业...")
        
        major_counts = self.df[self.target_major_col].value_counts()
        
        # 分类专业
        large_sample_majors = major_counts[major_counts >= 100]
        medium_sample_majors = major_counts[(major_counts >= self.medium_sample_min) & (major_counts < 100)]
        small_sample_majors = major_counts[(major_counts >= self.small_sample_min) & (major_counts < self.medium_sample_min)]
        tiny_sample_majors = major_counts[major_counts < self.small_sample_min]
        
        analysis = {
            'large_sample': {
                'count': len(large_sample_majors),
                'coverage': large_sample_majors.sum(),
                'majors': large_sample_majors.index.tolist()
            },
            'medium_sample': {
                'count': len(medium_sample_majors),
                'coverage': medium_sample_majors.sum(),
                'majors': medium_sample_majors.index.tolist()
            },
            'small_sample': {
                'count': len(small_sample_majors),
                'coverage': small_sample_majors.sum(),
                'majors': small_sample_majors.index.tolist()
            },
            'tiny_sample': {
                'count': len(tiny_sample_majors),
                'coverage': tiny_sample_majors.sum(),
                'majors': tiny_sample_majors.index.tolist()[:20]  # 只显示前20个
            }
        }
        
        print(f"大样本专业(≥100): {analysis['large_sample']['count']}个, 覆盖{analysis['large_sample']['coverage']}申请")
        print(f"中等样本专业(50-99): {analysis['medium_sample']['count']}个, 覆盖{analysis['medium_sample']['coverage']}申请") 
        print(f"小样本专业(30-49): {analysis['small_sample']['count']}个, 覆盖{analysis['small_sample']['coverage']}申请")
        print(f"微样本专业(<30): {analysis['tiny_sample']['count']}个, 覆盖{analysis['tiny_sample']['coverage']}申请")
        
        return analysis
    
    def create_simple_profile(self, major_name: str) -> Dict[str, Any]:
        """为小样本专业创建简化画像"""
        
        # 获取该专业的数据
        major_data = self.df[self.df[self.target_major_col] == major_name]
        sample_size = len(major_data)
        
        if sample_size < self.small_sample_min:
            return None
        
        # 计算基本统计信息
        profile = {
            'sample_size': sample_size,
            'profile_type': 'simple',
            'features': {}
        }
        
        # 计算每个特征的统计信息
        for feature in self.feature_cols:
            if feature in major_data.columns:
                values = major_data[feature].dropna()
                if len(values) > 0:
                    # 简化的统计信息
                    profile['features'][feature] = {
                        'mean': float(values.mean()),
                        'std': float(values.std()) if pd.notna(values.std()) else 0.0,
                        'median': float(values.median()),
                        'min': float(values.min()),
                        'max': float(values.max()),
                        'count': int(len(values))
                    }
        
        # 生成专业标签
        profile['label'] = self._generate_simple_label(profile['features'], sample_size)
        
        # 计算相似专业（基于专业名称）
        profile['similar_majors'] = self._find_similar_majors(major_name)
        
        return profile
    
    def _generate_simple_label(self, features: Dict[str, Any], sample_size: int) -> str:
        """为小样本专业生成简单标签"""
        
        # 基于关键特征生成标签
        labels = []
        
        # 院校背景
        if 'source_university_tier_score' in features:
            score = features['source_university_tier_score']['mean']
            if score >= 85:
                labels.append('名校背景')
            elif score >= 75:
                labels.append('211背景')
            else:
                labels.append('本科背景')
        
        # GPA水平
        if 'gpa_percentile' in features:
            gpa = features['gpa_percentile']['mean']
            if gpa >= 80:
                labels.append('高GPA')
            elif gpa >= 70:
                labels.append('中等GPA')
            else:
                labels.append('一般GPA')
        
        # 样本大小指示
        if sample_size >= 50:
            labels.append('中等样本')
        else:
            labels.append('小样本')
        
        return '-'.join(labels) if labels else f'小样本专业({sample_size})'
    
    def _find_similar_majors(self, major_name: str, max_similar: int = 3) -> List[str]:
        """基于专业名称找到相似专业"""
        
        similar_majors = []
        major_name_lower = major_name.lower()
        
        # 提取关键词
        keywords = []
        common_terms = ['master', 'bachelor', 'of', 'in', 'and', 'the', 'a']
        
        for word in major_name_lower.split():
            if word not in common_terms and len(word) > 2:
                keywords.append(word)
        
        if not keywords:
            return similar_majors
        
        # 在大样本专业中寻找相似的
        major_counts = self.df[self.target_major_col].value_counts()
        large_sample_majors = major_counts[major_counts >= 100].index
        
        for other_major in large_sample_majors:
            if other_major == major_name:
                continue
            
            other_major_lower = other_major.lower()
            match_count = sum(1 for keyword in keywords if keyword in other_major_lower)
            
            if match_count >= 1:  # 至少有一个关键词匹配
                similar_majors.append(other_major)
                if len(similar_majors) >= max_similar:
                    break
        
        return similar_majors
    
    def calculate_simple_similarity(self, student_features: Dict[str, float], simple_profile: Dict[str, Any]) -> float:
        """计算学生与小样本专业的简化相似度"""
        
        if not simple_profile or 'features' not in simple_profile:
            return 0.1
        
        similarities = []
        
        # 核心特征权重
        core_features = {
            'source_university_tier_score': 0.25,
            'gpa_percentile': 0.20,
            'major_matching_score': 0.15,
            'language_score_normalized': 0.15,
            'work_experience_years': 0.10,
            'work_relevance_score': 0.10,
            'academic_strength_score': 0.05
        }
        
        total_weight = 0.0
        
        for feature, weight in core_features.items():
            if feature in student_features and feature in simple_profile['features']:
                
                student_val = student_features[feature]
                profile_stats = simple_profile['features'][feature]
                
                if profile_stats['count'] > 0:
                    mean_val = profile_stats['mean']
                    std_val = max(profile_stats['std'], 1e-6)
                    
                    # 简化的相似度计算
                    z_score = abs(student_val - mean_val) / std_val
                    
                    if z_score <= 0.5:
                        feature_sim = 0.9 + 0.1 * (1 - z_score * 2)
                    elif z_score <= 1.0:
                        feature_sim = 0.7 + 0.2 * (1 - (z_score - 0.5) * 2)
                    elif z_score <= 2.0:
                        feature_sim = 0.4 + 0.3 * (1 - (z_score - 1.0))
                    else:
                        feature_sim = max(0.1, 0.4 - 0.05 * (z_score - 2.0))
                    
                    similarities.append(feature_sim * weight)
                    total_weight += weight
        
        if total_weight > 0 and similarities:
            return sum(similarities) / total_weight
        else:
            return 0.3  # 默认中等相似度
    
    def process_small_sample_majors(self) -> Dict[str, Any]:
        """处理所有小样本专业"""
        print("处理小样本专业...")
        
        # 分析专业分布
        analysis = self.analyze_small_sample_majors()
        
        # 处理中等样本专业（50-99申请）
        medium_profiles = {}
        for major in analysis['medium_sample']['majors']:
            profile = self.create_simple_profile(major)
            if profile:
                medium_profiles[major] = profile
        
        # 处理小样本专业（30-49申请）
        small_profiles = {}
        for major in analysis['small_sample']['majors']:
            profile = self.create_simple_profile(major)
            if profile:
                small_profiles[major] = profile
        
        # 合并结果
        all_small_sample_profiles = {
            'medium_sample_profiles': medium_profiles,
            'small_sample_profiles': small_profiles,
            'analysis_summary': analysis,
            'processing_stats': {
                'medium_processed': len(medium_profiles),
                'small_processed': len(small_profiles),
                'total_processed': len(medium_profiles) + len(small_profiles)
            }
        }
        
        # 保存结果
        os.makedirs(self.output_path, exist_ok=True)
        output_file = os.path.join(self.output_path, 'small_sample_profiles.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_small_sample_profiles, f, ensure_ascii=False, indent=2)
        
        print(f"小样本专业处理完成！")
        print(f"中等样本专业: {len(medium_profiles)}个")
        print(f"小样本专业: {len(small_profiles)}个")
        print(f"结果保存至: {output_file}")
        
        return all_small_sample_profiles
    
    def create_integrated_matching_data(self, large_sample_profiles_path: str) -> Dict[str, Any]:
        """创建集成的匹配数据，包含大样本和小样本专业"""
        
        # 加载大样本专业画像
        if os.path.exists(large_sample_profiles_path):
            with open(large_sample_profiles_path, 'r', encoding='utf-8') as f:
                large_profiles = json.load(f)
        else:
            large_profiles = {}
        
        # 处理小样本专业
        small_sample_data = self.process_small_sample_majors()
        
        # 集成数据
        integrated_data = {
            'large_sample_majors': large_profiles,
            'medium_sample_majors': small_sample_data['medium_sample_profiles'],
            'small_sample_majors': small_sample_data['small_sample_profiles'],
            'statistics': {
                'large_sample_count': len(large_profiles),
                'medium_sample_count': len(small_sample_data['medium_sample_profiles']),
                'small_sample_count': len(small_sample_data['small_sample_profiles']),
                'total_majors': len(large_profiles) + len(small_sample_data['medium_sample_profiles']) + len(small_sample_data['small_sample_profiles'])
            },
            'processing_info': {
                'large_sample_method': 'clustering_based',
                'medium_sample_method': 'simple_statistical',
                'small_sample_method': 'basic_statistical',
                'integration_timestamp': pd.Timestamp.now().isoformat()
            }
        }
        
        # 保存集成数据
        integrated_file = os.path.join(self.output_path, 'integrated_profiles.json')
        with open(integrated_file, 'w', encoding='utf-8') as f:
            json.dump(integrated_data, f, ensure_ascii=False, indent=2)
        
        print(f"集成匹配数据创建完成！")
        print(f"总专业数: {integrated_data['statistics']['total_majors']}")
        print(f"大样本: {integrated_data['statistics']['large_sample_count']}")
        print(f"中等样本: {integrated_data['statistics']['medium_sample_count']}")
        print(f"小样本: {integrated_data['statistics']['small_sample_count']}")
        print(f"集成文件: {integrated_file}")
        
        return integrated_data


class SmallSampleMatcher:
    """小样本专业匹配器"""
    
    def __init__(self, small_sample_profiles_path: str):
        """
        初始化小样本匹配器
        
        Args:
            small_sample_profiles_path: 小样本专业画像文件路径
        """
        self.small_sample_profiles_path = small_sample_profiles_path
        self.small_sample_data = None
        self.processor = None
        
        self.load_small_sample_data()
    
    def load_small_sample_data(self):
        """加载小样本专业数据"""
        with open(self.small_sample_profiles_path, 'r', encoding='utf-8') as f:
            self.small_sample_data = json.load(f)
        
        print(f"小样本数据加载完成")
        print(f"中等样本专业: {len(self.small_sample_data['medium_sample_profiles'])}")
        print(f"小样本专业: {len(self.small_sample_data['small_sample_profiles'])}")
    
    def match_small_sample_major(self, student_features: Dict[str, Any], target_major: str) -> Dict[str, Any]:
        """匹配小样本专业"""
        
        # 检查专业是否存在
        all_profiles = {
            **self.small_sample_data['medium_sample_profiles'],
            **self.small_sample_data['small_sample_profiles']
        }
        
        if target_major not in all_profiles:
            return {
                'success': False,
                'error': f'小样本专业 "{target_major}" 未找到'
            }
        
        try:
            # 获取专业画像
            profile = all_profiles[target_major]
            
            # 创建临时处理器用于相似度计算
            if not self.processor:
                self.processor = SmallSampleProcessor('', '')
            
            # 标准化学生特征
            normalized_features = {}
            for feature, value in student_features.items():
                if value is not None:
                    normalized_features[feature] = float(value)
            
            # 计算相似度
            similarity = self.processor.calculate_simple_similarity(normalized_features, profile)
            
            # 计算最终分数
            base_score = similarity * 100
            
            # 小样本调整：由于数据量少，降低置信度
            sample_size = profile['sample_size']
            if sample_size >= 50:
                confidence_penalty = 0  # 中等样本无惩罚
            else:
                confidence_penalty = (50 - sample_size) * 0.2  # 样本越小惩罚越大
            
            final_score = max(10, min(95, int(base_score - confidence_penalty)))
            
            # 生成结果
            result = {
                'success': True,
                'target_major': target_major,
                'match_score': final_score,
                'sample_size': sample_size,
                'profile_type': profile['profile_type'],
                'matched_path': profile['label'],
                'similarity': round(similarity, 3),
                'confidence_penalty': round(confidence_penalty, 1),
                'similar_majors': profile.get('similar_majors', []),
                'match_level': self._get_match_level(final_score),
                'recommendation': self._generate_small_sample_recommendation(final_score, sample_size, profile),
                'note': f'基于{sample_size}个历史申请样本的简化匹配'
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'小样本匹配计算失败: {str(e)}',
                'target_major': target_major
            }
    
    def _get_match_level(self, score: int) -> str:
        """获取匹配等级"""
        if score >= 80:
            return "较高匹配"
        elif score >= 65:
            return "中等匹配"
        elif score >= 50:
            return "一般匹配"
        else:
            return "较低匹配"
    
    def _generate_small_sample_recommendation(self, score: int, sample_size: int, profile: Dict[str, Any]) -> str:
        """生成小样本专业推荐建议"""
        
        base_recommendation = ""
        if score >= 80:
            base_recommendation = "您的背景与该专业历史申请者较为匹配，可以考虑申请。"
        elif score >= 65:
            base_recommendation = "您的背景与该专业有一定匹配，建议谨慎考虑。"
        elif score >= 50:
            base_recommendation = "您的背景与该专业存在差距，需要充分评估。"
        else:
            base_recommendation = "您的背景与该专业匹配度较低，不太推荐。"
        
        # 添加小样本提醒
        if sample_size < 50:
            sample_note = f"注意：该专业历史申请样本较少({sample_size}个)，建议参考相似专业。"
        else:
            sample_note = f"该专业有{sample_size}个历史申请样本，数据相对可靠。"
        
        # 相似专业建议
        similar_majors = profile.get('similar_majors', [])
        if similar_majors:
            similar_note = f"您也可以考虑相似专业：{', '.join(similar_majors[:2])}等。"
        else:
            similar_note = ""
        
        return f"{base_recommendation} {sample_note} {similar_note}".strip()


def main():
    """主函数 - 小样本专业处理演示"""
    
    # 配置路径
    data_path = 'data/processed/final_feature_dataset_latest.csv'
    output_path = 'data/small_sample_profiles'
    large_profiles_path = 'data/path_profiles/path_profiles.json'
    
    # 1. 创建小样本处理器
    processor = SmallSampleProcessor(data_path, output_path)
    
    # 2. 处理小样本专业并创建集成数据
    integrated_data = processor.create_integrated_matching_data(large_profiles_path)
    
    # 3. 测试小样本匹配器
    small_profiles_path = os.path.join(output_path, 'small_sample_profiles.json')
    if os.path.exists(small_profiles_path):
        matcher = SmallSampleMatcher(small_profiles_path)
        
        # 测试匹配一个小样本专业
        test_student = {
            'source_university_tier_score': 75,
            'gpa_percentile': 75,
            'major_matching_score': 0.7,
            'language_score_normalized': 70,
            'work_experience_years': 1,
            'work_relevance_score': 0.5
        }
        
        # 获取一个小样本专业进行测试
        medium_majors = list(matcher.small_sample_data['medium_sample_profiles'].keys())
        if medium_majors:
            test_major = medium_majors[0]
            print(f"\n=== 测试小样本专业匹配: {test_major} ===")
            result = matcher.match_small_sample_major(test_student, test_major)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return processor, integrated_data


if __name__ == "__main__":
    main()