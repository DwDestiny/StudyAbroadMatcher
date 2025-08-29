import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, DATA_EXTERNAL_DIR, OUTPUT_REPORTS_DIR

class OverseasUniversityFeatureBuilder:
    """海外院校层次特征构造器 - 基于QS排名和申请热度"""
    
    def __init__(self):
        self.df = None
        self.qs_ranking = None
        self.overseas_mapping = {}
        self.domestic_keywords = ['大学', '学院', '科技大学', '师范大学', '工业大学', '理工大学', 
                                '财经大学', '医科大学', '农业大学', '交通大学', '电力大学',
                                '石油大学', '民族大学', '政法大学', '外国语大学', '体育大学']
        
    def load_data(self):
        """加载数据"""
        try:
            # 加载主数据
            self.df = pd.read_csv(DATA_PROCESSED_DIR / 'cleaned_offer_data_with_comprehensive_university_features.csv', encoding='utf-8-sig')
            print(f"主数据加载成功: {self.df.shape}")
            
            # 加载QS排名数据
            self.qs_ranking = pd.read_csv(DATA_EXTERNAL_DIR / 'qs_university_rankings.csv', encoding='utf-8-sig')
            print(f"QS排名数据加载成功: {len(self.qs_ranking)}所院校")
            
            return True
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def identify_overseas_universities(self):
        """识别海外院校"""
        print("\n" + "="*60)
        print("识别海外院校")
        print("="*60)
        
        # 获取所有申请院校
        target_universities = self.df['申请院校_院校名称_标准化'].dropna().unique()
        print(f"申请院校总数: {len(target_universities)}")
        
        # 分类院校
        domestic_universities = []
        overseas_universities = []
        
        for uni in target_universities:
            if self._is_domestic_university(uni):
                domestic_universities.append(uni)
            else:
                overseas_universities.append(uni)
        
        print(f"国内院校: {len(domestic_universities)}所")
        print(f"海外院校: {len(overseas_universities)}所")
        
        # 显示前20个海外院校
        print("\n主要海外申请院校:")
        overseas_counts = self.df[self.df['申请院校_院校名称_标准化'].isin(overseas_universities)]['申请院校_院校名称_标准化'].value_counts()
        
        for i, (uni, count) in enumerate(overseas_counts.head(20).items(), 1):
            percentage = count / len(self.df) * 100
            print(f"{i:2d}. {uni}: {count}条申请 ({percentage:.1f}%)")
        
        return overseas_universities, domestic_universities
    
    def _is_domestic_university(self, university_name):
        """判断是否为国内院校"""
        if pd.isna(university_name):
            return True
        
        university_name = str(university_name)
        
        # 包含明显国内院校关键词
        for keyword in self.domestic_keywords:
            if keyword in university_name:
                return True
        
        # 包含中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in university_name):
            return True
        
        # 特殊处理一些可能的国内院校
        domestic_patterns = ['北京', '上海', '天津', '重庆', '广州', '深圳', '杭州', '南京', 
                           '武汉', '成都', '西安', '沈阳', '大连', '青岛', '厦门']
        for pattern in domestic_patterns:
            if pattern in university_name:
                return True
        
        return False
    
    def build_overseas_university_mapping(self):
        """构建海外院校映射"""
        print("\n" + "="*60)
        print("构建海外院校层次映射")
        print("="*60)
        
        # 从QS排名数据创建基础映射
        overseas_mapping = {}
        
        for _, row in self.qs_ranking.iterrows():
            university = row['university']
            qs_rank = row['qs_rank'] if pd.notna(row['qs_rank']) else 999
            country = row['country']
            
            # 根据QS排名划分层次
            if qs_rank <= 50:
                tier = 1
                tier_name = 'T1'
                tier_desc = 'T1-顶级院校'
            elif qs_rank <= 100:
                tier = 2
                tier_name = 'T2'
                tier_desc = 'T2-高级院校'
            elif qs_rank <= 300:
                tier = 3
                tier_name = 'T3'
                tier_desc = 'T3-中级院校'
            else:
                tier = 4
                tier_name = 'T4'
                tier_desc = 'T4-普通院校'
            
            overseas_mapping[university] = {
                'qs_rank': qs_rank,
                'tier': tier,
                'tier_name': tier_name,
                'tier_desc': tier_desc,
                'country': country,
                'tier_score': self._calculate_tier_score(tier, qs_rank)
            }
        
        # 添加院校别名和常见变体
        overseas_mapping.update(self._get_university_aliases())
        
        self.overseas_mapping = overseas_mapping
        
        # 统计层次分布
        tier_stats = {}
        for info in overseas_mapping.values():
            tier_desc = info['tier_desc']
            tier_stats[tier_desc] = tier_stats.get(tier_desc, 0) + 1
        
        print("海外院校层次分布:")
        for tier_desc, count in sorted(tier_stats.items()):
            print(f"  {tier_desc}: {count}所")
        
        return overseas_mapping
    
    def _calculate_tier_score(self, tier, qs_rank):
        """计算院校层次评分"""
        # 基础评分
        base_scores = {1: 95, 2: 85, 3: 75, 4: 65}
        base_score = base_scores.get(tier, 65)
        
        # 根据QS排名细调
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
        elif qs_rank <= 300:
            adjustment = -15
        else:
            adjustment = -20
        
        return max(min(base_score + adjustment, 100), 50)
    
    def _get_university_aliases(self):
        """获取院校别名映射"""
        aliases = {
            # 澳洲院校别名
            'Sydney University': {
                'qs_rank': 41, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Australia', 'tier_score': 95
            },
            'Melbourne University': {
                'qs_rank': 37, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Australia', 'tier_score': 98
            },
            'UNSW': {
                'qs_rank': 45, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Australia', 'tier_score': 95
            },
            'UQ': {
                'qs_rank': 50, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Australia', 'tier_score': 95
            },
            'ANU': {
                'qs_rank': 34, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Australia', 'tier_score': 98
            },
            
            # 英国院校别名
            'Oxford University': {
                'qs_rank': 3, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'UK', 'tier_score': 100
            },
            'Cambridge University': {
                'qs_rank': 2, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'UK', 'tier_score': 100
            },
            'LSE': {
                'qs_rank': 32, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'UK', 'tier_score': 98
            },
            'KCL': {
                'qs_rank': 31, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'UK', 'tier_score': 98
            },
            
            # 美国院校别名
            'MIT': {
                'qs_rank': 1, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'USA', 'tier_score': 100
            },
            'Harvard': {
                'qs_rank': 4, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'USA', 'tier_score': 100
            },
            'Stanford': {
                'qs_rank': 5, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'USA', 'tier_score': 100
            },
            
            # 加拿大院校别名
            'UofT': {
                'qs_rank': 25, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Canada', 'tier_score': 98
            },
            'Toronto University': {
                'qs_rank': 25, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Canada', 'tier_score': 98
            },
            'UBC': {
                'qs_rank': 38, 'tier': 1, 'tier_name': 'T1', 'tier_desc': 'T1-顶级院校',
                'country': 'Canada', 'tier_score': 98
            },
        }
        
        return aliases
    
    def calculate_application_volume_features(self):
        """计算申请热度特征"""
        print("\n" + "="*60)
        print("计算申请热度特征")
        print("="*60)
        
        # 计算每所院校的申请量
        university_volumes = self.df['申请院校_院校名称_标准化'].value_counts()
        
        # 计算申请热度评分和等级
        volume_features = {}
        
        for university, count in university_volumes.items():
            # 根据申请量划分热度等级
            if count >= 10000:
                volume_tier = 'Ultra High'
                volume_score = 100
            elif count >= 5000:
                volume_tier = 'Very High'
                volume_score = 90
            elif count >= 1000:
                volume_tier = 'High'
                volume_score = 80
            elif count >= 500:
                volume_tier = 'Medium High'
                volume_score = 70
            elif count >= 100:
                volume_tier = 'Medium'
                volume_score = 60
            elif count >= 50:
                volume_tier = 'Low Medium'
                volume_score = 50
            else:
                volume_tier = 'Low'
                volume_score = 40
            
            volume_features[university] = {
                'application_volume': count,
                'volume_tier': volume_tier,
                'volume_score': volume_score
            }
        
        # 显示申请热度分布
        print("申请热度分布:")
        volume_distribution = {}
        for features in volume_features.values():
            tier = features['volume_tier']
            volume_distribution[tier] = volume_distribution.get(tier, 0) + 1
        
        for tier, count in sorted(volume_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tier}: {count}所院校")
        
        return volume_features
    
    def calculate_comprehensive_tier_score(self, qs_tier_score, volume_score):
        """计算综合层次评分"""
        # QS排名权重70%，申请热度权重30%
        return qs_tier_score * 0.7 + volume_score * 0.3
    
    def apply_overseas_university_features(self):
        """应用海外院校特征到数据集"""
        print("\n" + "="*60)
        print("应用海外院校特征")
        print("="*60)
        
        # 计算申请热度特征
        volume_features = self.calculate_application_volume_features()
        
        # 初始化新特征列
        self.df['is_overseas_university'] = False
        self.df['target_university_tier'] = 4
        self.df['target_university_tier_desc'] = 'T4-普通院校'
        self.df['target_university_tier_score'] = 65
        self.df['target_university_qs_rank'] = 999
        self.df['target_university_country'] = 'Unknown'
        self.df['target_university_application_volume'] = 0
        self.df['target_university_volume_tier'] = 'Low'
        self.df['target_university_volume_score'] = 40
        self.df['target_university_comprehensive_score'] = 65
        
        # 匹配统计
        overseas_matched = 0
        overseas_unmatched = 0
        domestic_count = 0
        unmatched_overseas = set()
        
        # 处理每条记录
        for idx, row in self.df.iterrows():
            university = row['申请院校_院校名称_标准化']
            
            if pd.isna(university):
                continue
            
            # 判断是否为海外院校
            if not self._is_domestic_university(university):
                self.df.at[idx, 'is_overseas_university'] = True
                
                # 获取申请热度特征
                if university in volume_features:
                    vol_features = volume_features[university]
                    self.df.at[idx, 'target_university_application_volume'] = vol_features['application_volume']
                    self.df.at[idx, 'target_university_volume_tier'] = vol_features['volume_tier']
                    self.df.at[idx, 'target_university_volume_score'] = vol_features['volume_score']
                
                # 匹配QS排名和层次信息
                if university in self.overseas_mapping:
                    tier_info = self.overseas_mapping[university]
                    self.df.at[idx, 'target_university_tier'] = tier_info['tier']
                    self.df.at[idx, 'target_university_tier_desc'] = tier_info['tier_desc']
                    self.df.at[idx, 'target_university_tier_score'] = tier_info['tier_score']
                    self.df.at[idx, 'target_university_qs_rank'] = tier_info['qs_rank']
                    self.df.at[idx, 'target_university_country'] = tier_info['country']
                    
                    # 计算综合评分
                    volume_score = self.df.at[idx, 'target_university_volume_score']
                    comprehensive_score = self.calculate_comprehensive_tier_score(
                        tier_info['tier_score'], volume_score
                    )
                    self.df.at[idx, 'target_university_comprehensive_score'] = comprehensive_score
                    
                    overseas_matched += 1
                else:
                    # 未匹配的海外院校，根据申请热度重新评估层次
                    volume_score = self.df.at[idx, 'target_university_volume_score']
                    if volume_score >= 90:  # 申请量>5000，提升到T1
                        self.df.at[idx, 'target_university_tier'] = 1
                        self.df.at[idx, 'target_university_tier_desc'] = 'T1-顶级院校'
                        self.df.at[idx, 'target_university_tier_score'] = 95
                    elif volume_score >= 80:  # 申请量>1000，提升到T2
                        self.df.at[idx, 'target_university_tier'] = 2
                        self.df.at[idx, 'target_university_tier_desc'] = 'T2-高级院校'
                        self.df.at[idx, 'target_university_tier_score'] = 85
                    elif volume_score >= 60:  # 申请量>100，提升到T3
                        self.df.at[idx, 'target_university_tier'] = 3
                        self.df.at[idx, 'target_university_tier_desc'] = 'T3-中级院校'
                        self.df.at[idx, 'target_university_tier_score'] = 75
                    
                    # 计算综合评分
                    tier_score = self.df.at[idx, 'target_university_tier_score']
                    comprehensive_score = self.calculate_comprehensive_tier_score(tier_score, volume_score)
                    self.df.at[idx, 'target_university_comprehensive_score'] = comprehensive_score
                    
                    overseas_unmatched += 1
                    unmatched_overseas.add(university)
            else:
                domestic_count += 1
        
        # 输出匹配结果
        print(f"海外院校特征应用结果:")
        print(f"  海外院校(QS匹配): {overseas_matched}条记录")
        print(f"  海外院校(未QS匹配): {overseas_unmatched}条记录")
        print(f"  国内院校: {domestic_count}条记录")
        print(f"  未匹配海外院校数: {len(unmatched_overseas)}所")
        
        # 显示未匹配的主要海外院校
        if unmatched_overseas:
            print(f"\n主要未匹配海外院校:")
            unmatched_volumes = {uni: volume_features.get(uni, {'application_volume': 0})['application_volume'] 
                               for uni in unmatched_overseas}
            sorted_unmatched = sorted(unmatched_volumes.items(), key=lambda x: x[1], reverse=True)
            
            for i, (uni, volume) in enumerate(sorted_unmatched[:10], 1):
                print(f"  {i}. {uni}: {volume}条申请")
        
        return overseas_matched, overseas_unmatched, domestic_count
    
    def generate_comprehensive_analysis(self):
        """生成综合分析报告"""
        print("\n" + "="*80)
        print("海外院校特征分析报告")
        print("="*80)
        
        # 海外院校vs国内院校分布
        overseas_count = self.df['is_overseas_university'].sum()
        domestic_count = len(self.df) - overseas_count
        
        print(f"院校类型分布:")
        print(f"  海外院校: {overseas_count}条申请 ({overseas_count/len(self.df)*100:.1f}%)")
        print(f"  国内院校: {domestic_count}条申请 ({domestic_count/len(self.df)*100:.1f}%)")
        
        # 海外院校层次分布
        overseas_df = self.df[self.df['is_overseas_university'] == True]
        
        print(f"\n海外院校层次分布:")
        tier_dist = overseas_df['target_university_tier_desc'].value_counts()
        for tier_desc, count in tier_dist.items():
            percentage = count / len(overseas_df) * 100
            print(f"  {tier_desc}: {count}条 ({percentage:.1f}%)")
        
        # 海外院校国家分布
        print(f"\n海外院校国家分布:")
        country_dist = overseas_df['target_university_country'].value_counts()
        for country, count in country_dist.items():
            percentage = count / len(overseas_df) * 100
            print(f"  {country}: {count}条 ({percentage:.1f}%)")
        
        # 申请热度分布
        print(f"\n海外院校申请热度分布:")
        volume_dist = overseas_df['target_university_volume_tier'].value_counts()
        for volume_tier, count in volume_dist.items():
            percentage = count / len(overseas_df) * 100
            print(f"  {volume_tier}: {count}条 ({percentage:.1f}%)")
        
        # QS排名统计
        qs_ranks = overseas_df['target_university_qs_rank']
        valid_ranks = qs_ranks[qs_ranks < 999]
        
        print(f"\n海外院校QS排名统计:")
        print(f"  有QS排名: {len(valid_ranks)}条 ({len(valid_ranks)/len(overseas_df)*100:.1f}%)")
        if len(valid_ranks) > 0:
            print(f"  平均排名: {valid_ranks.mean():.1f}")
            print(f"  中位数排名: {valid_ranks.median():.1f}")
            print(f"  最好排名: {valid_ranks.min()}")
            print(f"  最差排名: {valid_ranks.max()}")
        
        # 综合评分统计
        print(f"\n海外院校综合评分统计:")
        comp_scores = overseas_df['target_university_comprehensive_score']
        print(f"  平均分: {comp_scores.mean():.1f}")
        print(f"  中位数: {comp_scores.median():.1f}")
        print(f"  标准差: {comp_scores.std():.1f}")
        print(f"  最高分: {comp_scores.max():.1f}")
        print(f"  最低分: {comp_scores.min():.1f}")
        
        # 顶级院校申请分布
        top_tier_unis = overseas_df[overseas_df['target_university_tier'] == 1]['申请院校_院校名称_标准化'].value_counts()
        if len(top_tier_unis) > 0:
            print(f"\n顶级海外院校(T1)申请分布:")
            for i, (uni, count) in enumerate(top_tier_unis.head(10).items(), 1):
                percentage = count / len(overseas_df) * 100
                print(f"  {i}. {uni}: {count}条 ({percentage:.1f}%)")
    
    def save_results(self):
        """保存结果"""
        print("\n" + "="*60)
        print("保存结果")
        print("="*60)
        
        # 保存增强的数据集
        output_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_with_overseas_features.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"增强数据集已保存: {output_path}")
        
        # 保存海外院校映射
        if self.overseas_mapping:
            mapping_df = pd.DataFrame.from_dict(self.overseas_mapping, orient='index').reset_index()
            mapping_df.columns = ['university_name', 'qs_rank', 'tier', 'tier_name', 'tier_desc', 'country', 'tier_score']
            
            mapping_path = DATA_EXTERNAL_DIR / 'overseas_university_features.csv'
            mapping_df.to_csv(mapping_path, index=False, encoding='utf-8-sig')
            print(f"海外院校特征映射已保存: {mapping_path}")
        
        # 生成分析报告
        report_path = OUTPUT_REPORTS_DIR / 'overseas_university_analysis_report.md'
        self._generate_analysis_report(report_path)
        print(f"分析报告已保存: {report_path}")
        
        return output_path, mapping_path, report_path
    
    def _generate_analysis_report(self, report_path):
        """生成Markdown分析报告"""
        overseas_df = self.df[self.df['is_overseas_university'] == True]
        overseas_count = len(overseas_df)
        total_count = len(self.df)
        
        report_content = f"""# 海外院校特征分析报告

## 概述

本报告基于QS排名和申请热度对{total_count}条留学申请记录中的海外院校进行了特征分析。

## 主要发现

### 1. 院校类型分布

- **海外院校**: {overseas_count}条申请 ({overseas_count/total_count*100:.1f}%)
- **国内院校**: {total_count-overseas_count}条申请 ({(total_count-overseas_count)/total_count*100:.1f}%)

### 2. 海外院校层次分布

根据QS排名和申请热度，海外院校被分为四个层次：

"""
        
        # 添加层次分布
        tier_dist = overseas_df['target_university_tier_desc'].value_counts()
        for tier_desc, count in tier_dist.items():
            percentage = count / overseas_count * 100
            report_content += f"- **{tier_desc}**: {count}条申请 ({percentage:.1f}%)\n"
        
        report_content += f"""

### 3. 海外院校国家分布

"""
        
        # 添加国家分布
        country_dist = overseas_df['target_university_country'].value_counts()
        for country, count in country_dist.head(10).items():
            percentage = count / overseas_count * 100
            report_content += f"- **{country}**: {count}条申请 ({percentage:.1f}%)\n"
        
        report_content += f"""

### 4. 申请热度分析

基于申请量对院校热度进行分级：

"""
        
        # 添加申请热度分布
        volume_dist = overseas_df['target_university_volume_tier'].value_counts()
        for volume_tier, count in volume_dist.items():
            percentage = count / overseas_count * 100
            report_content += f"- **{volume_tier}**: {count}条申请 ({percentage:.1f}%)\n"
        
        # 添加QS排名统计
        qs_ranks = overseas_df['target_university_qs_rank']
        valid_ranks = qs_ranks[qs_ranks < 999]
        
        report_content += f"""

### 5. QS排名统计

- **有QS排名院校**: {len(valid_ranks)}条申请 ({len(valid_ranks)/overseas_count*100:.1f}%)
"""
        
        if len(valid_ranks) > 0:
            report_content += f"""- **平均排名**: {valid_ranks.mean():.1f}
- **中位数排名**: {valid_ranks.median():.1f}
- **最好排名**: {valid_ranks.min()}
- **最差排名**: {valid_ranks.max()}
"""
        
        # 添加顶级院校列表
        top_tier_unis = overseas_df[overseas_df['target_university_tier'] == 1]['申请院校_院校名称_标准化'].value_counts()
        if len(top_tier_unis) > 0:
            report_content += f"""

### 6. 顶级海外院校(T1)申请分布

"""
            for i, (uni, count) in enumerate(top_tier_unis.head(10).items(), 1):
                percentage = count / overseas_count * 100
                report_content += f"{i}. **{uni}**: {count}条申请 ({percentage:.1f}%)\n"
        
        report_content += f"""

## 层次划分标准

- **T1 (顶级院校)**: QS排名1-50 或 申请量>5,000
- **T2 (高级院校)**: QS排名51-100 或 申请量1,000-5,000  
- **T3 (中级院校)**: QS排名101-300 或 申请量100-1,000
- **T4 (普通院校)**: QS排名300+ 或 申请量<100

## 综合评分算法

综合评分 = QS层次评分 × 0.7 + 申请热度评分 × 0.3

报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 确保输出目录存在
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def run_complete_analysis(self):
        """执行完整的海外院校特征分析流程"""
        print("="*80)
        print("海外院校特征构造器 - 基于QS排名和申请热度")
        print("="*80)
        
        # 1. 加载数据
        if not self.load_data():
            return None
        
        # 2. 识别海外院校
        self.identify_overseas_universities()
        
        # 3. 构建海外院校映射
        self.build_overseas_university_mapping()
        
        # 4. 应用海外院校特征
        self.apply_overseas_university_features()
        
        # 5. 生成综合分析
        self.generate_comprehensive_analysis()
        
        # 6. 保存结果
        return self.save_results()

if __name__ == "__main__":
    builder = OverseasUniversityFeatureBuilder()
    results = builder.run_complete_analysis()
    
    if results:
        data_path, mapping_path, report_path = results
        print(f"\n✅ 海外院校特征构造完成!")
        print(f"📊 增强数据集: {data_path}")
        print(f"🏫 院校映射: {mapping_path}") 
        print(f"📋 分析报告: {report_path}")