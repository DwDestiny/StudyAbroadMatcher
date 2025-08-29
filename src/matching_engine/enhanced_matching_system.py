"""
增强版统一匹配系统
集成优化后的聚类分析、路径画像构建、匹配度计算的完整服务
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
    from .enhanced_matching_calculator import EnhancedMatchingCalculator
except ImportError:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from clustering_analysis import ProfessionalPathClustering
    from path_profile_builder import PathProfileBuilder  
    from enhanced_matching_calculator import EnhancedMatchingCalculator


class EnhancedStudentMajorMatchingSystem:
    """增强版学生专业匹配系统"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化增强版匹配系统
        
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
            'log_level': 'INFO',
            'process_all_majors': True  # 处理所有符合条件的专业
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
        self.system_stats = {}
        
    def initialize_system(self, force_rebuild: bool = False):
        """
        初始化整个匹配系统
        
        Args:
            force_rebuild: 是否强制重建所有数据
        """
        print("=== 初始化增强版学生专业匹配系统 ===")
        
        try:
            # 检查数据文件
            if not os.path.exists(self.config['data_path']):
                raise FileNotFoundError(f"数据文件不存在: {self.config['data_path']}")
            
            # 1. 聚类分析（扩展版）
            clustering_results_file = os.path.join(self.config['clustering_output_path'], 'clustering_results.json')
            
            if force_rebuild or not os.path.exists(clustering_results_file):
                print("执行全量专业路径聚类分析...")
                self._run_enhanced_clustering_analysis()
            else:
                print("使用现有聚类结果...")
            
            # 2. 路径画像构建
            profiles_file = os.path.join(self.config['profiles_output_path'], 'path_profiles.json')
            
            if force_rebuild or not os.path.exists(profiles_file):
                print("构建增强版路径画像...")
                self._build_enhanced_path_profiles()
            else:
                print("使用现有路径画像...")
            
            # 3. 初始化增强版匹配计算器
            print("初始化增强版匹配计算器...")
            self.matching_calculator = EnhancedMatchingCalculator(
                profiles_file, 
                self.config['data_path']
            )
            self.available_majors = list(self.matching_calculator.path_profiles.keys())
            
            # 4. 生成系统统计信息
            self._generate_system_stats()
            
            self.is_initialized = True
            self.last_update_time = datetime.now()
            
            print("增强版系统初始化完成！")
            print(f"可用专业数量: {len(self.available_majors)}")
            print(f"平均路径置信度: {self.system_stats.get('avg_confidence', 'N/A')}")
            print(f"初始化时间: {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"增强版系统初始化失败: {str(e)}")
            raise
    
    def _run_enhanced_clustering_analysis(self):
        """执行增强版聚类分析"""
        self.clustering_analyzer = ProfessionalPathClustering(
            data_path=self.config['data_path'],
            output_path=self.config['clustering_output_path'],
            min_applications=self.config['min_applications']
        )
        
        results = self.clustering_analyzer.run_clustering_analysis()
        print(f"增强版聚类分析完成，处理专业数: {len(results)}")
    
    def _build_enhanced_path_profiles(self):
        """构建增强版路径画像"""
        clustering_results_path = os.path.join(self.config['clustering_output_path'], 'clustering_results.json')
        
        self.profile_builder = PathProfileBuilder(
            data_path=self.config['data_path'],
            clustering_results_path=clustering_results_path,
            output_path=self.config['profiles_output_path']
        )
        
        profiles = self.profile_builder.run_profile_building()
        print(f"增强版路径画像构建完成，专业数: {len(profiles)}")
    
    def _generate_system_stats(self):
        """生成系统统计信息"""
        if not self.matching_calculator or not self.matching_calculator.path_profiles:
            return
        
        total_paths = 0
        total_applications = 0
        confidences = []
        
        for major_name, major_data in self.matching_calculator.path_profiles.items():
            if 'paths' in major_data:
                paths = major_data['paths']
                total_paths += len(paths)
                
                if 'summary' in major_data:
                    total_applications += major_data['summary'].get('total_applications', 0)
                
                for path_info in paths.values():
                    rep = path_info.get('representativeness', 0)
                    if rep > 0:
                        confidences.append(rep)
        
        self.system_stats = {
            'total_majors': len(self.matching_calculator.path_profiles),
            'total_paths': total_paths,
            'total_applications': total_applications,
            'avg_confidence': round(np.mean(confidences) if confidences else 0, 3),
            'avg_paths_per_major': round(total_paths / len(self.matching_calculator.path_profiles), 1)
        }
    
    def calculate_enhanced_single_match(self, student_features: Dict[str, Any], target_major: str) -> Dict[str, Any]:
        """
        使用增强版算法计算单个学生与单个专业的匹配度
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        try:
            result = self.matching_calculator.calculate_match_score_enhanced(student_features, target_major)
            result['timestamp'] = datetime.now().isoformat()
            result['system_version'] = 'enhanced'
            return result
        
        except Exception as e:
            return {
                'success': False,
                'error': f'增强版匹配计算失败: {str(e)}',
                'target_major': target_major,
                'timestamp': datetime.now().isoformat()
            }
    
    def calculate_enhanced_batch_matches(self, student_features: Dict[str, Any], target_majors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        使用增强版算法计算批量匹配
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        if target_majors is None:
            target_majors = self.available_majors[:30]  # 默认匹配前30个专业
        
        try:
            results = {}
            successful_matches = 0
            
            for major in target_majors:
                result = self.calculate_enhanced_single_match(student_features, major)
                results[major] = result
                if result.get('success', False):
                    successful_matches += 1
            
            # 提取成功的匹配并排序
            successful_results = {k: v for k, v in results.items() if v.get('success', False)}
            if successful_results:
                sorted_matches = sorted(
                    successful_results.items(), 
                    key=lambda x: x[1]['match_score'], 
                    reverse=True
                )
                
                return {
                    'success': True,
                    'total_majors': len(target_majors),
                    'successful_matches': successful_matches,
                    'results': dict(sorted_matches),
                    'top_recommendations': [
                        {
                            'major': k,
                            'score': v['match_score'],
                            'level': v['match_level'],
                            'path': v['matched_path'],
                            'confidence': v['path_confidence']
                        }
                        for k, v in sorted_matches[:10]  # 前10个推荐
                    ],
                    'timestamp': datetime.now().isoformat(),
                    'system_version': 'enhanced'
                }
            else:
                return {
                    'success': False,
                    'error': '所有专业匹配均失败',
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'增强版批量匹配计算失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def find_enhanced_best_matches(self, student_features: Dict[str, Any], top_n: int = 15) -> Dict[str, Any]:
        """
        使用增强版算法为学生找到最佳匹配的专业
        """
        if not self.is_initialized:
            return {'success': False, 'error': '系统未初始化，请先调用 initialize_system()'}
        
        # 计算与所有专业的匹配度
        batch_result = self.calculate_enhanced_batch_matches(student_features, self.available_majors)
        
        if not batch_result.get('success', False):
            return batch_result
        
        # 提取并分析结果
        matches = []
        score_sum = 0
        high_matches = 0
        
        for major, result in batch_result['results'].items():
            if result.get('success', False):
                score = result['match_score']
                matches.append({
                    'major': major,
                    'score': score,
                    'level': result['match_level'],
                    'path': result['matched_path'],
                    'confidence': result['path_confidence'],
                    'recommendation': result['recommendation'],
                    'score_breakdown': result.get('score_breakdown', {})
                })
                score_sum += score
                if score >= 80:
                    high_matches += 1
        
        # 按分数排序
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'success': True,
            'student_profile': self._generate_enhanced_student_summary(student_features),
            'total_majors_evaluated': len(matches),
            'best_matches': matches[:top_n],
            'match_statistics': {
                'avg_score': round(score_sum / len(matches) if matches else 0, 1),
                'high_matches_count': high_matches,
                'high_matches_rate': round(high_matches / len(matches) * 100, 1) if matches else 0,
                'score_distribution': self._analyze_score_distribution([m['score'] for m in matches])
            },
            'system_version': 'enhanced',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_enhanced_student_summary(self, student_features: Dict[str, Any]) -> Dict[str, Any]:
        """生成增强版学生背景摘要"""
        summary = {'profile_type': '综合背景学生'}
        
        # 院校背景（更细化分级）
        university_score = student_features.get('source_university_tier_score', 0)
        if university_score >= 95:
            summary['university_background'] = '顶级985'
        elif university_score >= 88:
            summary['university_background'] = '985名校'
        elif university_score >= 78:
            summary['university_background'] = '211高校'
        elif university_score >= 65:
            summary['university_background'] = '双一流'
        else:
            summary['university_background'] = '普通本科'
        
        # GPA水平
        gpa = student_features.get('gpa_percentile', 0)
        if gpa >= 90:
            summary['academic_level'] = '优异GPA'
        elif gpa >= 80:
            summary['academic_level'] = '优秀GPA'
        elif gpa >= 70:
            summary['academic_level'] = '良好GPA'
        else:
            summary['academic_level'] = '一般GPA'
        
        # 专业匹配度
        major_match = student_features.get('major_matching_score', 0)
        if major_match >= 0.8:
            summary['major_relevance'] = '高度相关'
        elif major_match >= 0.6:
            summary['major_relevance'] = '中等相关'
        elif major_match >= 0.3:
            summary['major_relevance'] = '低度相关'
        else:
            summary['major_relevance'] = '跨专业'
        
        # 语言能力
        language_score = student_features.get('language_score_normalized', 0)
        if language_score >= 85:
            summary['language_ability'] = '语言卓越'
        elif language_score >= 75:
            summary['language_ability'] = '语言优秀'
        elif language_score >= 65:
            summary['language_ability'] = '语言良好'
        else:
            summary['language_ability'] = '语言一般'
        
        # 工作经验
        work_years = student_features.get('work_experience_years', 0)
        work_relevance = student_features.get('work_relevance_score', 0)
        
        if work_years >= 3:
            summary['experience_level'] = '丰富工作经验'
        elif work_years >= 1:
            if work_relevance >= 0.7:
                summary['experience_level'] = '相关工作经验'
            else:
                summary['experience_level'] = '一般工作经验'
        else:
            summary['experience_level'] = '应届毕业生'
        
        return summary
    
    def _analyze_score_distribution(self, scores: List[int]) -> Dict[str, int]:
        """分析分数分布"""
        if not scores:
            return {'high': 0, 'medium': 0, 'low': 0, 'very_low': 0}
        
        return {
            'high (85+)': sum(1 for s in scores if s >= 85),
            'medium (70-84)': sum(1 for s in scores if 70 <= s < 85),
            'low (55-69)': sum(1 for s in scores if 55 <= s < 70),
            'very_low (<55)': sum(1 for s in scores if s < 55)
        }
    
    def get_enhanced_system_status(self) -> Dict[str, Any]:
        """获取增强版系统状态信息"""
        return {
            'initialized': self.is_initialized,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'system_version': 'enhanced_v2.0',
            'config': self.config,
            'system_stats': self.system_stats,
            'available_majors_count': len(self.available_majors),
            'components_status': {
                'enhanced_clustering_analyzer': self.clustering_analyzer is not None,
                'enhanced_profile_builder': self.profile_builder is not None,
                'enhanced_matching_calculator': self.matching_calculator is not None
            }
        }
    
    def get_available_majors(self) -> List[str]:
        """获取所有可用专业列表"""
        return self.available_majors.copy() if self.available_majors else []
    
    def export_enhanced_results(self, results: Dict[str, Any], output_path: str, format_type: str = 'json'):
        """导出增强版匹配结果"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if format_type.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            elif format_type.lower() == 'csv':
                if 'best_matches' in results:
                    df = pd.DataFrame(results['best_matches'])
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                else:
                    df = pd.DataFrame([results])
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"增强版结果已导出至: {output_path}")
            return {'success': True, 'output_path': output_path}
            
        except Exception as e:
            return {'success': False, 'error': f'导出失败: {str(e)}'}


