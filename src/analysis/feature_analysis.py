import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from collections import Counter
import jieba

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class FeatureAnalyzer:
    """特征分析器"""
    
    def __init__(self):
        self.df = None
        
    def load_cleaned_data(self):
        """加载清洗后的数据"""
        data_path = DATA_PROCESSED_DIR / 'cleaned_offer_data.csv'
        try:
            self.df = pd.read_csv(data_path, encoding='utf-8-sig')
            print(f"清洗后数据加载成功: {self.df.shape}")
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def analyze_university_distribution(self):
        """分析申请院校分布"""
        print("\n" + "="*60)
        print("申请院校分布分析")
        print("="*60)
        
        # 院校申请频次
        uni_counts = self.df['申请院校_院校名称'].value_counts()
        print("申请最多的前20所院校:")
        for i, (uni, count) in enumerate(uni_counts.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {uni}: {count} ({percentage:.1f}%)")
        
        # 统计不同层次院校的申请情况
        return uni_counts
    
    def analyze_major_distribution(self):
        """分析专业分布"""
        print("\n" + "="*60)
        print("申请专业分布分析")
        print("="*60)
        
        major_counts = self.df['申请院校_专业名称'].value_counts()
        print("申请最多的前20个专业:")
        for i, (major, count) in enumerate(major_counts.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {major}: {count} ({percentage:.1f}%)")
            
        return major_counts
    
    def analyze_education_background(self):
        """分析教育背景分布"""
        print("\n" + "="*60)
        print("教育背景分布分析")
        print("="*60)
        
        # 毕业院校分布
        print("毕业院校TOP20:")
        grad_school_counts = self.df['教育经历_毕业院校'].value_counts()
        for i, (school, count) in enumerate(grad_school_counts.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {school}: {count} ({percentage:.1f}%)")
        
        # 专业分布
        print("\n本科专业TOP20:")
        undergrad_major_counts = self.df['教育经历_所学专业'].value_counts()
        for i, (major, count) in enumerate(undergrad_major_counts.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {major}: {count} ({percentage:.1f}%)")
        
        return grad_school_counts, undergrad_major_counts
    
    def analyze_gpa_distribution(self):
        """分析GPA分布"""
        print("\n" + "="*60)
        print("GPA分布分析")
        print("="*60)
        
        gpa_col = '教育经历_GPA成绩_百分制'
        valid_gpa = self.df[gpa_col].dropna()
        
        print(f"有效GPA记录数: {len(valid_gpa)}")
        print(f"GPA统计信息:")
        print(f"  平均值: {valid_gpa.mean():.2f}")
        print(f"  中位数: {valid_gpa.median():.2f}")
        print(f"  标准差: {valid_gpa.std():.2f}")
        print(f"  最小值: {valid_gpa.min():.2f}")
        print(f"  最大值: {valid_gpa.max():.2f}")
        
        # GPA分段分析
        gpa_ranges = pd.cut(valid_gpa, bins=[0, 60, 70, 75, 80, 85, 90, 100], 
                           labels=['<60', '60-70', '70-75', '75-80', '80-85', '85-90', '90+'])
        print(f"\nGPA分段分布:")
        for range_name, count in gpa_ranges.value_counts().sort_index().items():
            percentage = count / len(valid_gpa) * 100
            print(f"  {range_name}: {count} ({percentage:.1f}%)")
            
        return valid_gpa
    
    def analyze_language_scores(self):
        """分析语言成绩分布"""
        print("\n" + "="*60)
        print("语言成绩分布分析")
        print("="*60)
        
        # 筛选有语言成绩的记录
        has_lang = self.df[self.df['语言考试_考试类型'] != '无语言成绩']
        print(f"有语言成绩记录数: {len(has_lang)} ({len(has_lang)/len(self.df)*100:.1f}%)")
        
        if len(has_lang) > 0:
            print("\n语言考试类型分布:")
            lang_type_counts = has_lang['语言考试_考试类型'].value_counts()
            for test_type, count in lang_type_counts.items():
                percentage = count / len(has_lang) * 100
                print(f"  {test_type}: {count} ({percentage:.1f}%)")
        
        return has_lang
    
    def analyze_work_experience(self):
        """分析工作经验分布"""
        print("\n" + "="*60)
        print("工作经验分布分析")
        print("="*60)
        
        # 筛选有工作经验的记录
        has_work = self.df[self.df['工作经历_开始时间'] != '无工作经验']
        print(f"有工作经验记录数: {len(has_work)} ({len(has_work)/len(self.df)*100:.1f}%)")
        
        if len(has_work) > 0:
            print("\n工作职位TOP10:")
            position_counts = has_work['工作经历_职位名称'].value_counts()
            for i, (position, count) in enumerate(position_counts.head(10).items(), 1):
                percentage = count / len(has_work) * 100
                print(f"{i:2d}. {position}: {count} ({percentage:.1f}%)")
        
        return has_work
    
    def identify_feature_opportunities(self):
        """识别特征工程机会"""
        print("\n" + "="*60)
        print("特征工程机会分析")
        print("="*60)
        
        opportunities = []
        
        # 1. 院校层次特征
        opportunities.append({
            'type': '院校层次特征',
            'description': '根据申请院校的知名度和排名构造院校层次等级',
            'approach': '基于申请频次、QS排名等构建院校分层'
        })
        
        # 2. 专业匹配度特征
        opportunities.append({
            'type': '专业匹配度特征',
            'description': '计算申请专业与本科专业的相关性',
            'approach': '使用文本相似度、专业分类映射'
        })
        
        # 3. 学术实力特征
        opportunities.append({
            'type': '学术实力特征',
            'description': '综合GPA、院校背景等构造学术实力评分',
            'approach': 'GPA标准化 + 院校权重加权'
        })
        
        # 4. 语言能力特征
        opportunities.append({
            'type': '语言能力特征',
            'description': '标准化不同类型语言考试成绩',
            'approach': 'IELTS/TOEFL/PTE等效转换'
        })
        
        # 5. 工作经验特征
        opportunities.append({
            'type': '工作经验特征',
            'description': '量化工作经验的相关性和时长',
            'approach': '工作时长、职位层级、行业相关性'
        })
        
        # 6. 申请竞争度特征
        opportunities.append({
            'type': '申请竞争度特征',
            'description': '目标院校专业的申请难度',
            'approach': '基于历史申请数据计算竞争指数'
        })
        
        # 7. 时间相关特征
        opportunities.append({
            'type': '时间相关特征',
            'description': '申请时间、准备周期等时序特征',
            'approach': '申请年份、准备时长、时间间隔'
        })
        
        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. {opp['type']}")
            print(f"   描述: {opp['description']}")
            print(f"   方法: {opp['approach']}")
            print()
        
        return opportunities
    
    def run_full_analysis(self):
        """运行完整的特征分析"""
        if not self.load_cleaned_data():
            return None
        
        results = {}
        results['university_dist'] = self.analyze_university_distribution()
        results['major_dist'] = self.analyze_major_distribution()
        results['education_bg'] = self.analyze_education_background()
        results['gpa_dist'] = self.analyze_gpa_distribution()
        results['language_scores'] = self.analyze_language_scores()
        results['work_exp'] = self.analyze_work_experience()
        results['opportunities'] = self.identify_feature_opportunities()
        
        return results

if __name__ == "__main__":
    analyzer = FeatureAnalyzer()
    results = analyzer.run_full_analysis()