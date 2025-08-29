"""
简化的系统测试脚本
"""

from src.matching_engine.matching_system import StudentMajorMatchingSystem
import json

def test_system():
    print("=== 系统功能测试 ===")
    
    # 1. 初始化系统
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    status = system.get_system_status()
    print(f"系统初始化: {'成功' if status['initialized'] else '失败'}")
    print(f"可用专业数量: {status['available_majors_count']}")
    
    # 2. 准备测试数据
    test_students = {
        '优秀学生': {
            'source_university_tier_score': 95,
            'gpa_percentile': 90,
            'major_matching_score': 0.9,
            'language_score_normalized': 85,
            'work_experience_years': 2,
            'work_relevance_score': 0.8,
            'target_university_tier_score': 95,
            'university_matching_score': 0.9,
            'competition_index': 8.0,
            'academic_strength_score': 90,
            'applicant_comprehensive_strength': 88
        },
        '普通学生': {
            'source_university_tier_score': 60,
            'gpa_percentile': 60,
            'major_matching_score': 0.4,
            'language_score_normalized': 60,
            'work_experience_years': 0,
            'work_relevance_score': 0.2,
            'target_university_tier_score': 75,
            'university_matching_score': 0.6,
            'competition_index': 4.0,
            'academic_strength_score': 58,
            'applicant_comprehensive_strength': 55
        }
    }
    
    # 3. 测试单个专业匹配
    print("\n=== 单个专业匹配测试 ===")
    test_major = "Master of Commerce"
    
    for student_type, features in test_students.items():
        result = system.calculate_single_match(features, test_major)
        if result['success']:
            print(f"{student_type} -> {test_major}: {result['match_score']}分 ({result['match_level']})")
        else:
            print(f"{student_type} 匹配失败: {result.get('error', '未知错误')}")
    
    # 4. 测试批量匹配
    print("\n=== 批量专业匹配测试 ===")
    test_majors = ["Master of Commerce", "Master of Computer Science", "Master of Economics"]
    
    for student_type, features in test_students.items():
        result = system.calculate_batch_matches(features, test_majors)
        if result['success']:
            print(f"{student_type} 批量匹配成功，匹配 {result['successful_matches']} 个专业")
            # 显示前3个最佳匹配
            for i, (major, match_result) in enumerate(list(result['results'].items())[:3]):
                if match_result['success']:
                    print(f"  {i+1}. {major}: {match_result['match_score']}分")
        else:
            print(f"{student_type} 批量匹配失败")
    
    # 5. 测试最佳匹配推荐
    print("\n=== 最佳匹配推荐测试 ===")
    
    for student_type, features in test_students.items():
        result = system.find_best_matches(features, top_n=3)
        if result['success']:
            print(f"\n{student_type} 的前3个推荐专业:")
            for i, match in enumerate(result['best_matches']):
                print(f"  {i+1}. {match['major']}: {match['score']}分 ({match['level']})")
        else:
            print(f"{student_type} 推荐失败: {result.get('error', '未知错误')}")
    
    # 6. 测试专业信息获取
    print("\n=== 专业信息获取测试 ===")
    available_majors = system.get_available_majors()
    print(f"可获取信息的专业数量: {len(available_majors)}")
    
    if available_majors:
        sample_major = available_majors[0]
        info = system.get_major_details(sample_major)
        if info['success']:
            print(f"示例专业: {sample_major}")
            print(f"  总申请量: {info['total_applications']}")
            print(f"  路径数量: {info['num_paths']}")
            print(f"  聚类质量: {info['clustering_quality']}")
    
    print("\n=== 测试完成 ===")
    return True

def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    import time
    
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    # 测试单次匹配性能
    test_features = {
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
    
    # 单次匹配性能
    start_time = time.time()
    result = system.calculate_single_match(test_features, "Master of Commerce")
    single_match_time = time.time() - start_time
    
    print(f"单次匹配耗时: {single_match_time*1000:.1f}毫秒")
    
    # 批量匹配性能
    test_majors = system.get_available_majors()[:10]  # 测试前10个专业
    
    start_time = time.time()
    batch_result = system.calculate_batch_matches(test_features, test_majors)
    batch_match_time = time.time() - start_time
    
    print(f"批量匹配({len(test_majors)}个专业)耗时: {batch_match_time*1000:.1f}毫秒")
    print(f"平均每个专业: {batch_match_time/len(test_majors)*1000:.1f}毫秒")
    
    return True

def main():
    """主测试函数"""
    try:
        # 功能测试
        test_system()
        
        # 性能测试
        performance_test()
        
        print("\n=== 所有测试通过！ ===")
        return True
        
    except Exception as e:
        print(f"\n=== 测试失败: {str(e)} ===")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n测试结果: {'成功' if success else '失败'}")