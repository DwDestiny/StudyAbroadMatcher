"""
测试匹配度的适配性逻辑
验证：匹配度反映学生与历史成功申请者的相似程度，而非学生的优秀程度
"""

from src.matching_engine.matching_system import StudentMajorMatchingSystem
import json

def analyze_major_characteristics():
    """分析各专业的历史申请者特征，了解其要求水平"""
    
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    print("=== 分析各专业历史申请者特征 ===")
    
    # 选择几个代表性专业进行分析
    target_majors = [
        "Master of Commerce",           # 商科硕士（可能要求相对较低）
        "Master of Computer Science",   # 计算机硕士（技术要求高）
        "Bachelor of Commerce",         # 商科本科（要求较低）
        "Master of Laws",              # 法律硕士（专业要求高）
        "Juris Doctor"                 # JD（顶级法律项目）
    ]
    
    major_analysis = {}
    
    for major in target_majors:
        info = system.get_major_details(major)
        if info['success']:
            major_analysis[major] = {
                'total_applications': info['total_applications'],
                'num_paths': info['num_paths'],
                'clustering_quality': info['clustering_quality']
            }
            
            print(f"\n{major}:")
            print(f"  历史申请量: {info['total_applications']}")
            print(f"  成功路径数: {info['num_paths']}")
            print(f"  聚类质量: {info['clustering_quality']:.3f}")
            
            # 分析各路径特征
            for path_key, path_info in info['paths'].items():
                print(f"  {path_info['label']}: {path_info['sample_size']}人 ({path_info['coverage']*100:.1f}%)")
    
    return major_analysis

