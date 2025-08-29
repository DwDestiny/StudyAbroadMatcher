import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, OUTPUT_REPORTS_DIR

def analyze_overseas_university_features():
    """分析海外院校特征"""
    print("="*80)
    print("海外院校特征分析总结")
    print("="*80)
    
    # 加载数据
    df = pd.read_csv(DATA_PROCESSED_DIR / 'cleaned_offer_data_with_overseas_features.csv', encoding='utf-8-sig')
    print(f"数据加载成功: {len(df)}条记录")
    
    # 基本统计
    overseas_df = df[df['is_overseas_university'] == True]
    domestic_df = df[df['is_overseas_university'] == False]
    
    print(f"\n基本统计:")
    print(f"  总申请记录: {len(df)}条")
    print(f"  海外院校申请: {len(overseas_df)}条 ({len(overseas_df)/len(df)*100:.1f}%)")
    print(f"  国内院校申请: {len(domestic_df)}条 ({len(domestic_df)/len(df)*100:.1f}%)")
    
    # 海外院校层次分析
    print(f"\n海外院校层次分布:")
    tier_analysis = overseas_df['target_university_tier_desc'].value_counts()
    tier_percentages = overseas_df['target_university_tier_desc'].value_counts(normalize=True) * 100
    
    for tier in ['T1-顶级院校', 'T2-高级院校', 'T3-中级院校', 'T4-普通院校']:
        if tier in tier_analysis:
            count = tier_analysis[tier]
            percentage = tier_percentages[tier]
            print(f"  {tier}: {count:,}条 ({percentage:.1f}%)")
    
    # 国家分布分析
    print(f"\n目标国家分布:")
    country_analysis = overseas_df['target_university_country'].value_counts()
    country_percentages = overseas_df['target_university_country'].value_counts(normalize=True) * 100
    
    for country, count in country_analysis.head(10).items():
        percentage = country_percentages[country]
        print(f"  {country}: {count:,}条 ({percentage:.1f}%)")
    
    # 申请热度分析
    print(f"\n申请热度分析:")
    volume_analysis = overseas_df['target_university_volume_tier'].value_counts()
    volume_percentages = overseas_df['target_university_volume_tier'].value_counts(normalize=True) * 100
    
    volume_order = ['Ultra High', 'Very High', 'High', 'Medium High', 'Medium', 'Low Medium', 'Low']
    for volume_tier in volume_order:
        if volume_tier in volume_analysis:
            count = volume_analysis[volume_tier]
            percentage = volume_percentages[volume_tier]
            print(f"  {volume_tier}: {count:,}条 ({percentage:.1f}%)")
    
    # QS排名分析
    print(f"\nQS排名分析:")
    qs_ranks = overseas_df['target_university_qs_rank']
    valid_ranks = qs_ranks[qs_ranks < 999]
    
    print(f"  有QS排名的申请: {len(valid_ranks):,}条 ({len(valid_ranks)/len(overseas_df)*100:.1f}%)")
    if len(valid_ranks) > 0:
        print(f"  QS排名范围: {valid_ranks.min()} - {valid_ranks.max()}")
        print(f"  平均排名: {valid_ranks.mean():.1f}")
        print(f"  中位数排名: {valid_ranks.median():.0f}")
        
        # 排名区间分布
        print(f"\n  QS排名区间分布:")
        print(f"    1-50 (T1): {(valid_ranks <= 50).sum():,}条")
        print(f"    51-100 (T2): {((valid_ranks > 50) & (valid_ranks <= 100)).sum():,}条")
        print(f"    101-300 (T3): {((valid_ranks > 100) & (valid_ranks <= 300)).sum():,}条")
        print(f"    300+ (T4): {(valid_ranks > 300).sum():,}条")
    
    # 顶级院校分析
    print(f"\n顶级院校(T1)分析:")
    t1_unis = overseas_df[overseas_df['target_university_tier'] == 1]
    if len(t1_unis) > 0:
        t1_analysis = t1_unis['申请院校_院校名称_标准化'].value_counts()
        print(f"  T1院校申请总数: {len(t1_unis):,}条")
        print(f"  T1院校数量: {len(t1_analysis)}所")
        print(f"\n  申请最多的T1院校:")
        for i, (uni, count) in enumerate(t1_analysis.head(10).items(), 1):
            percentage = count / len(t1_unis) * 100
            print(f"    {i:2d}. {uni}: {count:,}条 ({percentage:.1f}%)")
    
    # 综合评分分析
    print(f"\n综合评分分析:")
    comp_scores = overseas_df['target_university_comprehensive_score']
    print(f"  平均综合评分: {comp_scores.mean():.1f}")
    print(f"  评分范围: {comp_scores.min():.1f} - {comp_scores.max():.1f}")
    print(f"  标准差: {comp_scores.std():.1f}")
    
    # 评分区间分布
    print(f"\n  综合评分区间分布:")
    print(f"    90-100分 (优秀): {(comp_scores >= 90).sum():,}条 ({(comp_scores >= 90).sum()/len(overseas_df)*100:.1f}%)")
    print(f"    80-89分 (良好): {((comp_scores >= 80) & (comp_scores < 90)).sum():,}条 ({((comp_scores >= 80) & (comp_scores < 90)).sum()/len(overseas_df)*100:.1f}%)")
    print(f"    70-79分 (中等): {((comp_scores >= 70) & (comp_scores < 80)).sum():,}条 ({((comp_scores >= 70) & (comp_scores < 80)).sum()/len(overseas_df)*100:.1f}%)")
    print(f"    60-69分 (及格): {((comp_scores >= 60) & (comp_scores < 70)).sum():,}条 ({((comp_scores >= 60) & (comp_scores < 70)).sum()/len(overseas_df)*100:.1f}%)")
    print(f"    60分以下 (较差): {(comp_scores < 60).sum():,}条 ({(comp_scores < 60).sum()/len(overseas_df)*100:.1f}%)")
    
    # 澳洲院校专项分析
    print(f"\n澳洲院校专项分析:")
    au_unis = overseas_df[overseas_df['target_university_country'] == 'Australia']
    if len(au_unis) > 0:
        print(f"  澳洲院校申请总数: {len(au_unis):,}条 ({len(au_unis)/len(overseas_df)*100:.1f}%)")
        
        au_tier_dist = au_unis['target_university_tier_desc'].value_counts()
        print(f"  澳洲院校层次分布:")
        for tier, count in au_tier_dist.items():
            percentage = count / len(au_unis) * 100
            print(f"    {tier}: {count:,}条 ({percentage:.1f}%)")
        
        au_top_unis = au_unis['申请院校_院校名称_标准化'].value_counts()
        print(f"\n  澳洲热门院校:")
        for i, (uni, count) in enumerate(au_top_unis.head(8).items(), 1):
            percentage = count / len(au_unis) * 100
            tier = au_unis[au_unis['申请院校_院校名称_标准化'] == uni]['target_university_tier_desc'].iloc[0]
            print(f"    {i}. {uni} ({tier}): {count:,}条 ({percentage:.1f}%)")
    
    # 英国院校专项分析
    print(f"\n英国院校专项分析:")
    uk_unis = overseas_df[overseas_df['target_university_country'] == 'UK']
    if len(uk_unis) > 0:
        print(f"  英国院校申请总数: {len(uk_unis):,}条 ({len(uk_unis)/len(overseas_df)*100:.1f}%)")
        
        uk_tier_dist = uk_unis['target_university_tier_desc'].value_counts()
        print(f"  英国院校层次分布:")
        for tier, count in uk_tier_dist.items():
            percentage = count / len(uk_unis) * 100
            print(f"    {tier}: {count:,}条 ({percentage:.1f}%)")
        
        uk_top_unis = uk_unis['申请院校_院校名称_标准化'].value_counts()
        print(f"\n  英国热门院校:")
        for i, (uni, count) in enumerate(uk_top_unis.head(5).items(), 1):
            percentage = count / len(uk_unis) * 100
            tier = uk_unis[uk_unis['申请院校_院校名称_标准化'] == uni]['target_university_tier_desc'].iloc[0]
            print(f"    {i}. {uni} ({tier}): {count:,}条 ({percentage:.1f}%)")
    
    print(f"\n" + "="*80)
    print("分析完成")
    print("="*80)

if __name__ == "__main__":
    analyze_overseas_university_features()