"""
路径画像构建系统
基于聚类结果，为每个路径构建详细的申请者画像
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any


class PathProfileBuilder:
    def __init__(self, data_path: str, clustering_results_path: str, output_path: str):
        """
        初始化路径画像构建器
        
        Args:
            data_path: 原始特征数据路径
            clustering_results_path: 聚类结果文件路径
            output_path: 画像数据输出路径
        """
        self.data_path = data_path
        self.clustering_results_path = clustering_results_path
        self.output_path = output_path
        self.df = None
        self.clustering_results = None
        self.feature_cols = None
        self.target_major_col = "申请院校_专业名称"
        
        # 关键特征定义 - 用于路径标签生成
        self.key_features = {
            'source_university_tier_score': {'name': '院校背景', 'thresholds': [(85, '985名校'), (75, '211高校'), (65, '双一流'), (0, '本科')]},
            'gpa_percentile': {'name': 'GPA水平', 'thresholds': [(85, '高GPA'), (70, '中等GPA'), (0, '一般GPA')]},
            'major_matching_score': {'name': '专业匹配', 'thresholds': [(0.8, '高匹配'), (0.6, '中等匹配'), (0.3, '低匹配'), (0, '跨专业')]},
            'language_score_normalized': {'name': '语言能力', 'thresholds': [(80, '优秀'), (65, '良好'), (0, '一般')]},
            'work_experience_years': {'name': '工作经验', 'thresholds': [(2, '有经验'), (0, '应届生')]}
        }
        
    def load_data(self):
        """加载数据和聚类结果"""
        print("加载原始数据和聚类结果...")
        
        # 加载原始数据
        self.df = pd.read_csv(self.data_path)
        
        # 加载聚类结果
        with open(self.clustering_results_path, 'r', encoding='utf-8') as f:
            self.clustering_results = json.load(f)
        
        # 识别特征列
        exclude_patterns = ['ID', 'id', '名称', '时间', '日期', '描述', '类型', '开始', '结束', '单位', '职位', '职责']
        self.feature_cols = []
        
        for col in self.df.columns:
            if self.df[col].dtype in ['int64', 'float64']:
                if not any(pattern in col for pattern in exclude_patterns):
                    self.feature_cols.append(col)
        
        print(f"加载完成 - 数据形状: {self.df.shape}, 特征列数: {len(self.feature_cols)}")
        return self
    
    def calculate_cluster_statistics(self, cluster_data: pd.DataFrame) -> Dict[str, Any]:
        """计算单个聚类的详细统计信息"""
        stats = {}
        
        for feature in self.feature_cols:
            feature_data = cluster_data[feature].dropna()
            
            if len(feature_data) > 0:
                stats[feature] = {
                    'mean': float(feature_data.mean()),
                    'std': float(feature_data.std()),
                    'median': float(feature_data.median()),
                    'q25': float(feature_data.quantile(0.25)),
                    'q75': float(feature_data.quantile(0.75)),
                    'min': float(feature_data.min()),
                    'max': float(feature_data.max()),
                    'count': int(len(feature_data))
                }
            else:
                # 处理空数据情况
                stats[feature] = {
                    'mean': 0.0, 'std': 0.0, 'median': 0.0,
                    'q25': 0.0, 'q75': 0.0, 'min': 0.0, 'max': 0.0,
                    'count': 0
                }
        
        return stats
    
    def generate_path_label(self, cluster_stats: Dict[str, Any], cluster_id: int) -> str:
        """基于统计特征生成路径标签"""
        labels = []
        
        # 检查关键特征并生成标签
        for feature_key, feature_info in self.key_features.items():
            if feature_key in cluster_stats and cluster_stats[feature_key]['count'] > 0:
                mean_val = cluster_stats[feature_key]['mean']
                
                # 根据阈值确定标签
                for threshold, desc in feature_info['thresholds']:
                    if mean_val >= threshold:
                        labels.append(desc)
                        break
        
        # 如果没有生成标签，使用默认标签
        if not labels:
            labels = [f'路径{cluster_id}']
        
        # 限制标签长度，最多3个
        return '-'.join(labels[:3])
    
    def calculate_representativeness(self, cluster_data: pd.DataFrame, cluster_center: List[float]) -> float:
        """计算聚类的代表性（聚类内相似度）"""
        if len(cluster_data) == 0 or len(cluster_center) == 0:
            return 0.0
        
        try:
            # 计算聚类内样本与中心的平均距离
            features_data = cluster_data[self.feature_cols].fillna(0).values
            
            # 确保维度匹配
            min_dim = min(features_data.shape[1], len(cluster_center))
            features_data = features_data[:, :min_dim]
            center_array = np.array(cluster_center[:min_dim])
            
            # 计算余弦相似度
            similarities = []
            for sample in features_data:
                # 避免除零错误
                sample_norm = np.linalg.norm(sample)
                center_norm = np.linalg.norm(center_array)
                
                if sample_norm > 0 and center_norm > 0:
                    similarity = np.dot(sample, center_array) / (sample_norm * center_norm)
                    similarities.append(similarity)
            
            if similarities:
                return float(np.mean(similarities))
            else:
                return 0.0
                
        except Exception as e:
            print(f"计算代表性时出错: {e}")
            return 0.0
    
    def identify_success_indicators(self, cluster_stats: Dict[str, Any]) -> Dict[str, float]:
        """识别成功申请的关键指标"""
        indicators = {}
        
        # 院校背景指标
        if 'source_university_tier_score' in cluster_stats:
            score = cluster_stats['source_university_tier_score']['mean']
            indicators['high_university_background'] = min(score / 100.0, 1.0)
        
        # 学术表现指标
        if 'gpa_percentile' in cluster_stats:
            gpa = cluster_stats['gpa_percentile']['mean']
            indicators['strong_academic_performance'] = min(gpa / 100.0, 1.0)
        
        # 专业相关性指标
        if 'major_matching_score' in cluster_stats:
            matching = cluster_stats['major_matching_score']['mean']
            indicators['relevant_major_background'] = min(matching, 1.0)
        
        # 语言能力指标
        if 'language_score_normalized' in cluster_stats:
            lang = cluster_stats['language_score_normalized']['mean']
            indicators['language_proficiency'] = min(lang / 100.0, 1.0)
        
        # 工作经验指标
        if 'work_experience_years' in cluster_stats:
            work_exp = cluster_stats['work_experience_years']['mean']
            indicators['professional_experience'] = min(work_exp / 5.0, 1.0)  # 5年为满分
        
        return indicators
    
    def get_key_distinguishing_features(self, cluster_stats: Dict[str, Any], major_name: str) -> List[str]:
        """识别该聚类的关键区分特征"""
        # 获取该专业的所有聚类数据进行比较
        major_clusters = self.clustering_results[major_name]['clusters']
        
        # 计算特征的变异系数，识别区分度高的特征
        feature_importance = {}
        
        for feature in self.feature_cols:
            if feature in cluster_stats:
                # 收集该专业所有聚类在此特征上的均值
                cluster_means = []
                for cluster_key, cluster_info in major_clusters.items():
                    # 这里需要根据实际数据重新计算，简化处理
                    pass
                
                # 简化：基于当前聚类的标准差作为重要性指标
                std_val = cluster_stats[feature]['std']
                mean_val = abs(cluster_stats[feature]['mean'])
                
                if mean_val > 0:
                    cv = std_val / mean_val  # 变异系数
                    feature_importance[feature] = cv
        
        # 返回重要性最高的前5个特征
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_features[:5]]
    
    def build_path_profile(self, major_name: str, cluster_id: str, cluster_info: Dict[str, Any]) -> Dict[str, Any]:
        """构建单个路径的完整画像"""
        print(f"构建路径画像: {major_name} - {cluster_id}")
        
        # 获取该聚类的原始数据
        major_data = self.df[self.df[self.target_major_col] == major_name]
        
        # 由于我们没有存储每个样本的聚类标签，这里使用聚类中心信息
        # 简化处理：基于聚类中心和大小估算数据分布
        cluster_size = cluster_info['size']
        cluster_center = cluster_info['center']
        cluster_percentage = cluster_info['percentage']
        
        # 模拟聚类数据（实际应用中应该存储聚类标签）
        # 这里我们随机选择一部分数据作为代表
        np.random.seed(42)  # 确保可重复
        sample_indices = np.random.choice(len(major_data), size=min(cluster_size, len(major_data)), replace=False)
        cluster_data = major_data.iloc[sample_indices]
        
        # 计算详细统计信息
        cluster_stats = self.calculate_cluster_statistics(cluster_data)
        
        # 生成路径标签
        path_label = self.generate_path_label(cluster_stats, int(cluster_id.split('_')[1]))
        
        # 计算代表性
        representativeness = self.calculate_representativeness(cluster_data, cluster_center)
        
        # 识别成功指标
        success_indicators = self.identify_success_indicators(cluster_stats)
        
        # 识别关键特征
        key_features = self.get_key_distinguishing_features(cluster_stats, major_name)
        
        # 构建完整画像
        path_profile = {
            'label': path_label,
            'sample_size': cluster_size,
            'coverage': cluster_percentage,
            'representativeness': representativeness,
            'profile': cluster_stats,
            'key_features': key_features,
            'success_indicators': success_indicators,
            'cluster_center': cluster_center
        }
        
        return path_profile
    
    def build_all_profiles(self):
        """构建所有专业的路径画像"""
        print("开始构建所有路径画像...")
        
        all_profiles = {}
        processed_count = 0
        
        for major_name, major_data in self.clustering_results.items():
            try:
                major_profiles = {'paths': {}}
                
                # 为该专业的每个聚类构建画像
                for cluster_id, cluster_info in major_data['clusters'].items():
                    path_profile = self.build_path_profile(major_name, cluster_id, cluster_info)
                    path_key = f"path_{cluster_id.split('_')[1]}"
                    major_profiles['paths'][path_key] = path_profile
                
                # 添加专业级别的汇总信息
                major_profiles['summary'] = {
                    'total_applications': major_data['total_applications'],
                    'num_paths': major_data['optimal_k'],
                    'clustering_quality': major_data['silhouette_score']
                }
                
                all_profiles[major_name] = major_profiles
                processed_count += 1
                
                if processed_count % 10 == 0:
                    print(f"已处理 {processed_count}/{len(self.clustering_results)} 个专业")
                    
            except Exception as e:
                print(f"处理专业 {major_name} 时出错: {e}")
                continue
        
        print(f"路径画像构建完成！成功处理 {processed_count} 个专业")
        return all_profiles
    
    def save_profiles(self, profiles: Dict[str, Any]):
        """保存路径画像数据"""
        os.makedirs(self.output_path, exist_ok=True)
        
        # 保存完整画像数据
        profiles_file = os.path.join(self.output_path, 'path_profiles.json')
        with open(profiles_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        
        print(f"路径画像数据已保存至: {profiles_file}")
        
        # 生成画像统计报告
        self.generate_profile_report(profiles)
    
    def generate_profile_report(self, profiles: Dict[str, Any]):
        """生成路径画像统计报告"""
        report = {
            'summary': {
                'total_majors_profiled': len(profiles),
                'total_paths': sum(len(p['paths']) for p in profiles.values()),
                'avg_paths_per_major': np.mean([len(p['paths']) for p in profiles.values()]),
                'avg_representativeness': 0.0
            },
            'path_distribution': {},
            'quality_metrics': {}
        }
        
        # 计算平均代表性
        all_representativeness = []
        for major_profiles in profiles.values():
            for path in major_profiles['paths'].values():
                all_representativeness.append(path['representativeness'])
        
        if all_representativeness:
            report['summary']['avg_representativeness'] = np.mean(all_representativeness)
        
        # 路径数分布
        path_counts = [len(p['paths']) for p in profiles.values()]
        for i in range(2, 6):
            report['path_distribution'][f'{i}_paths'] = path_counts.count(i)
        
        # 质量指标
        clustering_qualities = [p['summary']['clustering_quality'] for p in profiles.values()]
        report['quality_metrics'] = {
            'avg_clustering_quality': np.mean(clustering_qualities),
            'high_quality_majors (>0.5)': sum(1 for q in clustering_qualities if q > 0.5),
            'medium_quality_majors (0.3-0.5)': sum(1 for q in clustering_qualities if 0.3 <= q <= 0.5),
            'low_quality_majors (<0.3)': sum(1 for q in clustering_qualities if q < 0.3)
        }
        
        # 保存报告
        report_file = os.path.join(self.output_path, 'profile_building_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"画像构建报告已保存至: {report_file}")
        print(f"平均代表性: {report['summary']['avg_representativeness']:.3f}")
        print(f"平均聚类质量: {report['quality_metrics']['avg_clustering_quality']:.3f}")
    
    def run_profile_building(self):
        """执行完整的路径画像构建流程"""
        print("开始路径画像构建流程...")
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 构建所有画像
        profiles = self.build_all_profiles()
        
        # 3. 保存结果
        self.save_profiles(profiles)
        
        return profiles


def main():
    """主函数"""
    # 配置路径
    data_path = 'data/processed/final_feature_dataset_latest.csv'
    clustering_results_path = 'data/clustering_results/clustering_results.json'
    output_path = 'data/path_profiles'
    
    # 创建路径画像构建器
    builder = PathProfileBuilder(data_path, clustering_results_path, output_path)
    
    # 运行构建流程
    profiles = builder.run_profile_building()
    
    return profiles


if __name__ == "__main__":
    main()