def test_matching_appropriateness():
    """测试匹配度的适配性逻辑"""
    
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    print("\n=== 测试适配性匹配逻辑 ===")
    
    # 定义不同水平的学生档案
    students = {
        '顶级学生_985_95GPA': {
            'profile': {
                'source_university_tier_score': 95,    # 顶级985
                'gpa_percentile': 95,                  # 95%GPA
                'major_matching_score': 0.9,           
                'language_score_normalized': 90,       # 优秀语言
                'work_experience_years': 3,            # 丰富经验
                'work_relevance_score': 0.9,           
                'target_university_tier_score': 95,
                'university_matching_score': 0.9,
                'competition_index': 9.0,
                'academic_strength_score': 95,
                'applicant_comprehensive_strength': 92
            },
            'expected_logic': '应该匹配高要求专业，对低要求专业可能overqualified'
        },
        
        '优秀学生_985_85GPA': {
            'profile': {
                'source_university_tier_score': 88,    # 985
                'gpa_percentile': 85,                  # 85%GPA
                'major_matching_score': 0.8,           
                'language_score_normalized': 80,       
                'work_experience_years': 2,            
                'work_relevance_score': 0.7,           
                'target_university_tier_score': 90,
                'university_matching_score': 0.8,
                'competition_index': 7.5,
                'academic_strength_score': 85,
                'applicant_comprehensive_strength': 82
            },
            'expected_logic': '应该匹配中高要求专业'
        },
        
        '良好学生_211_75GPA': {
            'profile': {
                'source_university_tier_score': 75,    # 211
                'gpa_percentile': 75,                  # 75%GPA
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
            'expected_logic': '应该匹配中等要求专业'
        },
        
        '普通学生_60GPA': {
            'profile': {
                'source_university_tier_score': 60,    # 普通本科
                'gpa_percentile': 60,                  # 60%GPA
                'major_matching_score': 0.5,           
                'language_score_normalized': 60,       
                'work_experience_years': 0,            
                'work_relevance_score': 0.3,           
                'target_university_tier_score': 70,
                'university_matching_score': 0.6,
                'competition_index': 4.0,
                'academic_strength_score': 58,
                'applicant_comprehensive_strength': 55
            },
            'expected_logic': '应该匹配低要求专业，对高要求专业underqualified'
        }
    }
    
    # 不同层次的专业（根据申请量和名称推测难度）
    majors_by_level = {
        '入门级专业': [
            "Bachelor of Commerce",           # 本科商科
            "Bachelor of Business",           # 本科商务
        ],
        '中等专业': [
            "Master of Commerce",             # 商科硕士
            "Master of Management",           # 管理学硕士
            "Master of Marketing",            # 市场营销硕士
        ],
        '高要求专业': [
            "Master of Computer Science",     # 计算机硕士
            "Master of Data Science",         # 数据科学
            "Master of Engineering",          # 工程硕士
        ],
        '顶级专业': [
            "Juris Doctor",                   # JD项目
            "Master of Laws",                 # 法律硕士
        ]
    }
    
    # 执行测试
    results = {}
    
    for student_type, student_info in students.items():
        results[student_type] = {}
        
        print(f"\n--- {student_type} ---")
        print(f"预期逻辑: {student_info['expected_logic']}")
        
        # 测试该学生对不同层次专业的匹配度
        for level, majors in majors_by_level.items():
            level_scores = []
            
            for major in majors:
                result = system.calculate_single_match(student_info['profile'], major)
                if result['success']:
                    score = result['match_score']
                    level_scores.append(score)
                    print(f"  {major}: {score}分 ({result['match_level']})")
            
            if level_scores:
                avg_score = sum(level_scores) / len(level_scores)
                results[student_type][level] = {
                    'scores': level_scores,
                    'avg_score': avg_score,
                    'max_score': max(level_scores),
                    'min_score': min(level_scores)
                }
                print(f"  {level} 平均匹配度: {avg_score:.1f}分")
    
    return results

def analyze_matching_patterns(results):
    """分析匹配模式，验证适配性逻辑"""
    
    print("\n=== 匹配模式分析 ===")
    
    # 分析每个学生在不同专业层次的表现
    for student_type, student_results in results.items():
        print(f"\n{student_type} 的匹配模式:")
        
        # 按平均分排序专业层次
        sorted_levels = sorted(
            student_results.items(), 
            key=lambda x: x[1]['avg_score'], 
            reverse=True
        )
        
        for i, (level, scores) in enumerate(sorted_levels):
            print(f"  {i+1}. {level}: {scores['avg_score']:.1f}分")
        
        # 验证逻辑合理性
        best_level = sorted_levels[0][0]
        print(f"  最佳匹配层次: {best_level}")

def test_edge_cases():
    """测试边界情况"""
    
    system = StudentMajorMatchingSystem()
    system.initialize_system()
    
    print("\n=== 边界情况测试 ===")
    
    # 极端优秀学生
    super_student = {
        'source_university_tier_score': 100,   # 满分院校背景
        'gpa_percentile': 100,                 # 满分GPA
        'major_matching_score': 1.0,           # 完美专业匹配
        'language_score_normalized': 100,      # 满分语言
        'work_experience_years': 5,            # 丰富经验
        'work_relevance_score': 1.0,           # 完美相关性
        'target_university_tier_score': 100,
        'university_matching_score': 1.0,
        'competition_index': 10.0,
        'academic_strength_score': 100,
        'applicant_comprehensive_strength': 100
    }
    
    # 极端一般学生  
    weak_student = {
        'source_university_tier_score': 30,    # 很低院校背景
        'gpa_percentile': 30,                  # 很低GPA
        'major_matching_score': 0.1,           # 几乎不匹配
        'language_score_normalized': 30,       # 很低语言
        'work_experience_years': 0,            # 无经验
        'work_relevance_score': 0.1,           # 几乎无关
        'target_university_tier_score': 50,
        'university_matching_score': 0.3,
        'competition_index': 2.0,
        'academic_strength_score': 30,
        'applicant_comprehensive_strength': 25
    }
    
    test_cases = [
        ('极端优秀学生', super_student),
        ('极端一般学生', weak_student)
    ]
    
    test_majors = [
        "Bachelor of Commerce",      # 入门级
        "Master of Commerce",        # 中等级
        "Master of Computer Science", # 高级
        "Juris Doctor"              # 顶级
    ]
    
    for student_type, profile in test_cases:
        print(f"\n{student_type}:")
        
        for major in test_majors:
            result = system.calculate_single_match(profile, major)
            if result['success']:
                print(f"  {major}: {result['match_score']}分 ({result['match_level']})")
                print(f"    路径: {result['matched_path']}")
                print(f"    置信度: {result['path_confidence']:.3f}")

def main():
    """主测试函数"""
    
    print("=== 匹配度适配性逻辑验证 ===")
    print("核心假设: 匹配度反映适配性，而非优秀程度")
    print("- 学生过于优秀 → 低匹配度 (overqualified)")  
    print("- 学生不够优秀 → 低匹配度 (underqualified)")
    print("- 学生恰好匹配 → 高匹配度 (well-matched)")
    
    # 1. 分析专业特征
    major_analysis = analyze_major_characteristics()
    
    # 2. 测试适配性逻辑
    results = test_matching_appropriateness()
    
    # 3. 分析匹配模式
    analyze_matching_patterns(results)
    
    # 4. 测试边界情况
    test_edge_cases()
    
    print("\n=== 测试总结 ===")
    print("如果系统正确实现了适配性匹配逻辑，应该观察到:")
    print("1. 顶级学生在入门专业得分较低 (overqualified)")
    print("2. 普通学生在顶级专业得分较低 (underqualified)") 
    print("3. 各层次学生在对应层次专业得分最高 (well-matched)")

if __name__ == "__main__":
    main()