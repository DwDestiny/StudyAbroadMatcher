"""
专业路径聚类分析模块
基于历史成功申请数据，对申请量≥100的专业进行K-means聚类，识别不同的成功申请路径
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class ProfessionalPathClustering:
    def __init__(self, data_path, output_path, min_applications=100):
        """
        初始化聚类分析器
        
        Args:
            data_path: 特征数据文件路径
            output_path: 聚类结果输出路径
            min_applications: 最小申请量阈值
        """
        self.data_path = data_path
        self.output_path = output_path
        self.min_applications = min_applications
        self.df = None
        self.target_major_col = None
        self.feature_cols = None
        
    def load_data(self):
        """加载和预处理数据"""
        print("正在加载数据...")
        self.df = pd.read_csv(self.data_path)
        print(f"数据形状: {self.df.shape}")
        
        # 自动识别目标专业列（包含"专业名称"的列）
        for col in self.df.columns:
            if '专业名称' in col:
                self.target_major_col = col
                break
        
        if not self.target_major_col:
            # 如果没找到中文列名，使用第4列（索引3）
            self.target_major_col = self.df.columns[3]
        
        print(f"目标专业列: {self.target_major_col}")
        
        # 识别特征列（数值型列，排除ID和名称列）
        exclude_patterns = ['ID', 'id', '名称', '时间', '日期']
        self.feature_cols = []
        
        for col in self.df.columns:
            if self.df[col].dtype in ['int64', 'float64']:
                # 排除明显的非特征列
                if not any(pattern in col for pattern in exclude_patterns):
                    self.feature_cols.append(col)
        
        print(f"识别到 {len(self.feature_cols)} 个特征列")
        
        return self
    
    def filter_eligible_majors(self):
        """筛选申请量≥阈值的专业"""
        print(f"筛选申请量≥{self.min_applications}的专业...")
        
        major_counts = self.df[self.target_major_col].value_counts()
        eligible_majors = major_counts[major_counts >= self.min_applications].index.tolist()
        
        print(f"总专业数: {len(major_counts)}")
        print(f"符合条件的专业数: {len(eligible_majors)}")
        print(f"覆盖申请量: {major_counts[major_counts >= self.min_applications].sum()}")
        
        return eligible_majors
    
    def optimize_clustering(self, data, k_range=(2, 6)):
        """优化聚类参数"""
        best_k = 2
        best_score = -1
        scores = {}
        
        for k in range(k_range[0], k_range[1]):
            if len(data) < k:
                continue
                
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(data)
            
            # 检查聚类结果的有效性
            if len(np.unique(labels)) < k:
                continue
                
            silhouette_avg = silhouette_score(data, labels)
            scores[k] = silhouette_avg
            
            # 选择最佳K值：轮廓系数最高且>0.3
            if silhouette_avg > 0.3 and silhouette_avg > best_score:
                best_score = silhouette_avg
                best_k = k
        
        return best_k, best_score, scores
    
    def cluster_single_major(self, major_name):
        """对单个专业执行聚类分析"""
        print(f"分析专业: {major_name}")
        
        # 提取该专业的数据
        major_data = self.df[self.df[self.target_major_col] == major_name]
        features = major_data[self.feature_cols].fillna(0)
        
        # 数据标准化
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # 优化聚类参数
        best_k, best_score, all_scores = self.optimize_clustering(features_scaled)
        
        # 执行最佳聚类
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features_scaled)
        
        # 计算各聚类的统计信息
        clusters_info = {}
        for cluster_id in range(best_k):
            cluster_mask = labels == cluster_id
            cluster_data = features[cluster_mask]
            cluster_size = cluster_mask.sum()
            
            # 计算聚类中心（原始特征空间）
            cluster_center = cluster_data.mean().values
            
            # 生成聚类描述
            description = self.generate_cluster_description(cluster_data, cluster_id)
            
            clusters_info[f'cluster_{cluster_id}'] = {
                'size': int(cluster_size),
                'percentage': float(cluster_size / len(major_data)),
                'center': cluster_center.tolist(),
                'description': description
            }
        
        # 计算特征重要性
        feature_importance = self.calculate_feature_importance(features_scaled, labels)
        
        result = {
            'total_applications': len(major_data),
            'optimal_k': best_k,
            'silhouette_score': float(best_score),
            'all_scores': {str(k): float(v) for k, v in all_scores.items()},
            'clusters': clusters_info,
            'feature_importance': feature_importance
        }
        
        return result
    
    def generate_cluster_description(self, cluster_data, cluster_id):
        """生成聚类描述标签"""
        descriptions = []
        
        # 基于主要特征生成描述
        key_features = [
            ('source_university_score', '院校背景', [(85, '985'), (75, '211'), (65, '双一流'), (0, '普通本科')]),
            ('gpa_percentile', 'GPA水平', [(85, '高GPA'), (75, '中等GPA'), (0, '一般GPA')]),
            ('major_matching_score', '专业匹配', [(0.8, '高匹配'), (0.6, '中等匹配'), (0, '跨专业')])
        ]
        
        for feature_name, feature_label, thresholds in key_features:
            if feature_name in cluster_data.columns:
                mean_val = cluster_data[feature_name].mean()
                
                for threshold, desc in thresholds:
                    if mean_val >= threshold:
                        descriptions.append(desc)
                        break
        
        if descriptions:
            return '-'.join(descriptions[:3])  # 最多3个标签
        else:
            return f'路径{cluster_id}'
    
    def calculate_feature_importance(self, features_scaled, labels):
        """计算特征重要性"""
        feature_importance = {}
        
        # 使用方差分析计算特征区分度
        for i, feature in enumerate(self.feature_cols):
            cluster_means = []
            for cluster_id in np.unique(labels):
                cluster_mask = labels == cluster_id
                cluster_mean = features_scaled[cluster_mask, i].mean()
                cluster_means.append(cluster_mean)
            
            # 计算聚类间方差作为重要性指标
            importance = np.var(cluster_means)
            feature_importance[feature] = float(importance)
        
        # 归一化重要性分数
        total_importance = sum(feature_importance.values())
        if total_importance > 0:
            feature_importance = {k: v/total_importance for k, v in feature_importance.items()}
        
        # 返回前10个最重要的特征
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_features[:10])
    
    def run_clustering_analysis(self):
        """执行完整的聚类分析流程"""
        print("开始专业路径聚类分析...")
        
        # 加载数据
        self.load_data()
        
        # 筛选符合条件的专业
        eligible_majors = self.filter_eligible_majors()
        
        # 创建输出目录
        os.makedirs(self.output_path, exist_ok=True)
        
        # 对每个专业执行聚类分析
        all_results = {}
        successful_analysis = 0
        
        for i, major in enumerate(eligible_majors):  # 处理所有符合条件的专业
            try:
                print(f"正在处理: {major} ({i+1}/{len(eligible_majors)})")
                result = self.cluster_single_major(major)
                all_results[major] = result
                successful_analysis += 1
                
                if (i + 1) % 20 == 0:
                    print(f"已完成 {i + 1}/{len(eligible_majors)} 个专业的分析，成功率: {successful_analysis/(i+1)*100:.1f}%")
                    
            except Exception as e:
                print(f"专业 {major} 分析失败: {str(e)}")
                continue
        
        # 保存聚类结果
        output_file = os.path.join(self.output_path, 'clustering_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"聚类分析完成！")
        print(f"成功分析专业数: {successful_analysis}")
        print(f"结果保存至: {output_file}")
        
        # 生成分析统计报告
        self.generate_analysis_report(all_results)
        
        return all_results
    
    def generate_analysis_report(self, results):
        """生成聚类分析统计报告"""
        report = {
            'summary': {
                'total_majors_analyzed': len(results),
                'avg_silhouette_score': np.mean([r['silhouette_score'] for r in results.values()]),
                'avg_clusters_per_major': np.mean([r['optimal_k'] for r in results.values()]),
                'total_applications_covered': sum([r['total_applications'] for r in results.values()])
            },
            'score_distribution': {},
            'cluster_size_distribution': {}
        }
        
        # 轮廓系数分布
        scores = [r['silhouette_score'] for r in results.values()]
        report['score_distribution'] = {
            'excellent (>0.5)': sum(1 for s in scores if s > 0.5),
            'good (0.3-0.5)': sum(1 for s in scores if 0.3 <= s <= 0.5),
            'poor (<0.3)': sum(1 for s in scores if s < 0.3)
        }
        
        # 聚类数分布
        k_values = [r['optimal_k'] for r in results.values()]
        for k in range(2, 6):
            report['cluster_size_distribution'][f'{k}_clusters'] = k_values.count(k)
        
        # 保存报告
        report_file = os.path.join(self.output_path, 'clustering_analysis_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"分析报告保存至: {report_file}")
        print(f"平均轮廓系数: {report['summary']['avg_silhouette_score']:.3f}")
        print(f"平均聚类数: {report['summary']['avg_clusters_per_major']:.1f}")


def main():
    """主函数"""
    # 配置路径
    data_path = 'data/processed/final_feature_dataset_latest.csv'
    output_path = 'data/clustering_results'
    
    # 创建聚类分析器
    clustering = ProfessionalPathClustering(data_path, output_path, min_applications=100)
    
    # 运行分析
    results = clustering.run_clustering_analysis()
    
    return results


if __name__ == "__main__":
    main()