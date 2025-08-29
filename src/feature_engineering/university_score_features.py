"""
院校背景统一量化评分特征工程
实现将院校层次转换为0-100分的量化评分系统
"""

import pandas as pd
import numpy as np
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR, DATA_RAW_DIR, DATA_EXTERNAL_DIR

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UniversityScoreGenerator:
    """院校背景统一量化评分特征生成器"""
    
    def __init__(self):
        """初始化评分生成器"""
        self.china_tiers_df = None
        self.qs_rankings_df = None
        self.university_categories = None
        self._load_reference_data()
        self._init_scoring_rules()
        
    def _load_reference_data(self):
        """加载参考数据"""
        try:
            # 加载中国院校层次数据
            china_tiers_path = Path(DATA_EXTERNAL_DIR) / "china_university_tiers.csv"
            if china_tiers_path.exists():
                self.china_tiers_df = pd.read_csv(china_tiers_path)
                logger.info(f"加载中国院校层次数据：{len(self.china_tiers_df)}条记录")
            
            # 加载QS排名数据
            qs_rankings_path = Path(DATA_EXTERNAL_DIR) / "qs_university_rankings.csv"
            if qs_rankings_path.exists():
                self.qs_rankings_df = pd.read_csv(qs_rankings_path)
                logger.info(f"加载QS排名数据：{len(self.qs_rankings_df)}条记录")
                
        except Exception as e:
            logger.error(f"加载参考数据失败: {e}")
            
    def _init_scoring_rules(self):
        """初始化评分规则"""
        # 中国院校层次评分规则（根据CLAUDE.md定义）
        self.china_tier_scores = {
            1: (85, 100),  # C1级（985院校）：85-100分
            2: (75, 85),   # C2级（211院校）：75-85分
            2.5: (75, 90), # C2.5级（特色顶尖院校）：75-90分
            3: (65, 75),   # C3级（双一流/省重点）：65-75分
            4: (55, 65),   # C4级（普通本科）：55-65分
            5: (40, 55),   # C5级（专科）：40-55分
        }
        
        # QS排名评分规则
        self.qs_score_ranges = [
            (1, 50, 90, 100),      # Top 50: 90-100分
            (51, 100, 80, 90),     # 51-100: 80-90分
            (101, 200, 70, 80),    # 101-200: 70-80分
            (201, 300, 60, 70),    # 201-300: 60-70分
            (301, 500, 50, 60),    # 301-500: 50-60分
            (501, 1000, 40, 50),   # 501-1000: 40-50分
            (1001, 9999, 30, 40)   # 1000+: 30-40分
        ]
        
        # 院校类别映射（按优先级排序：专业类别优先）
        self.university_categories_mapping = {
            "艺术": ["艺术", "美术", "音乐", "戏剧", "影视", "art", "music", "drama", "film", "design", "creative"],
            "体育": ["体育", "运动", "physical", "sport", "体院"],
            "专业": ["理工", "财经", "医科", "师范", "农业", "政法", "技术", "科技", "工业", "医学", "师大", "财大", "农大"],
            "综合": ["大学", "学院", "university", "college"]
        }
        
    def calculate_china_university_score(self, tier: Union[int, float], 
                                       is_985: bool = False, 
                                       is_211: bool = False, 
                                       is_double_first_class: bool = False) -> float:
        """
        计算中国院校评分
        
        Args:
            tier: 院校层次等级
            is_985: 是否985院校
            is_211: 是否211院校
            is_double_first_class: 是否双一流院校
            
        Returns:
            float: 院校评分 (0-100)
        """
        if pd.isna(tier):
            return 50.0  # 默认分数
            
        # 获取基础分数范围
        if tier in self.china_tier_scores:
            min_score, max_score = self.china_tier_scores[tier]
        else:
            # 如果tier不在预定义范围内，使用最接近的tier
            closest_tier = min(self.china_tier_scores.keys(), key=lambda x: abs(x - tier))
            min_score, max_score = self.china_tier_scores[closest_tier]
        
        # 基础分数取范围中位数
        base_score = (min_score + max_score) / 2
        
        # 根据特殊标识调整分数
        adjustment = 0
        if is_985:
            adjustment += 5  # 985院校额外加分
        elif is_211:
            adjustment += 3  # 211院校额外加分
        elif is_double_first_class:
            adjustment += 2  # 双一流院校额外加分
            
        final_score = min(100, base_score + adjustment)
        return round(final_score, 2)
    
    def calculate_overseas_university_score(self, qs_rank: Union[int, float]) -> float:
        """
        计算海外院校评分（基于QS排名）
        
        Args:
            qs_rank: QS排名
            
        Returns:
            float: 院校评分 (0-100)
        """
        if pd.isna(qs_rank) or qs_rank == 999 or qs_rank > 9999:
            return 45.0  # 无排名或排名过低的院校默认分数
            
        qs_rank = int(qs_rank)
        
        # 根据QS排名确定分数范围
        for min_rank, max_rank, min_score, max_score in self.qs_score_ranges:
            if min_rank <= qs_rank <= max_rank:
                # 在范围内进行线性插值
                rank_ratio = (qs_rank - min_rank) / (max_rank - min_rank) if max_rank > min_rank else 0
                score = max_score - rank_ratio * (max_score - min_score)
                return round(score, 2)
        
        # 如果排名超出范围，返回最低分
        return 30.0
    
    def classify_university_category(self, university_name: str) -> str:
        """
        分类院校类别
        
        Args:
            university_name: 院校名称
            
        Returns:
            str: 院校类别（综合/艺术/体育/专业）
        """
        if pd.isna(university_name):
            return "综合"
            
        university_name = str(university_name).lower()
        
        # 检查各个类别的关键词
        for category, keywords in self.university_categories_mapping.items():
            for keyword in keywords:
                if keyword.lower() in university_name:
                    return category
                    
        return "综合"  # 默认为综合类
    
    def generate_university_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为数据集生成院校评分特征
        
        Args:
            df: 输入数据集
            
        Returns:
            pd.DataFrame: 包含院校评分特征的数据集
        """
        logger.info("开始生成院校评分特征...")
        result_df = df.copy()
        
        # 生成生源院校评分
        if 'source_university_tier' in df.columns:
            logger.info("计算生源院校评分...")
            result_df['source_university_score_unified'] = df.apply(
                lambda row: self.calculate_china_university_score(
                    tier=row.get('source_university_tier'),
                    is_985=row.get('source_is_985', False),
                    is_211=row.get('source_is_211', False),
                    is_double_first_class=row.get('source_is_double_first_class', False)
                ), axis=1
            )
        else:
            logger.warning("未找到source_university_tier列，使用默认评分")
            result_df['source_university_score_unified'] = 60.0
            
        # 生成目标院校评分
        target_scores = []
        logger.info("计算目标院校评分...")
        
        for idx, row in df.iterrows():
            # 优先使用QS排名计算海外院校评分
            if 'target_university_qs_rank' in df.columns and pd.notna(row.get('target_university_qs_rank')):
                qs_rank = row['target_university_qs_rank']
                if qs_rank != 999:  # 999表示无排名
                    score = self.calculate_overseas_university_score(qs_rank)
                    target_scores.append(score)
                    continue
            
            # 如果没有QS排名，使用中国院校层次计算
            if 'target_university_tier' in df.columns:
                tier = row.get('target_university_tier')
                score = self.calculate_china_university_score(tier)
                target_scores.append(score)
            else:
                target_scores.append(70.0)  # 默认分数
                
        result_df['target_university_score_unified'] = target_scores
        
        # 生成院校类别特征
        logger.info("生成院校类别特征...")
        if '教育经历_毕业院校' in df.columns:
            result_df['source_university_category'] = df['教育经历_毕业院校'].apply(
                self.classify_university_category
            )
        else:
            result_df['source_university_category'] = "综合"
            
        if '申请院校_院校名称' in df.columns:
            result_df['target_university_category'] = df['申请院校_院校名称'].apply(
                self.classify_university_category
            )
        else:
            result_df['target_university_category'] = "综合"
            
        # 计算院校评分差距
        result_df['university_score_gap_unified'] = (
            result_df['target_university_score_unified'] - 
            result_df['source_university_score_unified']
        )
        
        # 计算相对提升比例
        result_df['university_score_improvement_ratio'] = (
            result_df['university_score_gap_unified'] / 
            result_df['source_university_score_unified']
        ).fillna(0)
        
        logger.info("院校评分特征生成完成")
        return result_df
    
    def generate_score_statistics(self, df: pd.DataFrame) -> Dict:
        """
        生成评分统计分析
        
        Args:
            df: 包含评分特征的数据集
            
        Returns:
            Dict: 统计分析结果
        """
        logger.info("生成评分统计分析...")
        
        stats = {}
        
        # 生源院校评分统计
        if 'source_university_score_unified' in df.columns:
            source_scores = df['source_university_score_unified']
            stats['source_university_scores'] = {
                'mean': float(source_scores.mean()),
                'median': float(source_scores.median()),
                'std': float(source_scores.std()),
                'min': float(source_scores.min()),
                'max': float(source_scores.max()),
                'distribution': source_scores.value_counts().to_dict()
            }
        
        # 目标院校评分统计
        if 'target_university_score_unified' in df.columns:
            target_scores = df['target_university_score_unified']
            stats['target_university_scores'] = {
                'mean': float(target_scores.mean()),
                'median': float(target_scores.median()),
                'std': float(target_scores.std()),
                'min': float(target_scores.min()),
                'max': float(target_scores.max()),
                'distribution': target_scores.value_counts().to_dict()
            }
        
        # 评分差距统计
        if 'university_score_gap_unified' in df.columns:
            score_gaps = df['university_score_gap_unified']
            stats['score_gaps'] = {
                'mean': float(score_gaps.mean()),
                'median': float(score_gaps.median()),
                'std': float(score_gaps.std()),
                'min': float(score_gaps.min()),
                'max': float(score_gaps.max()),
                'positive_ratio': float((score_gaps > 0).mean()),
                'negative_ratio': float((score_gaps < 0).mean())
            }
        
        # 院校类别统计
        if 'source_university_category' in df.columns:
            stats['source_categories'] = df['source_university_category'].value_counts().to_dict()
            
        if 'target_university_category' in df.columns:
            stats['target_categories'] = df['target_university_category'].value_counts().to_dict()
            
        # 评分区间分布
        if 'source_university_score_unified' in df.columns:
            source_bins = pd.cut(df['source_university_score_unified'], 
                               bins=[0, 60, 70, 80, 90, 100], 
                               labels=['低(0-60)', '中低(60-70)', '中(70-80)', '中高(80-90)', '高(90-100)'])
            stats['source_score_ranges'] = source_bins.value_counts().to_dict()
            
        if 'target_university_score_unified' in df.columns:
            target_bins = pd.cut(df['target_university_score_unified'], 
                               bins=[0, 60, 70, 80, 90, 100], 
                               labels=['低(0-60)', '中低(60-70)', '中(70-80)', '中高(80-90)', '高(90-100)'])
            stats['target_score_ranges'] = target_bins.value_counts().to_dict()
        
        logger.info("统计分析生成完成")
        return stats
    
    def save_statistics_report(self, stats: Dict, output_path: str):
        """
        保存统计分析报告
        
        Args:
            stats: 统计分析结果
            output_path: 输出文件路径
        """
        logger.info(f"保存统计分析报告到: {output_path}")
        
        report_lines = []
        report_lines.append("# 院校背景统一量化评分特征统计分析报告\n")
        report_lines.append(f"生成时间: {pd.Timestamp.now()}\n")
        
        # 生源院校评分统计
        if 'source_university_scores' in stats:
            source_stats = stats['source_university_scores']
            report_lines.append("## 生源院校评分统计\n")
            report_lines.append(f"- 平均分: {source_stats['mean']:.2f}")
            report_lines.append(f"- 中位数: {source_stats['median']:.2f}")
            report_lines.append(f"- 标准差: {source_stats['std']:.2f}")
            report_lines.append(f"- 最低分: {source_stats['min']:.2f}")
            report_lines.append(f"- 最高分: {source_stats['max']:.2f}\n")
        
        # 目标院校评分统计
        if 'target_university_scores' in stats:
            target_stats = stats['target_university_scores']
            report_lines.append("## 目标院校评分统计\n")
            report_lines.append(f"- 平均分: {target_stats['mean']:.2f}")
            report_lines.append(f"- 中位数: {target_stats['median']:.2f}")
            report_lines.append(f"- 标准差: {target_stats['std']:.2f}")
            report_lines.append(f"- 最低分: {target_stats['min']:.2f}")
            report_lines.append(f"- 最高分: {target_stats['max']:.2f}\n")
        
        # 评分差距统计
        if 'score_gaps' in stats:
            gap_stats = stats['score_gaps']
            report_lines.append("## 院校评分差距统计\n")
            report_lines.append(f"- 平均差距: {gap_stats['mean']:.2f}")
            report_lines.append(f"- 中位数差距: {gap_stats['median']:.2f}")
            report_lines.append(f"- 标准差: {gap_stats['std']:.2f}")
            report_lines.append(f"- 最大提升: {gap_stats['max']:.2f}")
            report_lines.append(f"- 最大下降: {gap_stats['min']:.2f}")
            report_lines.append(f"- 正向提升比例: {gap_stats['positive_ratio']:.2%}")
            report_lines.append(f"- 负向下降比例: {gap_stats['negative_ratio']:.2%}\n")
        
        # 院校类别分布
        if 'source_categories' in stats:
            report_lines.append("## 生源院校类别分布\n")
            for category, count in stats['source_categories'].items():
                report_lines.append(f"- {category}: {count}所")
            report_lines.append("")
        
        if 'target_categories' in stats:
            report_lines.append("## 目标院校类别分布\n")
            for category, count in stats['target_categories'].items():
                report_lines.append(f"- {category}: {count}所")
            report_lines.append("")
        
        # 评分区间分布
        if 'source_score_ranges' in stats:
            report_lines.append("## 生源院校评分区间分布\n")
            for range_name, count in stats['source_score_ranges'].items():
                report_lines.append(f"- {range_name}: {count}个")
            report_lines.append("")
        
        if 'target_score_ranges' in stats:
            report_lines.append("## 目标院校评分区间分布\n")
            for range_name, count in stats['target_score_ranges'].items():
                report_lines.append(f"- {range_name}: {count}个")
            report_lines.append("")
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info("统计分析报告保存完成")


def main():
    """主函数 - 演示评分特征生成"""
    # 初始化评分生成器
    score_generator = UniversityScoreGenerator()
    
    # 加载现有数据
    input_file = Path(DATA_PROCESSED_DIR) / "cleaned_offer_data_with_comprehensive_university_features.csv"
    if not input_file.exists():
        logger.error(f"输入文件不存在: {input_file}")
        return
    
    logger.info(f"加载数据文件: {input_file}")
    df = pd.read_csv(input_file)
    
    # 生成评分特征
    df_with_scores = score_generator.generate_university_scores(df)
    
    # 保存结果
    output_file = Path(DATA_PROCESSED_DIR) / "cleaned_offer_data_with_unified_scores.csv"
    df_with_scores.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"保存结果文件: {output_file}")
    
    # 生成统计分析
    stats = score_generator.generate_score_statistics(df_with_scores)
    
    # 保存统计报告
    report_file = Path(DATA_PROCESSED_DIR).parent / "outputs" / "reports" / "university_score_analysis_report.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    score_generator.save_statistics_report(stats, str(report_file))
    
    logger.info("院校评分特征生成完成！")


if __name__ == "__main__":
    main()