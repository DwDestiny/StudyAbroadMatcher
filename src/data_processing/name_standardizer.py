import pandas as pd
import numpy as np
import re
from fuzzywuzzy import fuzz, process
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, DATA_EXTERNAL_DIR

class NameStandardizer:
    """院校和专业名称标准化器"""
    
    def __init__(self):
        self.df = None
        self.qs_ranking = None
        self.china_universities = None
        self.university_mapping = {}
        self.major_mapping = {}
        
    def load_data(self):
        """加载数据"""
        # 加载主数据
        data_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_gpa_fixed.csv'
        try:
            self.df = pd.read_csv(data_path, encoding='utf-8-sig')
            print(f"主数据加载成功: {self.df.shape}")
        except Exception as e:
            print(f"主数据加载失败: {e}")
            return False
        
        # 加载QS排名数据
        try:
            self.qs_ranking = pd.read_csv(DATA_EXTERNAL_DIR / 'qs_university_rankings.csv', encoding='utf-8-sig')
            print(f"QS排名数据加载成功: {len(self.qs_ranking)}所院校")
        except Exception as e:
            print(f"QS排名数据加载失败: {e}")
            return False
        
        # 加载中国院校数据
        try:
            from config.config import DATA_RAW_DIR
            self.china_universities = pd.read_excel(DATA_RAW_DIR / '中国院校 校对.xlsx')
            print(f"中国院校数据加载成功: {len(self.china_universities)}所院校")
        except Exception as e:
            print(f"中国院校数据加载失败: {e}")
            return False
            
        return True
    
    def standardize_target_universities(self):
        """标准化申请院校名称"""
        print("\n" + "="*60)
        print("标准化申请院校名称")
        print("="*60)
        
        target_universities = self.df['申请院校_院校名称'].value_counts()
        print(f"原始目标院校数量: {len(target_universities)}")
        
        # 创建QS院校名称列表用于匹配
        qs_universities = self.qs_ranking['university'].tolist()
        
        standardized_names = {}
        matched_count = 0
        unmatched_count = 0
        
        for university, count in target_universities.items():
            # 尝试精确匹配
            if university in qs_universities:
                standardized_names[university] = university
                matched_count += 1
                continue
            
            # 尝试模糊匹配
            best_match = process.extractOne(
                university, 
                qs_universities, 
                scorer=fuzz.ratio,
                score_cutoff=80
            )
            
            if best_match:
                standardized_names[university] = best_match[0]
                matched_count += 1
                print(f"模糊匹配: '{university}' -> '{best_match[0]}' (相似度: {best_match[1]})")
            else:
                # 手动处理一些常见的变体
                manual_mapping = self._get_manual_university_mapping()
                if university in manual_mapping:
                    standardized_names[university] = manual_mapping[university]
                    matched_count += 1
                    print(f"手动匹配: '{university}' -> '{manual_mapping[university]}'")
                else:
                    standardized_names[university] = university  # 保持原名
                    unmatched_count += 1
        
        self.university_mapping = standardized_names
        
        print(f"\n院校名称标准化结果:")
        print(f"  精确+模糊匹配: {matched_count}")
        print(f"  未匹配院校: {unmatched_count}")
        
        # 应用标准化
        self.df['申请院校_院校名称_标准化'] = self.df['申请院校_院校名称'].map(standardized_names)
        
        return standardized_names
    
    def standardize_source_universities(self):
        """标准化毕业院校名称（中国院校）"""
        print("\n" + "="*60)
        print("标准化毕业院校名称")
        print("="*60)
        
        source_universities = self.df['教育经历_毕业院校'].value_counts()
        print(f"原始毕业院校数量: {len(source_universities)}")
        
        # 创建中国院校名称列表
        china_university_names = self.china_universities['院校名称'].tolist()
        
        standardized_source = {}
        matched_count = 0
        unmatched_count = 0
        
        for university, count in source_universities.items():
            # 尝试精确匹配
            if university in china_university_names:
                standardized_source[university] = university
                matched_count += 1
                continue
            
            # 尝试模糊匹配
            best_match = process.extractOne(
                university,
                china_university_names,
                scorer=fuzz.ratio,
                score_cutoff=70  # 中文匹配阈值稍低
            )
            
            if best_match:
                standardized_source[university] = best_match[0]
                matched_count += 1
                if best_match[1] < 95:  # 只显示不是非常相似的匹配
                    try:
                        print(f"模糊匹配: '{university}' -> '{best_match[0]}' (相似度: {best_match[1]})")
                    except UnicodeEncodeError:
                        print(f"模糊匹配: 院校名称包含特殊字符 (相似度: {best_match[1]})")
            else:
                standardized_source[university] = university  # 保持原名
                unmatched_count += 1
        
        print(f"\n毕业院校名称标准化结果:")
        print(f"  匹配成功: {matched_count}")
        print(f"  未匹配院校: {unmatched_count}")
        
        # 应用标准化
        self.df['教育经历_毕业院校_标准化'] = self.df['教育经历_毕业院校'].map(standardized_source)
        
        return standardized_source
    
    def standardize_majors(self):
        """标准化专业名称"""
        print("\n" + "="*60)
        print("标准化专业名称")
        print("="*60)
        
        # 分析申请专业
        target_majors = self.df['申请院校_专业名称'].value_counts()
        source_majors = self.df['教育经历_所学专业'].value_counts()
        
        print(f"申请专业数量: {len(target_majors)}")
        print(f"本科专业数量: {len(source_majors)}")
        
        # 创建专业标准化映射
        target_major_mapping = self._standardize_major_names(target_majors, "申请专业")
        source_major_mapping = self._standardize_major_names(source_majors, "本科专业")
        
        # 应用标准化
        self.df['申请院校_专业名称_标准化'] = self.df['申请院校_专业名称'].map(target_major_mapping)
        self.df['教育经历_所学专业_标准化'] = self.df['教育经历_所学专业'].map(source_major_mapping)
        
        return target_major_mapping, source_major_mapping
    
    def _standardize_major_names(self, major_counts, major_type):
        """标准化专业名称的具体实现"""
        standardized_majors = {}
        
        # 专业名称标准化规则
        standardization_rules = {
            # 商科类
            'commerce': 'Commerce',
            'master of commerce': 'Master of Commerce', 
            'Master of commerce': 'Master of Commerce',
            'business': 'Business',
            'Business': 'Business',
            'finance': 'Finance',
            'Finance': 'Finance',
            'accounting': 'Accounting',
            'Accounting': 'Accounting',
            'economics': 'Economics',
            'Economics': 'Economics',
            'management': 'Management',
            'Management': 'Management',
            'marketing': 'Marketing',
            'Marketing': 'Marketing',
            
            # 计算机类
            'computer science': 'Computer Science',
            'Computer Science': 'Computer Science',
            'Computer Science and Technology': 'Computer Science',
            'information technology': 'Information Technology',
            'Information Technology': 'Information Technology',
            'Information technology': 'Information Technology',
            'software engineering': 'Software Engineering',
            'Software Engineering': 'Software Engineering',
            'data science': 'Data Science',
            'Data Science': 'Data Science',
            
            # 工程类
            'engineering': 'Engineering',
            'Engineering': 'Engineering',
            'electrical engineering': 'Electrical Engineering',
            'Electrical Engineering': 'Electrical Engineering',
            'Electrical Engineering and Automation': 'Electrical Engineering',
            
            # 法学类
            'law': 'Law',
            'Law': 'Law',
            'legal studies': 'Law',
            'Legal Studies': 'Law',
            
            # 教育类
            'education': 'Education',
            'Education': 'Education',
            'teaching': 'Education',
            'Teaching': 'Education',
            
            # 语言文学类
            'english': 'English',
            'English': 'English',
            'journalism': 'Journalism',
            'Journalism': 'Journalism',
            
            # 艺术设计类
            'design': 'Design',
            'Design': 'Design',
            'visual communication design': 'Visual Communication Design',
            'Visual Communication Design': 'Visual Communication Design',
            
            # 医学类
            'medicine': 'Medicine',
            'Medicine': 'Medicine',
            'nursing': 'Nursing',
            'Nursing': 'Nursing',
        }
        
        for major, count in major_counts.items():
            # 首先尝试直接映射
            if major in standardization_rules:
                standardized_majors[major] = standardization_rules[major]
            else:
                # 尝试部分匹配和清理
                cleaned_major = self._clean_major_name(major)
                if cleaned_major in standardization_rules:
                    standardized_majors[major] = standardization_rules[cleaned_major]
                else:
                    standardized_majors[major] = cleaned_major  # 使用清理后的名称
        
        print(f"\n{major_type}标准化完成，处理了{len(standardized_majors)}个专业")
        
        return standardized_majors
    
    def _clean_major_name(self, major):
        """清理专业名称"""
        if pd.isna(major):
            return major
            
        # 基本清理
        cleaned = str(major).strip()
        
        # 移除多余的空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 标准化大小写（保持专业词汇的正确大小写）
        # 这里可以根据需要添加更多清理规则
        
        return cleaned
    
    def _get_manual_university_mapping(self):
        """手动创建一些常见的院校名称映射"""
        return {
            'University of Sydney': 'The University of Sydney',
            'Sydney University': 'The University of Sydney',
            'University of Melbourne': 'The University of Melbourne',
            'Melbourne University': 'The University of Melbourne',
            'Australian National University (ANU)': 'The Australian National University',
            'The Australian National University (ANU)': 'The Australian National University',
            'University of Queensland': 'The University of Queensland',
            'Queensland University': 'The University of Queensland',
            'University of Western Australia': 'The University of Western Australia',
            'Western Australia University': 'The University of Western Australia',
            'University of Adelaide': 'The University of Adelaide',
            'Adelaide University': 'The University of Adelaide',
            'University of New South Wales': 'UNSW Sydney',
            'UNSW': 'UNSW Sydney',
            'University of Technology, Sydney': 'University of Technology Sydney',
            'UTS': 'University of Technology Sydney',
        }
    
    def generate_standardization_report(self):
        """生成标准化报告"""
        print("\n" + "="*60)
        print("名称标准化总结报告")
        print("="*60)
        
        # 统计标准化后的唯一值数量
        original_target_unis = self.df['申请院校_院校名称'].nunique()
        standardized_target_unis = self.df['申请院校_院校名称_标准化'].nunique()
        
        original_source_unis = self.df['教育经历_毕业院校'].nunique()
        standardized_source_unis = self.df['教育经历_毕业院校_标准化'].nunique()
        
        original_target_majors = self.df['申请院校_专业名称'].nunique()
        standardized_target_majors = self.df['申请院校_专业名称_标准化'].nunique()
        
        original_source_majors = self.df['教育经历_所学专业'].nunique()
        standardized_source_majors = self.df['教育经历_所学专业_标准化'].nunique()
        
        print("标准化效果:")
        print(f"  申请院校: {original_target_unis} -> {standardized_target_unis} ({original_target_unis - standardized_target_unis} 合并)")
        print(f"  毕业院校: {original_source_unis} -> {standardized_source_unis} ({original_source_unis - standardized_source_unis} 合并)")
        print(f"  申请专业: {original_target_majors} -> {standardized_target_majors} ({original_target_majors - standardized_target_majors} 合并)")
        print(f"  本科专业: {original_source_majors} -> {standardized_source_majors} ({original_source_majors - standardized_source_majors} 合并)")
    
    def save_standardized_data(self):
        """保存标准化后的数据"""
        output_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_standardized.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n标准化数据已保存: {output_path}")
        return output_path
    
    def run_standardization(self):
        """执行完整的名称标准化流程"""
        if not self.load_data():
            return None
        
        # 标准化申请院校名称
        self.standardize_target_universities()
        
        # 标准化毕业院校名称  
        self.standardize_source_universities()
        
        # 标准化专业名称
        self.standardize_majors()
        
        # 生成报告
        self.generate_standardization_report()
        
        # 保存数据
        output_path = self.save_standardized_data()
        
        return output_path

if __name__ == "__main__":
    standardizer = NameStandardizer()
    result = standardizer.run_standardization()