def main():
    """主函数 - 增强版系统演示"""
    print("=== 增强版学生专业匹配系统演示 ===")
    
    # 1. 创建增强版系统实例
    system = EnhancedStudentMajorMatchingSystem()
    
    # 2. 初始化系统（如果需要重建数据，设置force_rebuild=True）
    system.initialize_system(force_rebuild=False)
    
    # 3. 测试学生特征
    test_students = {
        '211中等学生': {
            'source_university_tier_score': 75,
            'gpa_percentile': 75,
            'major_matching_score': 0.7,
            'language_score_normalized': 70,
            'work_experience_years': 1,
            'work_relevance_score': 0.5,
            'target_university_tier_score': 80,
            'university_matching_score': 0.7,
            'competition_index': 6.0,
            'academic_strength_score': 75,
            'applicant_comprehensive_strength': 72
        },
        '985优秀学生': {
            'source_university_tier_score': 90,
            'gpa_percentile': 88,
            'major_matching_score': 0.9,
            'language_score_normalized': 85,
            'work_experience_years': 2,
            'work_relevance_score': 0.8,
            'target_university_tier_score': 95,
            'university_matching_score': 0.9,
            'competition_index': 8.5,
            'academic_strength_score': 90,
            'applicant_comprehensive_strength': 88
        }
    }
    
    # 4. 测试增强版匹配功能
    for student_type, features in test_students.items():
        print(f"\n=== {student_type} 匹配测试 ===")
        
        # 寻找最佳匹配
        best_matches = system.find_enhanced_best_matches(features, top_n=5)
        
        if best_matches['success']:
            print(f"学生画像: {best_matches['student_profile']}")
            print(f"匹配统计: 平均分{best_matches['match_statistics']['avg_score']}，高匹配{best_matches['match_statistics']['high_matches_count']}个")
            print("前5个推荐专业:")
            for i, match in enumerate(best_matches['best_matches']):
                print(f"  {i+1}. {match['major']}: {match['score']}分 ({match['level']})")
                print(f"     路径: {match['path']}, 置信度: {match['confidence']:.3f}")
        else:
            print(f"匹配失败: {best_matches.get('error', '未知错误')}")
    
    # 5. 显示系统状态
    print(f"\n=== 增强版系统状态 ===")
    status = system.get_enhanced_system_status()
    print(f"系统版本: {status['system_version']}")
    print(f"可用专业: {status['available_majors_count']}个")
    print(f"平均路径置信度: {status['system_stats']['avg_confidence']}")
    
    return system


if __name__ == "__main__":
    main()