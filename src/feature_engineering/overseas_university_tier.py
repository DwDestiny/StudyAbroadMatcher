import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, DATA_EXTERNAL_DIR

class OverseasUniversityTierBuilder:
    """海外院校层次特征构造器"""
    
    def __init__(self):
        self.df = None
        self.qs_ranking = None
        self.university_mapping = {}
        
    def load_data(self):
        """加载数据"""
        # 加载主数据
        try:
            self.df = pd.read_csv(DATA_PROCESSED_DIR / 'cleaned_offer_data_with_china_tiers.csv', encoding='utf-8-sig')
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
            
        return True
    
    def analyze_target_universities(self):
        """分析申请院校分布"""
        print("\n" + "="*60)
        print("申请院校分布分析")
        print("="*60)
        
        target_unis = self.df['申请院校_院校名称_标准化'].value_counts()
        print(f"申请院校总数: {len(target_unis)}")
        
        print(f"\n申请最多的前20所院校:")
        for i, (uni, count) in enumerate(target_unis.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {uni}: {count} ({percentage:.1f}%)")
        
        return target_unis
    
    def create_university_tier_mapping(self):
        """创建海外院校层次映射"""
        print("\n" + "="*60)
        print("构建海外院校层次映射")
        print("="*60)
        
        # 从QS排名数据创建映射
        university_mapping = {}
        
        for _, row in self.qs_ranking.iterrows():
            university = row['university']
            qs_rank = row['qs_rank']
            tier = row['university_tier']
            country = row['country']
            tier_desc = row['tier_description']
            
            university_mapping[university] = {
                'qs_rank': qs_rank,
                'university_tier': tier,
                'tier_description': tier_desc,
                'country': country,
                'tier_score': self._calculate_tier_score(tier, qs_rank)
            }
        
        # 添加未在QS排名中但常见的院校
        additional_universities = self._get_additional_universities()
        university_mapping.update(additional_universities)
        
        self.university_mapping = university_mapping
        
        # 统计层次分布
        tier_stats = {}
        for info in university_mapping.values():
            tier_desc = info['tier_description']
            tier_stats[tier_desc] = tier_stats.get(tier_desc, 0) + 1
        
        print("海外院校层次分布:")
        for tier_desc, count in sorted(tier_stats.items()):
            print(f"  {tier_desc}: {count}所")
        
        return university_mapping
    
    def _calculate_tier_score(self, tier, qs_rank):
        """根据层次和QS排名计算评分"""
        base_scores = {1: 95, 2: 85, 3: 75, 4: 65}
        base_score = base_scores.get(tier, 65)
        
        # 根据QS排名进行细微调整
        if pd.notna(qs_rank):
            if qs_rank <= 10:
                adjustment = 5
            elif qs_rank <= 25:
                adjustment = 3
            elif qs_rank <= 50:
                adjustment = 0
            elif qs_rank <= 100:
                adjustment = -5
            elif qs_rank <= 200:
                adjustment = -10
            else:
                adjustment = -15
        else:
            adjustment = -20  # 未排名院校
        
        return max(min(base_score + adjustment, 100), 50)
    
    def _get_additional_universities(self):
        """添加QS排名外的其他常见院校"""
        additional_universities = {
            # 美国社区学院和其他院校
            'Santa Monica College': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'USA',
                'tier_score': 55
            },
            'De Anza College': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'USA',
                'tier_score': 55
            },
            
            # 澳洲其他院校
            'Australian Institute of Business': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'Australia',
                'tier_score': 60
            },
            'Federation University Australia': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'Australia',
                'tier_score': 60
            },
            
            # 英国其他院校
            'University of Hertfordshire': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'UK',
                'tier_score': 65
            },
            'Coventry University': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'UK',
                'tier_score': 65
            },
            
            # 加拿大其他院校
            'Seneca College': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'Canada',
                'tier_score': 60
            },
            'Centennial College': {
                'qs_rank': np.nan,
                'university_tier': 4,
                'tier_description': 'Regular Tier (QS 300+ or Unranked)',
                'country': 'Canada',
                'tier_score': 60
            },
        }
        
        return additional_universities
    
    def apply_overseas_tier_features(self):
        """将海外院校层次特征应用到数据"""
        print("\n" + "="*60)
        print("应用海外院校层次特征")
        print("="*60)
        
        # 初始化新特征列
        self.df['target_university_tier'] = 4  # 默认为T4
        self.df['target_university_tier_desc'] = 'Regular Tier (QS 300+ or Unranked)'
        self.df['target_university_qs_rank'] = np.nan
        self.df['target_university_tier_score'] = 65  # 默认评分
        self.df['target_university_country'] = 'Unknown'
        
        # 匹配统计
        matched_count = 0
        unmatched_count = 0
        unmatched_universities = set()
        
        # 为每条记录分配层次特征
        for idx, row in self.df.iterrows():
            university = row['申请院校_院校名称_标准化']
            
            if pd.isna(university):
                continue
            
            # 尝试精确匹配
            if university in self.university_mapping:
                tier_info = self.university_mapping[university]
                self.df.at[idx, 'target_university_tier'] = tier_info['university_tier']
                self.df.at[idx, 'target_university_tier_desc'] = tier_info['tier_description']
                self.df.at[idx, 'target_university_qs_rank'] = tier_info['qs_rank']
                self.df.at[idx, 'target_university_tier_score'] = tier_info['tier_score']
                self.df.at[idx, 'target_university_country'] = tier_info['country']
                matched_count += 1
            else:
                # 尝试手动匹配一些变体
                matched_tier = self._manual_overseas_matching(university)
                if matched_tier:
                    self.df.at[idx, 'target_university_tier'] = matched_tier['university_tier']
                    self.df.at[idx, 'target_university_tier_desc'] = matched_tier['tier_description']
                    self.df.at[idx, 'target_university_qs_rank'] = matched_tier['qs_rank']
                    self.df.at[idx, 'target_university_tier_score'] = matched_tier['tier_score']
                    self.df.at[idx, 'target_university_country'] = matched_tier['country']
                    matched_count += 1
                else:
                    unmatched_count += 1
                    unmatched_universities.add(university)
        
        print(f"海外院校层次匹配结果:")
        print(f"  匹配成功: {matched_count}条记录")
        print(f"  未匹配: {unmatched_count}条记录")
        print(f"  未匹配院校数: {len(unmatched_universities)}所")
        
        # 显示前10个未匹配的院校
        if unmatched_universities:
            print(f"\n未匹配院校样本 (前10个):")
            for i, uni in enumerate(list(unmatched_universities)[:10], 1):
                count = (self.df['申请院校_院校名称_标准化'] == uni).sum()
                print(f"  {i}. {uni}: {count}条申请")
    
    def _manual_overseas_matching(self, university):
        """手动匹配一些院校变体"""
        # 手动映射一些常见变体
        manual_mapping = {
            # 澳洲院校变体
            'Sydney University': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 41, 'country': 'Australia', 'tier_score': 95},
            'Melbourne University': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 37, 'country': 'Australia', 'tier_score': 98},
            'UNSW': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 45, 'country': 'Australia', 'tier_score': 95},
            
            # 英国院校变体
            'Oxford University': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 3, 'country': 'UK', 'tier_score': 100},
            'Cambridge University': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 2, 'country': 'UK', 'tier_score': 100},
            
            # 美国院校变体
            'MIT': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 1, 'country': 'USA', 'tier_score': 100},
            'Harvard': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 4, 'country': 'USA', 'tier_score': 100},
            'Stanford': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 5, 'country': 'USA', 'tier_score': 100},
            
            # 加拿大院校变体
            'UofT': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 25, 'country': 'Canada', 'tier_score': 98},
            'Toronto University': {'university_tier': 1, 'tier_description': 'Top Tier (QS 1-50)', 'qs_rank': 25, 'country': 'Canada', 'tier_score': 98},
        }
        
        return manual_mapping.get(university, None)
    
    def create_application_volume_features(self):
        """创建申请热度特征"""
        print("\n" + "="*60)
        print("创建申请热度特征")
        print("="*60)
        
        # 计算每所院校的申请量
        university_volumes = self.df['申请院校_院校名称_标准化'].value_counts()
        
        # 创建申请量映射
        volume_mapping = {}
        for university, count in university_volumes.items():
            if count >= 10000:
                volume_level = 'Ultra High'
                volume_score = 100
            elif count >= 5000:
                volume_level = 'Very High'
                volume_score = 90
            elif count >= 1000:
                volume_level = 'High'
                volume_score = 80
            elif count >= 500:
                volume_level = 'Medium High'
                volume_score = 70
            elif count >= 100:
                volume_level = 'Medium'
                volume_score = 60
            elif count >= 50:
                volume_level = 'Low Medium'
                volume_score = 50
            else:
                volume_level = 'Low'
                volume_score = 40
            
            volume_mapping[university] = {
                'application_count': count,
                'volume_level': volume_level,
                'volume_score': volume_score
            }
        
        # 应用到数据
        self.df['target_university_application_count'] = self.df['申请院校_院校名称_标准化'].map(
            {k: v['application_count'] for k, v in volume_mapping.items()}
        )
        self.df['target_university_volume_level'] = self.df['申请院校_院校名称_标准化'].map(
            {k: v['volume_level'] for k, v in volume_mapping.items()}
        )
        self.df['target_university_volume_score'] = self.df['申请院校_院校名称_标准化'].map(
            {k: v['volume_score'] for k, v in volume_mapping.items()}
        )
        
        # 统计申请热度分布
        print("申请热度分布:")
        volume_dist = self.df['target_university_volume_level'].value_counts()
        for level, count in volume_dist.items():
            percentage = count / len(self.df) * 100
            print(f"  {level}: {count}条 ({percentage:.1f}%)")
    
    def generate_overseas_tier_analysis(self):
        """生成海外院校层次特征分析报告"""
        print("\n" + "="*60)
        print("海外院校层次特征分析报告")
        print("="*60)
        
        # 目标院校层次分布
        print("目标院校层次分布:")
        tier_dist = self.df['target_university_tier_desc'].value_counts()
        for tier_desc, count in tier_dist.items():
            percentage = count / len(self.df) * 100
            print(f"  {tier_desc}: {count}条 ({percentage:.1f}%)")
        
        # 目标院校国家分布
        print("\n目标院校国家分布:")
        country_dist = self.df['target_university_country'].value_counts()
        for country, count in country_dist.items():
            percentage = count / len(self.df) * 100
            print(f"  {country}: {count}条 ({percentage:.1f}%)")
        
        # QS排名统计
        qs_ranks = self.df['target_university_qs_rank'].dropna()
        if len(qs_ranks) > 0:
            print(f"\n目标院校QS排名统计:")
            print(f"  有排名院校: {len(qs_ranks)}条 ({len(qs_ranks)/len(self.df)*100:.1f}%)")
            print(f"  平均排名: {qs_ranks.mean():.1f}")
            print(f"  中位数排名: {qs_ranks.median():.1f}")
            print(f"  最好排名: {qs_ranks.min()}")
            print(f"  最差排名: {qs_ranks.max()}")
        
        # 院校层次评分统计
        print(f"\n目标院校层次评分统计:")
        print(f"  平均分: {self.df['target_university_tier_score'].mean():.1f}")
        print(f"  中位数: {self.df['target_university_tier_score'].median():.1f}")
        print(f"  标准差: {self.df['target_university_tier_score'].std():.1f}")
        print(f"  最高分: {self.df['target_university_tier_score'].max()}")
        print(f"  最低分: {self.df['target_university_tier_score'].min()}")
    
    def save_enhanced_data(self):
        """保存添加了海外院校层次特征的数据"""
        output_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_with_university_tiers.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n添加海外院校层次特征的数据已保存: {output_path}")
        return output_path
    
    def save_university_mapping(self):
        """保存院校映射数据"""
        if self.university_mapping:
            mapping_df = pd.DataFrame.from_dict(self.university_mapping, orient='index').reset_index()
            mapping_df.columns = ['university_name', 'qs_rank', 'university_tier', 'tier_description', 'country', 'tier_score']
            
            output_path = DATA_EXTERNAL_DIR / 'overseas_university_tiers.csv'
            mapping_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"海外院校层次映射已保存: {output_path}")
            
            return output_path
        return None
    
    def run_overseas_tier_construction(self):
        """执行完整的海外院校层次特征构造流程"""
        print("="*60)
        print("海外院校层次特征构造")
        print("="*60)
        
        if not self.load_data():
            return None
        
        # 分析申请院校分布
        self.analyze_target_universities()
        
        # 创建层次映射
        self.create_university_tier_mapping()
        
        # 应用层次特征
        self.apply_overseas_tier_features()
        
        # 创建申请热度特征
        self.create_application_volume_features()
        
        # 生成分析报告
        self.generate_overseas_tier_analysis()
        
        # 保存数据
        mapping_path = self.save_university_mapping()
        enhanced_data_path = self.save_enhanced_data()
        
        return enhanced_data_path, mapping_path

if __name__ == "__main__":
    builder = OverseasUniversityTierBuilder()
    result = builder.run_overseas_tier_construction()