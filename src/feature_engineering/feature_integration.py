"""
特征整合模块
整合所有已生成的特征，生成最终的特征数据集
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class FeatureIntegrator:
    """特征整合器"""
    
    def __init__(self, data_path=None):
        """
        初始化特征整合器
        
        Parameters:
        -----------
        data_path : str, optional
            数据文件路径，如果不提供则使用最新的全特征数据
        """
        self.data_path = data_path
        self.data = None
        self.feature_groups = {}
        self.feature_metadata = {}
        
    def load_data(self):
        """加载数据"""
        if self.data_path is None:
            # 查找最新的全特征数据文件
            processed_dir = "data/processed"
            files = [f for f in os.listdir(processed_dir) if f.startswith("data_with_all_features")]
            if files:
                files.sort(reverse=True)  # 按时间戳降序
                self.data_path = os.path.join(processed_dir, files[0])
                print(f"使用最新数据文件: {files[0]}")
            else:
                raise FileNotFoundError("未找到全特征数据文件")
        
        self.data = pd.read_csv(self.data_path, encoding='utf-8-sig')
        print(f"数据加载完成，共{len(self.data)}行，{len(self.data.columns)}列")
        return self.data
    
    def categorize_features(self):
        """将特征按类别分组"""
        if self.data is None:
            self.load_data()
            
        columns = self.data.columns.tolist()
        
        # 定义特征分组
        self.feature_groups = {
            # 基础信息
            'basic_info': [
                '申请院校_院校ID', '申请院校_专业ID', '申请院校_院校名称', 
                '申请院校_专业名称', '申请院校_课程类型'
            ],
            
            # 教育背景
            'education_background': [
                '教育经历_毕业院校', '教育经历_所学专业', '教育经历_学历层次',
                '教育经历_就读国家', '教育经历_入学时间', '教育经历_毕业时间',
                '教育经历_GPA成绩', '教育经历_是否有退学或开除经历'
            ],
            
            # 标准化教育信息
            'standardized_education': [
                '教育经历_GPA成绩_百分制', '教育经历_学历层次_标准化',
                '教育经历_GPA成绩_百分制_修复', '申请院校_院校名称_标准化',
                '申请院校_专业名称_标准化', '教育经历_所学专业_标准化'
            ],
            
            # 源院校特征
            'source_university_features': [
                'source_university_tier', 'source_university_tier_desc',
                'source_is_985', 'source_is_211', 'source_is_double_first_class',
                'source_university_tier_score'
            ],
            
            # 目标院校特征
            'target_university_features': [
                'target_university_tier', 'target_university_tier_desc',
                'target_university_tier_score', 'target_university_qs_rank',
                'target_university_application_volume', 'target_university_avg_applicant_gpa',
                'target_university_competitiveness'
            ],
            
            # 院校匹配特征
            'university_matching_features': [
                'university_tier_gap', 'university_score_gap',
                'university_matching_score', 'university_matching_level'
            ],
            
            # 竞争度特征
            'competition_features': [
                'competition_index', 'competition_level',
                'target_university_competition', 'target_major_popularity',
                'competition_level_new'
            ],
            
            # 学术实力特征
            'academic_strength_features': [
                'applicant_comprehensive_strength', 'estimated_success_probability',
                'success_probability_level', 'gpa_percentile', 'gpa_relative_rank',
                'academic_strength_score'
            ],
            
            # 语言考试特征
            'language_features': [
                '语言考试_考试类型', '语言考试_考试成绩', '语言考试_考试时间',
                'has_language_score', 'language_test_type', 'language_score_normalized'
            ],
            
            # 工作经历特征
            'work_experience_features': [
                '工作经历_开始时间', '工作经历_结束时间', '工作经历_工作单位',
                '工作经历_职位名称', '工作经历_工作职责',
                'has_work_experience', 'work_experience_years', 'work_relevance_score'
            ],
            
            # 专业匹配度特征
            'major_matching_features': [
                'major_matching_score', 'cross_major_type', 'major_matching_description',
                'is_same_field', 'major_matching_level', '申请专业主分类', '申请专业子分类',
                '申请专业分类置信度', '教育专业主分类', '教育专业子分类', '教育专业分类置信度'
            ],
            
            # 时间特征
            'time_features': [
                'application_year', 'application_season', 'time_to_graduation'
            ]
        }
        
        # 检查实际存在的列
        existing_columns = set(columns)
        for group_name, feature_list in self.feature_groups.items():
            existing_features = [f for f in feature_list if f in existing_columns]
            missing_features = [f for f in feature_list if f not in existing_columns]
            
            self.feature_groups[group_name] = existing_features
            if missing_features:
                print(f"警告: {group_name} 组缺失特征: {missing_features}")
        
        print(f"特征分组完成，共分为{len(self.feature_groups)}个组")
        return self.feature_groups
    
    def create_feature_metadata(self):
        """创建特征元数据"""
        if self.data is None:
            self.load_data()
            
        if not self.feature_groups:
            self.categorize_features()
            
        self.feature_metadata = {}
        
        for column in self.data.columns:
            dtype = str(self.data[column].dtype)
            null_count = self.data[column].isnull().sum()
            null_rate = null_count / len(self.data)
            unique_count = self.data[column].nunique()
            
            # 判断特征类型
            if dtype in ['int64', 'float64']:
                feature_type = 'numerical'
                min_val = self.data[column].min()
                max_val = self.data[column].max()
                mean_val = self.data[column].mean()
                std_val = self.data[column].std()
                stats = {
                    'min': min_val,
                    'max': max_val,
                    'mean': mean_val,
                    'std': std_val
                }
            else:
                feature_type = 'categorical'
                stats = {
                    'top_values': self.data[column].value_counts().head(5).to_dict()
                }
            
            # 找到特征所属组
            feature_group = None
            for group_name, features in self.feature_groups.items():
                if column in features:
                    feature_group = group_name
                    break
            
            self.feature_metadata[column] = {
                'group': feature_group,
                'type': feature_type,
                'dtype': dtype,
                'null_count': null_count,
                'null_rate': null_rate,
                'unique_count': unique_count,
                'stats': stats
            }
        
        return self.feature_metadata
    
    def validate_data_quality(self):
        """验证数据质量"""
        if self.data is None:
            self.load_data()
            
        quality_report = {
            'total_records': len(self.data),
            'total_features': len(self.data.columns),
            'duplicate_records': self.data.duplicated().sum(),
            'features_with_missing': 0,
            'high_missing_features': [],
            'constant_features': [],
            'data_types': {}
        }
        
        # 检查缺失值
        missing_summary = self.data.isnull().sum()
        features_with_missing = (missing_summary > 0).sum()
        quality_report['features_with_missing'] = features_with_missing
        
        # 高缺失率特征（>50%）
        high_missing = missing_summary[missing_summary / len(self.data) > 0.5]
        quality_report['high_missing_features'] = high_missing.index.tolist()
        
        # 常量特征
        for col in self.data.columns:
            if self.data[col].nunique() <= 1:
                quality_report['constant_features'].append(col)
        
        # 数据类型统计
        dtype_counts = self.data.dtypes.value_counts()
        quality_report['data_types'] = dtype_counts.to_dict()
        
        return quality_report
    
    def generate_final_dataset(self, output_path=None, exclude_columns=None):
        """
        生成最终的特征数据集
        
        Parameters:
        -----------
        output_path : str, optional
            输出文件路径
        exclude_columns : list, optional
            要排除的列名列表
        """
        if self.data is None:
            self.load_data()
            
        # 创建最终数据集
        final_data = self.data.copy()
        
        # 排除指定列
        if exclude_columns:
            existing_exclude = [col for col in exclude_columns if col in final_data.columns]
            final_data = final_data.drop(columns=existing_exclude)
            print(f"排除了{len(existing_exclude)}个列: {existing_exclude}")
        
        # 数据类型优化
        final_data = self._optimize_dtypes(final_data)
        
        # 保存最终数据集
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"data/processed/final_feature_dataset_{timestamp}.csv"
        
        final_data.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"最终特征数据集已保存到: {output_path}")
        print(f"数据集包含 {len(final_data)} 行，{len(final_data.columns)} 列")
        
        return final_data, output_path
    
    def _optimize_dtypes(self, df):
        """优化数据类型以节省内存"""
        for col in df.columns:
            col_type = df[col].dtype
            
            # 优化整数类型
            if col_type == 'int64':
                col_min = df[col].min()
                col_max = df[col].max()
                
                if col_min >= 0:  # 无符号整数
                    if col_max < 255:
                        df[col] = df[col].astype('uint8')
                    elif col_max < 65535:
                        df[col] = df[col].astype('uint16')
                    elif col_max < 4294967295:
                        df[col] = df[col].astype('uint32')
                else:  # 有符号整数
                    if col_min > -128 and col_max < 127:
                        df[col] = df[col].astype('int8')
                    elif col_min > -32768 and col_max < 32767:
                        df[col] = df[col].astype('int16')
                    elif col_min > -2147483648 and col_max < 2147483647:
                        df[col] = df[col].astype('int32')
            
            # 优化浮点类型
            elif col_type == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
            
            # 优化分类类型
            elif col_type == 'object':
                unique_count = df[col].nunique()
                total_count = len(df[col])
                if unique_count / total_count < 0.5:  # 如果唯一值比例小于50%，转为分类类型
                    df[col] = df[col].astype('category')
        
        return df
    
    def get_feature_summary(self):
        """获取特征总结"""
        if not self.feature_metadata:
            self.create_feature_metadata()
            
        summary = {
            'total_features': len(self.feature_metadata),
            'feature_groups': {},
            'data_types': {},
            'missing_data_summary': {}
        }
        
        # 按组统计
        for group_name, features in self.feature_groups.items():
            summary['feature_groups'][group_name] = len(features)
        
        # 按数据类型统计
        type_counts = {}
        for feature, metadata in self.feature_metadata.items():
            ftype = metadata['type']
            type_counts[ftype] = type_counts.get(ftype, 0) + 1
        summary['data_types'] = type_counts
        
        # 缺失数据统计
        null_rates = [metadata['null_rate'] for metadata in self.feature_metadata.values()]
        summary['missing_data_summary'] = {
            'features_with_missing': sum(1 for rate in null_rates if rate > 0),
            'avg_missing_rate': np.mean(null_rates),
            'max_missing_rate': max(null_rates),
            'features_high_missing': sum(1 for rate in null_rates if rate > 0.5)
        }
        
        return summary

def main():
    """主函数"""
    print("=== 特征整合开始 ===")
    
    # 创建特征整合器
    integrator = FeatureIntegrator()
    
    # 加载数据
    data = integrator.load_data()
    
    # 特征分组
    feature_groups = integrator.categorize_features()
    
    # 创建特征元数据
    metadata = integrator.create_feature_metadata()
    
    # 验证数据质量
    quality_report = integrator.validate_data_quality()
    
    # 生成最终数据集
    final_data, output_path = integrator.generate_final_dataset()
    
    # 获取特征总结
    summary = integrator.get_feature_summary()
    
    # 输出结果
    print("\n=== 特征整合完成 ===")
    print(f"总特征数: {summary['total_features']}")
    print(f"特征分组: {summary['feature_groups']}")
    print(f"数据类型分布: {summary['data_types']}")
    print(f"缺失数据概况: {summary['missing_data_summary']}")
    print(f"最终数据集路径: {output_path}")
    
    return integrator, final_data

if __name__ == "__main__":
    integrator, final_data = main()