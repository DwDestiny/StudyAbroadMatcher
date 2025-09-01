#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生专业匹配系统 - 主入口程序

使用方法：
python main.py
"""

from src.matching_engine.enhanced_matching_system import EnhancedStudentMajorMatchingSystem
import json

def main():
    """主函数"""
    print("=" * 60)
    print("  学生专业匹配系统 - 生产级增强版 v2.0")
    print("=" * 60)
    print("初始化系统中...")
    
    # 创建增强系统实例
    system = EnhancedStudentMajorMatchingSystem()
    
    # 初始化系统
    system.initialize_system()
    
    # 获取系统状态
    status = system.get_enhanced_system_status()
    available_majors = system.get_available_majors()
    print(f"系统初始化完成")
    print(f"支持专业数: {len(available_majors)}")
    print(f"平均路径置信度: {status.get('avg_path_confidence', 'N/A')}")
    print()
    
    # 示例学生特征
    demo_student = {
        'source_university_tier_score': 75,      # 211大学
        'gpa_percentile': 75,                    # 75%百分位
        'major_matching_score': 0.7,             # 70%专业匹配度
        'language_score_normalized': 70,         # 标准化语言成绩
        'work_experience_years': 1,              # 1年工作经验
        'work_relevance_score': 0.5,             # 50%工作相关性
        'target_university_tier_score': 80,
        'university_matching_score': 0.7,
        'competition_index': 6.0,
        'academic_strength_score': 75,
        'applicant_comprehensive_strength': 72
    }
    
    print("=" * 60)
    print("  系统功能演示")
    print("=" * 60)
    
    # 演示单个专业匹配
    print("1. 单个专业匹配演示")
    print("-" * 30)
    test_major = "Master of Commerce"
    result = system.calculate_enhanced_single_match(demo_student, test_major)
    
    if result['success']:
        print(f"专业: {test_major}")
        print(f"匹配度: {result['match_score']}分")
        print(f"匹配等级: {result['match_level']}")
        print(f"路径置信度: {result['path_confidence']:.1%}")
        print(f"匹配路径: {result['matched_path']}")
        print()
    
    # 演示最佳匹配推荐
    print("2. 最佳匹配推荐演示")
    print("-" * 30)
    best_matches = system.find_enhanced_best_matches(demo_student, top_n=5)
    
    if best_matches['success']:
        print("为示例学生推荐的前5个专业:")
        for i, match in enumerate(best_matches['best_matches'][:5], 1):
            print(f"{i}. {match['major']}: {match['score']}分 ({match['level']})")
        print()
    
    print("=" * 60)
    print("  系统使用说明")  
    print("=" * 60)
    print("1. 导入系统:")
    print("   from src.matching_engine.enhanced_matching_system import EnhancedStudentMajorMatchingSystem")
    print()
    print("2. 创建实例:")
    print("   system = EnhancedStudentMajorMatchingSystem()")
    print("   system.initialize_system()")
    print()
    print("3. 使用匹配功能:")
    print("   result = system.calculate_enhanced_single_match(student_features, major_name)")
    print("   best_matches = system.find_enhanced_best_matches(student_features, top_n=10)")
    print()
    print("详细使用说明请参考 USAGE_GUIDE.md")
    print("部署指南请参考 DEPLOYMENT_GUIDE.md")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n系统运行出错: {str(e)}")
        print("请检查环境配置和数据文件是否完整")