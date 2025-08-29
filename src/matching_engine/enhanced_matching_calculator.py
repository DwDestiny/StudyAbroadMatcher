"""
增强版匹配度计算引擎
修复路径置信度计算、优化相似度算法、校准分数区间
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from sklearn.preprocessing import RobustScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class EnhancedMatchingCalculator:
    def __init__(self, path_profiles_path: str, data_path: str, config_path: Optional[str] = None):
        """
        初始化增强版匹配度计算器
        
        Args:
            path_profiles_path: 路径画像数据文件路径
            data_path: 原始数据文件路径（用于统计分析）
            config_path: 配置文件路径（可选）
        """
        self.path_profiles_path = path_profiles_path
        self.data_path = data_path
        self.path_profiles = None
        self.feature_weights = self._get_default_feature_weights()
        self.feature_cols = None
        self.feature_stats = {}  # 特征统计信息
        self.scaler = None  # 特征缩放器
        
        # 加载数据和初始化
        self.load_path_profiles()
        self.analyze_feature_statistics()
        
        # 加载配置（如果提供）
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def _get_default_feature_weights(self) -> Dict[str, float]:
        """获取默认特征权重配置"""
        return {
            # 核心特征（高权重）
            'source_university_tier_score': 0.20,        # 院校背景
            'gpa_percentile': 0.18,                      # 学术成绩  
            'major_matching_score': 0.15,                # 专业匹配度
            
            # 重要特征（中等权重）
            'language_score_normalized': 0.12,           # 语言能力
            'work_experience_years': 0.10,               # 工作经验
            'work_relevance_score': 0.08,                # 工作相关性
            
            # 辅助特征（低权重）
            'target_university_tier_score': 0.05,        # 目标院校层次
            'university_matching_score': 0.04,           # 院校匹配度
            'competition_index': 0.03,                   # 竞争指数
            'academic_strength_score': 0.03,             # 学术实力
            'applicant_comprehensive_strength': 0.02,     # 综合实力
        }
    
    def load_path_profiles(self):
        """加载路径画像数据"""
        print("加载路径画像数据...")
        
        with open(self.path_profiles_path, 'r', encoding='utf-8') as f:
            self.path_profiles = json.load(f)
        
        # 提取特征列信息
        if self.path_profiles:
            first_major = list(self.path_profiles.keys())[0]
            first_path = list(self.path_profiles[first_major]['paths'].values())[0]
            self.feature_cols = list(first_path['profile'].keys())
        
        print(f"加载完成 - 专业数: {len(self.path_profiles)}, 特征数: {len(self.feature_cols)}")
    
    def analyze_feature_statistics(self):
        """分析特征统计信息，识别异常值和合理范围"""
        print("分析特征统计信息...")
        
        # 加载原始数据
        df = pd.read_csv(self.data_path)
        
        for feature in self.feature_cols:
            if feature in df.columns:
                values = df[feature].copy()
                
                # 异常值检测和清理
                values = self._clean_feature_values(values, feature)
                
                if len(values) > 0:
                    self.feature_stats[feature] = {
                        'mean': float(values.mean()),
                        'std': float(values.std()),
                        'median': float(values.median()),
                        'q25': float(values.quantile(0.25)),
                        'q75': float(values.quantile(0.75)),
                        'min': float(values.min()),
                        'max': float(values.max()),
                        'iqr': float(values.quantile(0.75) - values.quantile(0.25)),
                        'outlier_threshold_lower': float(values.quantile(0.25) - 1.5 * (values.quantile(0.75) - values.quantile(0.25))),
                        'outlier_threshold_upper': float(values.quantile(0.75) + 1.5 * (values.quantile(0.75) - values.quantile(0.25))),
                        'robust_mean': float(values.clip(values.quantile(0.05), values.quantile(0.95)).mean()),
                        'robust_std': float(values.clip(values.quantile(0.05), values.quantile(0.95)).std())
                    }
                else:
                    # 默认统计值
                    self.feature_stats[feature] = {
                        'mean': 0.0, 'std': 1.0, 'median': 0.0, 'q25': 0.0, 'q75': 0.0,
                        'min': 0.0, 'max': 1.0, 'iqr': 1.0,
                        'outlier_threshold_lower': 0.0, 'outlier_threshold_upper': 1.0,
                        'robust_mean': 0.0, 'robust_std': 1.0
                    }
        
        print(f"特征统计分析完成，处理 {len(self.feature_stats)} 个特征")
    
    def _clean_feature_values(self, values: pd.Series, feature_name: str) -> pd.Series:
        """清理特征值，移除异常值"""
        
        # 移除缺失值
        values = values.dropna()
        
        if len(values) == 0:
            return values
        
        # 特殊处理已知问题特征
        if 'GPA' in feature_name and '百分制' in feature_name:
            # GPA百分制应该在0-100范围内
            values = values.clip(0, 100)
        
        # 通用异常值检测（使用IQR方法）
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        
        if iqr > 0:
            lower_bound = q1 - 3 * iqr  # 使用3倍IQR而非1.5倍，更宽松
            upper_bound = q3 + 3 * iqr
            
            # 记录异常值数量
            outlier_count = ((values < lower_bound) | (values > upper_bound)).sum()
            if outlier_count > 0:
                print(f"特征 {feature_name}: 移除 {outlier_count} 个异常值")
            
            values = values.clip(lower_bound, upper_bound)
        
        return values
    
    def normalize_student_features(self, student_features: Dict[str, Any]) -> Dict[str, float]:
        """改进的学生特征标准化"""
        normalized = {}
        
        for feature in self.feature_cols:
            if feature in student_features and student_features[feature] is not None:
                value = float(student_features[feature])
                
                # 使用特征统计信息进行清理
                if feature in self.feature_stats:
                    stats = self.feature_stats[feature]
                    # 异常值剪切
                    value = max(stats['outlier_threshold_lower'], 
                              min(stats['outlier_threshold_upper'], value))
                
                normalized[feature] = value
            else:
                # 使用特征均值而非0填充
                if feature in self.feature_stats:
                    normalized[feature] = self.feature_stats[feature]['robust_mean']
                else:
                    normalized[feature] = 0.0
        
        return normalized
    
    def calculate_robust_similarity(self, student_features: Dict[str, float], path_profile: Dict[str, Any]) -> float:
        """使用鲁棒的相似度计算方法"""
        
        similarities = []
        total_weight = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in student_features and feature in path_profile and feature in self.feature_stats:
                try:
                    student_val = student_features[feature]
                    path_stats = path_profile[feature]
                    feature_stats = self.feature_stats[feature]
                    
                    # 获取路径统计信息
                    path_mean = path_stats['mean']
                    path_std = max(path_stats['std'], feature_stats['iqr'] / 2)  # 防止标准差为0
                    
                    # 使用鲁棒的相似度计算
                    if path_std > 0:
                        # 标准化差值
                        z_score = abs(student_val - path_mean) / path_std
                        
                        # 使用改进的相似度函数
                        if z_score <= 0.5:
                            # 非常接近，高相似度
                            feature_similarity = 1.0 - 0.2 * z_score
                        elif z_score <= 1.0:
                            # 接近，中等相似度
                            feature_similarity = 0.9 - 0.3 * (z_score - 0.5)
                        elif z_score <= 2.0:
                            # 有差距，低相似度
                            feature_similarity = 0.75 - 0.4 * (z_score - 1.0)
                        else:
                            # 差距很大，很低相似度
                            feature_similarity = max(0.1, 0.35 - 0.1 * (z_score - 2.0))
                    else:
                        # 标准差为0，直接比较
                        feature_similarity = 1.0 if abs(student_val - path_mean) < 0.01 else 0.5
                    
                    similarities.append(feature_similarity)
                    total_weight += weight
                    
                except Exception as e:
                    print(f"计算特征 {feature} 相似度时出错: {e}")
                    continue
        
        if similarities and total_weight > 0:
            weighted_similarity = sum(similarities) / len(similarities)  # 简单平均
            return max(0.1, min(1.0, weighted_similarity))  # 确保在合理范围内
        else:
            return 0.1  # 最低相似度
    
    def calculate_enhanced_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """增强版余弦相似度计算"""
        try:
            # 确保维度匹配
            min_dim = min(len(vec1), len(vec2))
            if min_dim == 0:
                return 0.0
            
            # 创建特征向量，使用鲁棒标准化
            v1_normalized = []
            v2_normalized = []
            
            for i in range(min_dim):
                feature = self.feature_cols[i] if i < len(self.feature_cols) else f"feature_{i}"
                
                if feature in self.feature_stats:
                    stats = self.feature_stats[feature]
                    robust_std = max(stats['robust_std'], 1e-6)  # 防止除零
                    
                    # 鲁棒标准化：使用robust_mean和robust_std
                    v1_norm = (vec1[i] - stats['robust_mean']) / robust_std
                    v2_norm = (vec2[i] - stats['robust_mean']) / robust_std
                    
                    v1_normalized.append(v1_norm)
                    v2_normalized.append(v2_norm)
                else:
                    # 简单标准化
                    v1_normalized.append(vec1[i])
                    v2_normalized.append(vec2[i])
            
            # 计算余弦相似度
            v1_array = np.array(v1_normalized)
            v2_array = np.array(v2_normalized)
            
            dot_product = np.dot(v1_array, v2_array)
            norm1 = np.linalg.norm(v1_array)
            norm2 = np.linalg.norm(v2_array)
            
            if norm1 > 1e-10 and norm2 > 1e-10:
                similarity = dot_product / (norm1 * norm2)
                # 将相似度映射到0-1范围
                similarity = (similarity + 1) / 2
                return max(0.0, min(1.0, similarity))
            else:
                return 0.1  # 默认低相似度
                
        except Exception as e:
            print(f"计算增强余弦相似度时出错: {e}")
            return 0.1
    
    def assign_best_path_enhanced(self, student_features: Dict[str, float], major_paths: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """增强版路径归属判断"""
        best_path_key = None
        best_confidence = 0.0
        best_path_info = None
        
        # 将学生特征转换为标准化向量
        student_vector = []
        for feature in self.feature_cols:
            student_vector.append(student_features.get(feature, self.feature_stats.get(feature, {}).get('robust_mean', 0.0)))
        
        # 计算与每个路径的相似度
        similarities = {}
        
        for path_key, path_info in major_paths.items():
            try:
                # 方法1：增强版余弦相似度
                path_center = path_info['cluster_center']
                cosine_sim = self.calculate_enhanced_cosine_similarity(student_vector, path_center)
                
                # 方法2：基于特征分布的相似度
                robust_sim = self.calculate_robust_similarity(student_features, path_info['profile'])
                
                # 综合相似度（两种方法结合）
                combined_similarity = (cosine_sim * 0.4) + (robust_sim * 0.6)
                
                # 路径代表性权重调整
                representativeness = path_info.get('representativeness', 0.5)
                coverage = path_info.get('coverage', 0.1)
                
                # 最终置信度计算
                confidence = combined_similarity * (0.7 + 0.3 * representativeness) * min(1.0, coverage * 10)
                
                similarities[path_key] = {
                    'cosine_sim': cosine_sim,
                    'robust_sim': robust_sim,
                    'combined_sim': combined_similarity,
                    'confidence': confidence,
                    'path_info': path_info
                }
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_path_key = path_key
                    best_path_info = path_info
                    
            except Exception as e:
                print(f"计算路径 {path_key} 相似度时出错: {e}")
                continue
        
        # 确保最低置信度
        final_confidence = max(0.15, min(1.0, best_confidence))
        
        return best_path_key, final_confidence, best_path_info
    
    def calculate_match_score_enhanced(self, student_features: Dict[str, Any], target_major: str) -> Dict[str, Any]:
        """增强版匹配度计算"""
        
        # 检查专业是否存在
        if target_major not in self.path_profiles:
            return {
                'success': False,
                'error': f'专业 "{target_major}" 未找到',
                'available_majors': list(self.path_profiles.keys())[:10]
            }
        
        try:
            # 标准化学生特征
            normalized_features = self.normalize_student_features(student_features)
            
            # 获取专业路径数据
            major_data = self.path_profiles[target_major]
            major_paths = major_data['paths']
            
            # 增强版路径归属判断
            best_path_key, confidence, best_path_info = self.assign_best_path_enhanced(normalized_features, major_paths)
            
            if not best_path_key:
                return {
                    'success': False,
                    'error': '无法找到匹配的路径',
                    'target_major': target_major
                }
            
            # 详细相似度计算
            detailed_similarity = self.calculate_robust_similarity(normalized_features, best_path_info['profile'])
            
            # 改进的最终分数计算
            # 基础分数：基于详细相似度
            base_score = detailed_similarity * 100
            
            # 置信度调整：高置信度提升分数，低置信度降低分数
            confidence_adjustment = (confidence - 0.5) * 20  # -10到+10的调整
            
            # 路径覆盖度调整：覆盖度高的路径更可信
            coverage_adjustment = (best_path_info.get('coverage', 0.1) - 0.2) * 10  # 覆盖度调整
            
            # 最终分数
            final_score = base_score + confidence_adjustment + coverage_adjustment
            final_score = max(10, min(100, int(final_score)))  # 确保在10-100范围内
            
            # 生成详细结果
            result = {
                'success': True,
                'target_major': target_major,
                'match_score': final_score,
                'matched_path': best_path_info['label'],
                'path_confidence': round(confidence, 3),
                'detailed_similarity': round(detailed_similarity, 3),
                'path_coverage': round(best_path_info['coverage'], 3),
                'path_representativeness': round(best_path_info['representativeness'], 3),
                'success_indicators': best_path_info.get('success_indicators', {}),
                'match_level': self._get_match_level(final_score),
                'recommendation': self._generate_recommendation(final_score, best_path_info),
                'score_breakdown': {
                    'base_score': round(base_score, 1),
                    'confidence_adjustment': round(confidence_adjustment, 1),
                    'coverage_adjustment': round(coverage_adjustment, 1)
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'计算匹配度时出错: {str(e)}',
                'target_major': target_major
            }
    
    def _get_match_level(self, score: int) -> str:
        """根据分数确定匹配等级"""
        if score >= 85:
            return "高匹配"
        elif score >= 70:
            return "中等匹配"
        elif score >= 55:
            return "低匹配"
        elif score >= 40:
            return "较低匹配"
        else:
            return "不匹配"
    
    def _generate_recommendation(self, score: int, path_info: Dict[str, Any]) -> str:
        """生成匹配建议"""
        if score >= 85:
            return f"您的背景与{path_info['label']}路径高度匹配，强烈推荐申请。"
        elif score >= 70:
            return f"您的背景与{path_info['label']}路径较为匹配，推荐申请。"
        elif score >= 55:
            return f"您的背景与{path_info['label']}路径有一定匹配，可以考虑申请。"
        elif score >= 40:
            return f"您的背景与{path_info['label']}路径存在差距，建议提升相关背景后申请。"
        else:
            return "不建议申请此专业，建议重新评估专业选择。"
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'feature_weights' in config:
            self.feature_weights.update(config['feature_weights'])
            print("已加载自定义特征权重配置")


def main():
    """主函数 - 演示增强版匹配计算器"""
    
    # 配置路径
    path_profiles_path = 'data/path_profiles/path_profiles.json'
    data_path = 'data/processed/final_feature_dataset_latest.csv'
    
    # 创建增强版匹配计算器
    calculator = EnhancedMatchingCalculator(path_profiles_path, data_path)
    
    # 测试学生特征
    student_example = {
        'source_university_tier_score': 75,      # 211院校
        'gpa_percentile': 75,                    # 中等GPA
        'major_matching_score': 0.7,             # 中等匹配
        'language_score_normalized': 70,         # 中等语言
        'work_experience_years': 1,              # 少量经验
        'work_relevance_score': 0.5,             # 中等相关
        'target_university_tier_score': 80,
        'university_matching_score': 0.7,
        'competition_index': 6.0,
        'academic_strength_score': 75,
        'applicant_comprehensive_strength': 72
    }
    
    # 测试增强版匹配计算
    print("=== 增强版匹配计算测试 ===")
    result = calculator.calculate_match_score_enhanced(student_example, "Master of Commerce")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return calculator


if __name__ == "__main__":
    main()