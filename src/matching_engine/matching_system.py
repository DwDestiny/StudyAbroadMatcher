"""
统一匹配系统API接口
整合聚类分析、路径画像构建、匹配度计算的完整服务
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 导入核心模块
try:
    from .clustering_analysis import ProfessionalPathClustering
    from .path_profile_builder import PathProfileBuilder  
    from .matching_calculator import MatchingCalculator
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from clustering_analysis import ProfessionalPathClustering
    from path_profile_builder import PathProfileBuilder  
    from matching_calculator import MatchingCalculator


class StudentMajorMatchingSystem:
    """学生专业匹配系统 - 统一API接口"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化匹配系统
        
        Args:
            config: 系统配置字典
        """
        # 默认配置
        self.config = {
            'data_path': 'data/processed/final_feature_dataset_latest.csv',
            'clustering_output_path': 'data/clustering_results',
            'profiles_output_path': 'data/path_profiles', 
            'min_applications': 100,
            'enable_caching': True,
            'log_level': 'INFO'
        }
        
        # 更新用户配置
        if config:
            self.config.update(config)
        
        # 初始化组件
        self.clustering_analyzer = None
        self.profile_builder = None
        self.matching_calculator = None
        self.is_initialized = False
        
        # 系统状态
        self.last_update_time = None
        self.available_majors = []
        
    def initialize_system(self, force_rebuild: bool = False):
        """
        初始化整个匹配系统
        
        Args:
            force_rebuild: 是否强制重建所有数据
        """
        print("=== 初始化学生专业匹配系统 ===")
        
        try:
            # 检查数据文件
            if not os.path.exists(self.config['data_path']):
                raise FileNotFoundError(f"数据文件不存在: {self.config['data_path']}")
            
            # 1. 聚类分析
            clustering_results_file = os.path.join(self.config['clustering_output_path'], 'clustering_results.json')
            
            if force_rebuild or not os.path.exists(clustering_results_file):
                print("执行专业路径聚类分析...")
                self._run_clustering_analysis()
            else:
                print("使用现有聚类结果...")
            
            # 2. 路径画像构建
            profiles_file = os.path.join(self.config['profiles_output_path'], 'path_profiles.json')
            
            if force_rebuild or not os.path.exists(profiles_file):
                print("构建路径画像...")
                self._build_path_profiles()
            else:
                print("使用现有路径画像...")
            
            # 3. 初始化匹配计算器
            print("初始化匹配计算器...")
            self.matching_calculator = MatchingCalculator(profiles_file)
            self.available_majors = self.matching_calculator.get_available_majors()
            
            self.is_initialized = True
            self.last_update_time = datetime.now()
            
            print("系统初始化完成！")
            print(f"可用专业数量: {len(self.available_majors)}")
            print(f"初始化时间: {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"系统初始化失败: {str(e)}")
            raise
    
    def _run_clustering_analysis(self):
        """执行聚类分析"""
        self.clustering_analyzer = ProfessionalPathClustering(
            data_path=self.config['data_path'],
            output_path=self.config['clustering_output_path'],
            min_applications=self.config['min_applications']
        )
        
        results = self.clustering_analyzer.run_clustering_analysis()
        print(f"聚类分析完成，处理专业数: {len(results)}")
    
    def _build_path_profiles(self):
        """构建路径画像"""
        clustering_results_path = os.path.join(self.config['clustering_output_path'], 'clustering_results.json')
        
        self.profile_builder = PathProfileBuilder(
            data_path=self.config['data_path'],
            clustering_results_path=clustering_results_path,
            output_path=self.config['profiles_output_path']
        )
        
        profiles = self.profile_builder.run_profile_building()
        print(f"路径画像构建完成，专业数: {len(profiles)}")
    
    def calculate_single_match(self, student_features: Dict[str, Any], target_major: str) -> Dict[str, Any]:
        """
        计算单个学生与单个专业的匹配度
        
        Args:
            student_features: 学生特征字典
            target_major: 目标专业名称
            
        Returns:
            匹配结果字典
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        try:
            result = self.matching_calculator.calculate_match_score(student_features, target_major)
            result['timestamp'] = datetime.now().isoformat()
            return result
        
        except Exception as e:
            return {
                'success': False,
                'error': f'匹配计算失败: {str(e)}',
                'target_major': target_major,
                'timestamp': datetime.now().isoformat()
            }
    
    def calculate_batch_matches(self, student_features: Dict[str, Any], target_majors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        计算单个学生与多个专业的匹配度
        
        Args:
            student_features: 学生特征字典
            target_majors: 目标专业列表，如果为None则匹配所有可用专业
            
        Returns:
            批量匹配结果字典
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        if target_majors is None:
            target_majors = self.available_majors[:20]  # 默认匹配前20个专业
        
        try:
            result = self.matching_calculator.batch_calculate_matches(student_features, target_majors)
            result['timestamp'] = datetime.now().isoformat()
            return result
        
        except Exception as e:
            return {
                'success': False,
                'error': f'批量匹配计算失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def find_best_matches(self, student_features: Dict[str, Any], top_n: int = 10) -> Dict[str, Any]:
        """
        为学生找到最佳匹配的专业
        
        Args:
            student_features: 学生特征字典
            top_n: 返回前N个最佳匹配
            
        Returns:
            最佳匹配结果
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        # 计算与所有专业的匹配度
        batch_result = self.calculate_batch_matches(student_features, self.available_majors)
        
        if not batch_result.get('success', False):
            return batch_result
        
        # 提取并排序结果
        matches = []
        for major, result in batch_result['results'].items():
            if result.get('success', False):
                matches.append({
                    'major': major,
                    'score': result['match_score'],
                    'level': result['match_level'],
                    'path': result['matched_path'],
                    'confidence': result['path_confidence'],
                    'recommendation': result['recommendation']
                })
        
        # 按分数排序
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'success': True,
            'student_profile': self._generate_student_summary(student_features),
            'total_majors_evaluated': len(matches),
            'best_matches': matches[:top_n],
            'match_distribution': self._analyze_match_distribution(matches),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_student_summary(self, student_features: Dict[str, Any]) -> Dict[str, Any]:
        """生成学生背景摘要"""
        summary = {'profile_type': '未知背景'}
        
        # 院校背景
        university_score = student_features.get('source_university_tier_score', 0)
        if university_score >= 85:
            summary['university_background'] = '985名校'
        elif university_score >= 75:
            summary['university_background'] = '211高校'
        elif university_score >= 65:
            summary['university_background'] = '双一流'
        else:
            summary['university_background'] = '普通本科'
        
        # GPA水平
        gpa = student_features.get('gpa_percentile', 0)
        if gpa >= 85:
            summary['academic_level'] = '优秀GPA'
        elif gpa >= 70:
            summary['academic_level'] = '良好GPA'
        else:
            summary['academic_level'] = '一般GPA'
        
        # 语言能力
        language_score = student_features.get('language_score_normalized', 0)
        if language_score >= 80:
            summary['language_ability'] = '语言优秀'
        elif language_score >= 65:
            summary['language_ability'] = '语言良好'
        else:
            summary['language_ability'] = '语言一般'
        
        # 工作经验
        work_years = student_features.get('work_experience_years', 0)
        if work_years >= 2:
            summary['experience_level'] = '有工作经验'
        elif work_years >= 1:
            summary['experience_level'] = '少量经验'
        else:
            summary['experience_level'] = '应届毕业生'
        
        return summary
    
    def _analyze_match_distribution(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析匹配度分布"""
        if not matches:
            return {'high_match': 0, 'medium_match': 0, 'low_match': 0, 'no_match': 0}
        
        scores = [m['score'] for m in matches]
        
        return {
            'high_match': sum(1 for s in scores if s >= 80),
            'medium_match': sum(1 for s in scores if 65 <= s < 80),
            'low_match': sum(1 for s in scores if 50 <= s < 65),
            'no_match': sum(1 for s in scores if s < 50),
            'avg_score': round(np.mean(scores), 1),
            'max_score': max(scores),
            'min_score': min(scores)
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态信息"""
        return {
            'initialized': self.is_initialized,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'available_majors_count': len(self.available_majors),
            'config': self.config,
            'components_status': {
                'clustering_analyzer': self.clustering_analyzer is not None,
                'profile_builder': self.profile_builder is not None,
                'matching_calculator': self.matching_calculator is not None
            }
        }
    
    def get_available_majors(self) -> List[str]:
        """获取所有可用专业列表"""
        return self.available_majors.copy() if self.available_majors else []
    
    def get_major_details(self, major_name: str) -> Dict[str, Any]:
        """获取专业详细信息"""
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化'}
        
        return self.matching_calculator.get_major_info(major_name)
    
    def export_results(self, results: Dict[str, Any], output_path: str, format_type: str = 'json'):
        """
        导出匹配结果
        
        Args:
            results: 匹配结果字典
            output_path: 输出文件路径
            format_type: 输出格式 ('json' 或 'csv')
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if format_type.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            elif format_type.lower() == 'csv':
                # 转换为CSV格式
                if 'best_matches' in results:
                    df = pd.DataFrame(results['best_matches'])
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                else:
                    # 处理其他格式的结果
                    df = pd.DataFrame([results])
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"结果已导出至: {output_path}")
            return {'success': True, 'output_path': output_path}
            
        except Exception as e:
            return {'success': False, 'error': f'导出失败: {str(e)}'}


def main():
    """主函数 - 完整系统演示"""
    print("=== 学生专业匹配系统演示 ===")
    
    # 1. 创建系统实例
    system = StudentMajorMatchingSystem()
    
    # 2. 初始化系统
    system.initialize_system()
    
    # 3. 示例学生特征
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
    
    # 4. 寻找最佳匹配
    print("\\n=== 寻找最佳专业匹配 ===")
    best_matches = system.find_best_matches(student_example, top_n=5)
    print(json.dumps(best_matches, ensure_ascii=False, indent=2))
    
    # 5. 获取系统状态
    print("\\n=== 系统状态 ===")
    status = system.get_system_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    
    return system


if __name__ == "__main__":
    main()