"""
测试统一匹配系统
"""

from src.matching_engine.matching_system import StudentMajorMatchingSystem

def test_system():
    print("=== 测试统一匹配系统 ===")
    
    # 创建系统实例
    system = StudentMajorMatchingSystem()
    
    # 初始化系统（使用现有数据）
    system.initialize_system()
    
    print(f"系统初始化成功！")
    print(f"可用专业数量: {len(system.get_available_majors())}")
    
    # 测试学生特征
    student_example = {
        'source_university_tier_score': 85,
        'gpa_percentile': 78,
        'major_matching_score': 0.8,
        'language_score_normalized': 75,
        'work_experience_years': 1,
        'work_relevance_score': 0.6,
        'target_university_tier_score': 90,
        'university_matching_score': 0.85,
        'competition_index': 6.5,
        'academic_strength_score': 80,
        'applicant_comprehensive_strength': 75
    }
    
    # 测试单个专业匹配
    result = system.calculate_single_match(student_example, "Master of Commerce")
    if result['success']:
        print(f"单个匹配测试成功！匹配度: {result['match_score']}分")
    else:
        print(f"单个匹配测试失败: {result.get('error', '未知错误')}")
    
    # 测试寻找最佳匹配
    best_matches = system.find_best_matches(student_example, top_n=3)
    if best_matches['success']:
        print("最佳匹配测试成功！")
        print("Top 3 推荐专业:")
        for i, match in enumerate(best_matches['best_matches'][:3]):
            print(f"{i+1}. {match['major']}: {match['score']}分 ({match['level']})")
    else:
        print(f"最佳匹配测试失败: {best_matches.get('error', '未知错误')}")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_system()