import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, DATA_RAW_DIR, DATA_EXTERNAL_DIR

class ChinaUniversityTierBuilder:
    """中国院校层次特征构造器"""
    
    def __init__(self):
        self.df = None
        self.china_universities = None
        self.tier_mapping = {}
        
    def load_data(self):
        """加载数据"""
        # 加载主数据
        try:
            self.df = pd.read_csv(DATA_PROCESSED_DIR / 'cleaned_offer_data_standardized.csv', encoding='utf-8-sig')
            print(f"主数据加载成功: {self.df.shape}")
        except Exception as e:
            print(f"主数据加载失败: {e}")
            return False
        
        # 加载中国院校数据
        try:
            self.china_universities = pd.read_excel(DATA_RAW_DIR / '中国院校 校对.xlsx')
            print(f"中国院校数据加载成功: {len(self.china_universities)}所院校")
            print(f"中国院校数据列名: {list(self.china_universities.columns)}")
        except Exception as e:
            print(f"中国院校数据加载失败: {e}")
            return False
            
        return True
    
    def analyze_china_university_data(self):
        """分析中国院校数据结构"""
        print("\n" + "="*60)
        print("中国院校数据分析")
        print("="*60)
        
        # 显示基本信息
        print(f"院校总数: {len(self.china_universities)}")
        
        # 分析各字段的分布
        for col in self.china_universities.columns:
            if col in ['院校名称', '院校ID']:
                continue
                
            print(f"\n{col} 字段分布:")
            value_counts = self.china_universities[col].value_counts()
            for value, count in value_counts.head(10).items():
                percentage = count / len(self.china_universities) * 100
                print(f"  {value}: {count} ({percentage:.1f}%)")
                
            if len(value_counts) > 10:
                print(f"  ... 还有{len(value_counts)-10}个其他值")
    
    def create_university_tier_system(self):
        """创建院校层次体系"""
        print("\n" + "="*60)
        print("构建中国院校层次体系")
        print("="*60)
        
        tier_mapping = {}
        
        # 遍历每所院校，根据标识确定层次
        for _, row in self.china_universities.iterrows():
            university_name = row['院校名称']
            school_type = row.get('办学层次', '')
            is_double_first = row.get('是否双一流', '')
            university_type = row.get('院校类型', '')  # 正确的985/211标识字段
            
            # 确定层次 - 修复985院校识别逻辑
            if 'C9' in str(university_type) or '985' in str(university_type):
                tier = 1  # C1: 985院校
                tier_desc = "C1-985院校"
            elif '211' in str(university_type) or '双一流' in str(is_double_first):
                tier = 2  # C2: 211/双一流院校
                tier_desc = "C2-211/双一流院校"
            elif school_type == '本科' or '本科' in str(school_type):
                tier = 4  # C4: 本科院校
                tier_desc = "C4-本科院校"
            elif school_type == '专科' or '专科' in str(school_type):
                tier = 5  # C5: 专科院校
                tier_desc = "C5-专科院校"
            else:
                tier = 4  # 默认归为本科层次
                tier_desc = "C4-本科院校"
            
            tier_mapping[university_name] = {
                'tier': tier,
                'tier_desc': tier_desc,
                'is_985': 1 if tier == 1 else 0,
                'is_211': 1 if tier <= 2 else 0,
                'is_double_first_class': 1 if ('双一流' in str(is_double_first) or tier <= 2) else 0
            }
        
        self.tier_mapping = tier_mapping
        
        # 统计各层次分布
        tier_stats = {}
        for info in tier_mapping.values():
            tier_desc = info['tier_desc']
            tier_stats[tier_desc] = tier_stats.get(tier_desc, 0) + 1
        
        print("中国院校层次分布:")
        for tier_desc, count in sorted(tier_stats.items()):
            percentage = count / len(tier_mapping) * 100
            print(f"  {tier_desc}: {count}所 ({percentage:.1f}%)")
        
        return tier_mapping
    
    def apply_tier_features_to_data(self):
        """将层次特征应用到主数据"""
        print("\n" + "="*60)
        print("应用中国院校层次特征")
        print("="*60)
        
        # 提取毕业院校列表
        source_universities = self.df['教育经历_毕业院校'].unique()
        print(f"数据中的毕业院校数量: {len(source_universities)}")
        
        # 初始化新特征列
        self.df['source_university_tier'] = 4  # 默认为C4本科
        self.df['source_university_tier_desc'] = 'C4-本科院校'
        self.df['source_is_985'] = 0
        self.df['source_is_211'] = 0  
        self.df['source_is_double_first_class'] = 0
        
        # 匹配统计
        matched_count = 0
        unmatched_count = 0
        
        # 为每条记录分配层次特征
        for idx, row in self.df.iterrows():
            university = row['教育经历_毕业院校']
            
            if pd.isna(university):
                continue
                
            # 精确匹配
            if university in self.tier_mapping:
                tier_info = self.tier_mapping[university]
                self.df.at[idx, 'source_university_tier'] = tier_info['tier']
                self.df.at[idx, 'source_university_tier_desc'] = tier_info['tier_desc']
                self.df.at[idx, 'source_is_985'] = tier_info['is_985']
                self.df.at[idx, 'source_is_211'] = tier_info['is_211']
                self.df.at[idx, 'source_is_double_first_class'] = tier_info['is_double_first_class']
                matched_count += 1
            else:
                # 尝试模糊匹配或手动匹配
                matched_tier = self._manual_university_matching(university)
                if matched_tier:
                    self.df.at[idx, 'source_university_tier'] = matched_tier['tier']
                    self.df.at[idx, 'source_university_tier_desc'] = matched_tier['tier_desc']
                    self.df.at[idx, 'source_is_985'] = matched_tier['is_985']
                    self.df.at[idx, 'source_is_211'] = matched_tier['is_211']
                    self.df.at[idx, 'source_is_double_first_class'] = matched_tier['is_double_first_class']
                    matched_count += 1
                else:
                    unmatched_count += 1
        
        print(f"院校层次匹配结果:")
        print(f"  匹配成功: {matched_count}条记录")
        print(f"  未匹配: {unmatched_count}条记录")
        
        # 统计最终分布
        print(f"\n数据中的院校层次分布:")
        tier_dist = self.df['source_university_tier_desc'].value_counts()
        for tier_desc, count in tier_dist.items():
            percentage = count / len(self.df) * 100
            print(f"  {tier_desc}: {count}条 ({percentage:.1f}%)")
    
    def _manual_university_matching(self, university):
        """手动匹配一些常见的院校变体"""
        # 985院校手动匹配
        c1_universities = {
            'Beijing University': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            'Tsinghua University': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            'Peking University': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '北京大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '清华大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '复旦大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '上海交通大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '浙江大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '南京大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '中山大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '华中科技大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '四川大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '西安交通大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '中南大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '山东大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '吉林大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '厦门大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '同济大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '东南大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '天津大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '华南理工大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '北京理工大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '大连理工大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '北京航空航天大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '重庆大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '湖南大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '兰州大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '电子科技大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '东北大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '西北工业大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '西北农林科技大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '华东师范大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '中国海洋大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '中央民族大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
            '国防科技大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},
        }
        
        # 211院校手动匹配(部分)
        c2_universities = {
            '北京交通大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京工业大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京科技大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京化工大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京邮电大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京林业大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京中医药大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京外国语大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国传媒大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '对外经济贸易大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中央财经大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国政法大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '华北电力大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国矿业大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国石油大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国地质大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中南财经政法大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '华中师范大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '中国农业大学': {'tier': 2, 'tier_desc': 'C2-211/双一流院校', 'is_985': 0, 'is_211': 1, 'is_double_first_class': 1},
            '北京师范大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},  # 985
            '中国人民大学': {'tier': 1, 'tier_desc': 'C1-985院校', 'is_985': 1, 'is_211': 1, 'is_double_first_class': 1},  # 985
        }
        
        # 海外知名中国相关院校
        overseas_chinese_universities = {
            'University of Toronto': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'The University of Sydney': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'The University of Melbourne': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'University of Melbourne': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'UNSW': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'USYD': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
            'Monash University': {'tier': 1, 'tier_desc': 'C1-海外知名院校', 'is_985': 0, 'is_211': 0, 'is_double_first_class': 0},
        }
        
        # 合并所有手动映射
        manual_mapping = {**c1_universities, **c2_universities, **overseas_chinese_universities}
        
        return manual_mapping.get(university, None)
    
    def create_university_tier_score(self):
        """创建院校层次评分"""
        print("\n" + "="*60)
        print("创建院校层次评分")
        print("="*60)
        
        # 层次评分映射
        tier_score_mapping = {
            1: 100,  # C1-985院校
            2: 85,   # C2-211/双一流院校
            3: 70,   # C3-双一流院校
            4: 60,   # C4-本科院校
            5: 50    # C5-专科院校
        }
        
        # 添加层次评分
        self.df['source_university_tier_score'] = self.df['source_university_tier'].map(tier_score_mapping)
        
        # 统计评分分布
        score_dist = self.df['source_university_tier_score'].value_counts().sort_index(ascending=False)
        print("院校层次评分分布:")
        for score, count in score_dist.items():
            percentage = count / len(self.df) * 100
            tier_name = {100: 'C1-985院校', 85: 'C2-211/双一流', 70: 'C3-双一流', 60: 'C4-本科', 50: 'C5-专科'}.get(score, '未知')
            print(f"  {score}分 ({tier_name}): {count}条 ({percentage:.1f}%)")
    
    def save_tier_mapping(self):
        """保存层次映射数据"""
        if self.tier_mapping:
            tier_df = pd.DataFrame.from_dict(self.tier_mapping, orient='index').reset_index()
            tier_df.columns = ['university_name', 'tier', 'tier_desc', 'is_985', 'is_211', 'is_double_first_class']
            
            output_path = DATA_EXTERNAL_DIR / 'china_university_tiers.csv'
            tier_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n院校层次映射已保存: {output_path}")
            
            return output_path
        return None
    
    def save_enhanced_data(self):
        """保存添加了层次特征的数据"""
        output_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_with_china_tiers.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"添加中国院校层次特征的数据已保存: {output_path}")
        return output_path
    
    def generate_tier_analysis_report(self):
        """生成层次特征分析报告"""
        print("\n" + "="*60)
        print("中国院校层次特征分析报告")
        print("="*60)
        
        # 985院校学生分布
        print("985院校学生分布:")
        is_985_dist = self.df['source_is_985'].value_counts()
        for is_985, count in is_985_dist.items():
            percentage = count / len(self.df) * 100
            status = "985院校" if is_985 == 1 else "非985院校"
            print(f"  {status}: {count}条 ({percentage:.1f}%)")
        
        # 211院校学生分布
        print("\n211院校学生分布:")
        is_211_dist = self.df['source_is_211'].value_counts()
        for is_211, count in is_211_dist.items():
            percentage = count / len(self.df) * 100
            status = "211院校" if is_211 == 1 else "非211院校"
            print(f"  {status}: {count}条 ({percentage:.1f}%)")
        
        # 双一流院校学生分布
        print("\n双一流院校学生分布:")
        is_double_first_dist = self.df['source_is_double_first_class'].value_counts()
        for is_double_first, count in is_double_first_dist.items():
            percentage = count / len(self.df) * 100
            status = "双一流院校" if is_double_first == 1 else "非双一流院校"
            print(f"  {status}: {count}条 ({percentage:.1f}%)")
        
        # 层次评分统计
        print(f"\n院校层次评分统计:")
        print(f"  平均分: {self.df['source_university_tier_score'].mean():.1f}")
        print(f"  中位数: {self.df['source_university_tier_score'].median():.1f}")
        print(f"  标准差: {self.df['source_university_tier_score'].std():.1f}")
    
    def run_china_tier_construction(self):
        """执行完整的中国院校层次特征构造流程"""
        print("="*60)
        print("中国院校层次特征构造")
        print("="*60)
        
        if not self.load_data():
            return None
        
        # 分析中国院校数据
        self.analyze_china_university_data()
        
        # 创建层次体系
        self.create_university_tier_system()
        
        # 应用层次特征
        self.apply_tier_features_to_data()
        
        # 创建层次评分
        self.create_university_tier_score()
        
        # 生成分析报告
        self.generate_tier_analysis_report()
        
        # 保存数据
        tier_mapping_path = self.save_tier_mapping()
        enhanced_data_path = self.save_enhanced_data()
        
        return enhanced_data_path, tier_mapping_path

if __name__ == "__main__":
    builder = ChinaUniversityTierBuilder()
    result = builder.run_china_tier_construction()