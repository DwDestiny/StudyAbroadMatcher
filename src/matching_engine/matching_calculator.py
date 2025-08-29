"""
匹配度计算引擎
实现两阶段匹配算法，为新学生计算与特定专业的匹配度
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class MatchingCalculator:
    def __init__(self, path_profiles_path: str, config_path: Optional[str] = None):
        """
        初始化匹配度计算器
        
        Args:
            path_profiles_path: 路径画像数据文件路径
            config_path: 配置文件路径（可选）
        """
        self.path_profiles_path = path_profiles_path
        self.path_profiles = None
        self.feature_weights = self._get_default_feature_weights()
        self.feature_cols = None
        
        # 加载路径画像数据
        self.load_path_profiles()
        
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
        
        # 提取特征列信息（从第一个专业的第一个路径中）
        if self.path_profiles:
            first_major = list(self.path_profiles.keys())[0]
            first_path = list(self.path_profiles[first_major]['paths'].values())[0]
            self.feature_cols = list(first_path['profile'].keys())
        
        print(f"加载完成 - 专业数: {len(self.path_profiles)}, 特征数: {len(self.feature_cols)}")
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'feature_weights' in config:
            self.feature_weights.update(config['feature_weights'])
            print("已加载自定义特征权重配置")
    
    def normalize_student_features(self, student_features: Dict[str, Any]) -> Dict[str, float]:
        """标准化学生特征向量"""
        normalized = {}
        
        for feature in self.feature_cols:
            if feature in student_features:
                value = student_features[feature]
                # 确保数值类型
                try:
                    normalized[feature] = float(value)
                except (ValueError, TypeError):
                    normalized[feature] = 0.0
            else:
                normalized[feature] = 0.0
        
        return normalized
    
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            # 确保维度匹配
            min_dim = min(len(vec1), len(vec2))
            vec1 = np.array(vec1[:min_dim])
            vec2 = np.array(vec2[:min_dim])
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, similarity)  # 确保非负
            
        except Exception as e:
            print(f"计算余弦相似度时出错: {e}")
            return 0.0
    
    def assign_best_path(self, student_features: Dict[str, float], major_paths: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """
        阶段1：路径归属判断
        计算学生向量与各路径中心的距离，返回最相似的路径
        """
        best_path_key = None
        best_similarity = -1.0
        best_path_info = None
        
        # 将学生特征转换为向量
        student_vector = []
        for feature in self.feature_cols:
            student_vector.append(student_features.get(feature, 0.0))
        
        # 计算与每个路径中心的相似度
        for path_key, path_info in major_paths.items():
            try:
                path_center = path_info['cluster_center']
                similarity = self.calculate_cosine_similarity(student_vector, path_center)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_path_key = path_key
                    best_path_info = path_info
                    
            except Exception as e:
                print(f"计算路径 {path_key} 相似度时出错: {e}")
                continue
        
        # 计算置信度（基于相似度）
        confidence = best_similarity if best_similarity > 0 else 0.1
        
        return best_path_key, confidence, best_path_info
    
    def calculate_weighted_similarity(self, student_features: Dict[str, float], path_profile: Dict[str, Any]) -> float:
        """
        阶段2：加权相似度计算
        基于路径画像计算详细的加权相似度分数
        """
        weighted_similarity = 0.0
        total_weight = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in student_features and feature in path_profile:
                try:
                    student_val = student_features[feature]
                    path_stats = path_profile[feature]
                    
                    # 获取路径统计信息
                    path_mean = path_stats['mean']
                    path_std = path_stats['std']
                    
                    # 计算标准化距离
                    if path_std > 0:
                        # 使用正态分布模型计算相似度
                        z_score = abs(student_val - path_mean) / path_std
                        # 转换为相似度（z_score越小相似度越高）
                        feature_similarity = max(0.0, 1.0 - (z_score / 3.0))  # 3个标准差内的相似度
                    else:
                        # 标准差为0，直接比较均值
                        if abs(student_val - path_mean) < 0.01:
                            feature_similarity = 1.0
                        else:
                            feature_similarity = max(0.0, 1.0 - abs(student_val - path_mean) / max(abs(path_mean), 1.0))
                    
                    weighted_similarity += feature_similarity * weight
                    total_weight += weight
                    
                except Exception as e:
                    print(f"计算特征 {feature} 相似度时出错: {e}")
                    continue
        
        if total_weight > 0:
            return weighted_similarity / total_weight
        else:
            return 0.0
    
    def calculate_match_score(self, student_features: Dict[str, Any], target_major: str) -> Dict[str, Any]:
        """
        计算学生与目标专业的匹配度
        
        Args:
            student_features: 学生特征字典（75维）
            target_major: 目标专业名称
            
        Returns:
            匹配度结果字典，包含分数、路径标签、置信度等信息
        """
        
        # 检查专业是否存在
        if target_major not in self.path_profiles:
            return {
                'success': False,
                'error': f'专业 "{target_major}" 未找到',
                'available_majors': list(self.path_profiles.keys())[:10]  # 返回前10个可用专业
            }
        
        try:
            # 标准化学生特征
            normalized_features = self.normalize_student_features(student_features)
            
            # 获取专业路径数据
            major_data = self.path_profiles[target_major]
            major_paths = major_data['paths']
            
            # 阶段1：路径归属判断
            best_path_key, confidence, best_path_info = self.assign_best_path(normalized_features, major_paths)
            
            if not best_path_key:
                return {
                    'success': False,
                    'error': '无法找到匹配的路径',
                    'target_major': target_major
                }
            
            # 阶段2：详细相似度计算
            detailed_similarity = self.calculate_weighted_similarity(
                normalized_features, 
                best_path_info['profile']
            )
            
            # 计算最终匹配度分数（0-100）
            # 综合考虑相似度和置信度
            final_similarity = (detailed_similarity * 0.7) + (confidence * 0.3)
            match_score = int(final_similarity * 100)
            
            # 生成详细结果
            result = {
                'success': True,
                'target_major': target_major,
                'match_score': match_score,
                'matched_path': best_path_info['label'],
                'path_confidence': round(confidence, 3),
                'detailed_similarity': round(detailed_similarity, 3),
                'path_coverage': round(best_path_info['coverage'], 3),
                'path_representativeness': round(best_path_info['representativeness'], 3),
                'success_indicators': best_path_info.get('success_indicators', {}),
                'match_level': self._get_match_level(match_score),
                'recommendation': self._generate_recommendation(match_score, best_path_info)
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
        if score >= 80:
            return "高匹配"
        elif score >= 65:
            return "中等匹配"
        elif score >= 50:
            return "低匹配"
        else:
            return "不匹配"
    
    def _generate_recommendation(self, score: int, path_info: Dict[str, Any]) -> str:
        """生成匹配建议"""
        if score >= 80:
            return f"您的背景与{path_info['label']}路径高度匹配，建议积极申请。"
        elif score >= 65:
            return f"您的背景与{path_info['label']}路径较为匹配，可以考虑申请，建议适当提升相关背景。"
        elif score >= 50:
            return f"您的背景与{path_info['label']}路径存在一定差距，需要重点提升相关能力后再申请。"
        else:
            return "建议重新考虑专业选择，或大幅提升相关背景后再申请。"
    
    def batch_calculate_matches(self, student_features: Dict[str, Any], target_majors: List[str]) -> Dict[str, Any]:
        """
        批量计算学生与多个专业的匹配度
        
        Args:
            student_features: 学生特征字典
            target_majors: 目标专业列表
            
        Returns:
            批量匹配结果字典
        """
        results = {}
        
        for major in target_majors:
            results[major] = self.calculate_match_score(student_features, major)
        
        # 按匹配度排序
        successful_matches = {k: v for k, v in results.items() if v.get('success', False)}
        if successful_matches:
            sorted_matches = sorted(
                successful_matches.items(), 
                key=lambda x: x[1]['match_score'], 
                reverse=True
            )
            
            return {
                'success': True,
                'total_majors': len(target_majors),
                'successful_matches': len(successful_matches),
                'results': dict(sorted_matches),
                'top_recommendations': [
                    {
                        'major': k,
                        'score': v['match_score'],
                        'level': v['match_level'],
                        'path': v['matched_path']
                    }
                    for k, v in sorted_matches[:5]  # 前5个推荐
                ]
            }
        else:
            return {
                'success': False,
                'error': '所有专业匹配均失败',
                'results': results
            }
    
    def get_available_majors(self) -> List[str]:
        """获取所有可用的专业列表"""
        return list(self.path_profiles.keys()) if self.path_profiles else []
    
    def get_major_info(self, major_name: str) -> Dict[str, Any]:
        """获取专业的详细信息"""
        if major_name not in self.path_profiles:
            return {'success': False, 'error': f'专业 "{major_name}" 未找到'}
        
        major_data = self.path_profiles[major_name]
        
        return {
            'success': True,
            'major_name': major_name,
            'total_applications': major_data['summary']['total_applications'],
            'num_paths': major_data['summary']['num_paths'],
            'clustering_quality': round(major_data['summary']['clustering_quality'], 3),
            'paths': {
                path_key: {
                    'label': path_info['label'],
                    'sample_size': path_info['sample_size'],
                    'coverage': round(path_info['coverage'], 3),
                    'representativeness': round(path_info['representativeness'], 3),
                    'success_indicators': path_info.get('success_indicators', {})
                }
                for path_key, path_info in major_data['paths'].items()
            }
        }


def main():
    """主函数 - 演示使用"""
    # 配置路径
    path_profiles_path = 'data/path_profiles/path_profiles.json'
    
    # 创建匹配计算器
    calculator = MatchingCalculator(path_profiles_path)
    
    # 示例学生特征
    student_example = {
        'source_university_tier_score': 85,      # 985院校
        'gpa_percentile': 78,                    # GPA百分位
        'major_matching_score': 0.8,             # 专业匹配度
        'language_score_normalized': 75,         # 语言成绩
        'work_experience_years': 1,              # 工作经验
        'work_relevance_score': 0.6,             # 工作相关性
        'target_university_tier_score': 90,      # 目标院校分数
        'university_matching_score': 0.85,       # 院校匹配度
        'competition_index': 6.5,                # 竞争指数
        'academic_strength_score': 80,           # 学术实力
        'applicant_comprehensive_strength': 75   # 综合实力
    }
    
    # 测试单个专业匹配
    print("=== 单个专业匹配测试 ===")
    result = calculator.calculate_match_score(student_example, "Master of Commerce")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试批量匹配
    print("\n=== 批量专业匹配测试 ===")
    test_majors = ["Master of Commerce", "Master of Computer Science", "Master of Economics"]
    batch_result = calculator.batch_calculate_matches(student_example, test_majors)
    print(json.dumps(batch_result, ensure_ascii=False, indent=2))
    
    return calculator


if __name__ == "__main__":
    main()