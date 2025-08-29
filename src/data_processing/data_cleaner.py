import pandas as pd
import numpy as np
import re
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, OFFER_DATA_FILE
from src.data_processing.gpa_converter import GPAConverter

class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        self.gpa_converter = GPAConverter()
        self.df = None
        self.cleaning_stats = {}
        
    def load_data(self):
        """加载原始数据"""
        data_path = DATA_RAW_DIR / OFFER_DATA_FILE
        try:
            self.df = pd.read_csv(data_path, encoding='utf-8')
            print(f"原始数据加载成功: {self.df.shape}")
            self.cleaning_stats['original_shape'] = self.df.shape
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def remove_duplicates(self):
        """去除重复数据，保留第一条"""
        if self.df is None:
            return
            
        original_count = len(self.df)
        self.df = self.df.drop_duplicates(keep='first')
        removed_count = original_count - len(self.df)
        
        print(f"去除重复数据: 删除{removed_count}行，剩余{len(self.df)}行")
        self.cleaning_stats['duplicates_removed'] = removed_count
        self.cleaning_stats['after_dedup_shape'] = self.df.shape
    
    def handle_missing_education(self):
        """处理教育背景缺失的记录"""
        if self.df is None:
            return
            
        # 定义教育背景关键字段
        edu_cols = ['教育经历_毕业院校', '教育经历_所学专业', '教育经历_学历层次']
        
        original_count = len(self.df)
        
        # 删除教育背景关键信息缺失的记录
        mask = self.df[edu_cols].isnull().any(axis=1)
        removed_count = mask.sum()
        self.df = self.df[~mask]
        
        print(f"删除教育背景缺失记录: 删除{removed_count}行，剩余{len(self.df)}行")
        self.cleaning_stats['education_missing_removed'] = removed_count
        self.cleaning_stats['after_edu_filter_shape'] = self.df.shape
    
    def handle_missing_work_language(self):
        """处理工作经历和语言成绩缺失"""
        if self.df is None:
            return
            
        # 工作经历缺失标记为"无工作经验"
        work_cols = ['工作经历_开始时间', '工作经历_结束时间', '工作经历_工作单位', '工作经历_职位名称']
        work_missing_mask = self.df[work_cols].isnull().all(axis=1)
        
        for col in work_cols:
            self.df.loc[work_missing_mask, col] = '无工作经验'
        
        # 语言成绩缺失标记为"无语言成绩"
        lang_cols = ['语言考试_考试类型', '语言考试_考试成绩', '语言考试_考试时间']
        lang_missing_mask = self.df[lang_cols].isnull().all(axis=1)
        
        for col in lang_cols:
            self.df.loc[lang_missing_mask, col] = '无语言成绩'
            
        work_filled = work_missing_mask.sum()
        lang_filled = lang_missing_mask.sum()
        
        print(f"工作经历缺失填充: {work_filled}条记录")
        print(f"语言成绩缺失填充: {lang_filled}条记录")
        
        self.cleaning_stats['work_missing_filled'] = work_filled
        self.cleaning_stats['language_missing_filled'] = lang_filled
    
    def clean_gpa(self):
        """清洗和标准化GPA成绩"""
        if self.df is None:
            return
            
        gpa_col = '教育经历_GPA成绩'
        
        # 分析原始GPA格式分布
        print("\n原始GPA格式分析:")
        format_analysis = self.gpa_converter.analyze_gpa_formats(self.df[gpa_col])
        for format_type, count in format_analysis.items():
            print(f"  {format_type}: {count}条")
        
        # 转换GPA为百分制
        original_gpa = self.df[gpa_col].copy()
        self.df[gpa_col + '_百分制'] = self.gpa_converter.batch_convert(self.df[gpa_col])
        
        # 统计转换结果
        successful_conversions = self.df[gpa_col + '_百分制'].notna().sum()
        failed_conversions = self.df[gpa_col + '_百分制'].isna().sum()
        
        print(f"\nGPA转换结果:")
        print(f"  成功转换: {successful_conversions}条")
        print(f"  转换失败: {failed_conversions}条")
        
        self.cleaning_stats['gpa_conversions'] = {
            'successful': successful_conversions,
            'failed': failed_conversions,
            'format_analysis': format_analysis
        }
    
    def clean_dates(self):
        """清洗日期字段"""
        if self.df is None:
            return
            
        date_cols = [
            '教育经历_入学时间', '教育经历_毕业时间',
            '语言考试_考试时间', '工作经历_开始时间', '工作经历_结束时间'
        ]
        
        cleaned_dates = {}
        
        for col in date_cols:
            if col in self.df.columns:
                original_count = self.df[col].notna().sum()
                
                # 处理异常日期（如2999年）
                self.df.loc[self.df[col].str.contains('2999', na=False), col] = np.nan
                
                # 标准化日期格式
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                
                cleaned_count = self.df[col].notna().sum()
                invalid_count = original_count - cleaned_count
                
                cleaned_dates[col] = {
                    'original': original_count,
                    'cleaned': cleaned_count,
                    'invalid': invalid_count
                }
                
                if invalid_count > 0:
                    print(f"{col}: 发现{invalid_count}个无效日期")
        
        self.cleaning_stats['date_cleaning'] = cleaned_dates
    
    def standardize_categorical(self):
        """标准化分类变量"""
        if self.df is None:
            return
            
        # 标准化院校名称（去除前后空格，统一大小写）
        self.df['申请院校_院校名称'] = self.df['申请院校_院校名称'].str.strip()
        
        # 标准化学历层次
        degree_mapping = {
            '本科': '本科', 'Bachelor': '本科', 'undergraduate': '本科', 'Undergraduate': '本科',
            '硕士': '硕士', 'Master': '硕士', 'master': '硕士', 'Master(Coursework)': '硕士',
            '博士': '博士', 'PhD': '博士', 'Doctorate': '博士'
        }
        
        self.df['教育经历_学历层次_标准化'] = self.df['教育经历_学历层次'].map(degree_mapping).fillna(self.df['教育经历_学历层次'])
        
        print("分类变量标准化完成")
        
        # 统计标准化后的分布
        degree_dist = self.df['教育经历_学历层次_标准化'].value_counts()
        print("标准化后学历层次分布:")
        for degree, count in degree_dist.head(10).items():
            print(f"  {degree}: {count}条")
    
    def generate_cleaning_report(self):
        """生成清洗报告"""
        if self.df is None:
            return
            
        print("\n" + "="*60)
        print("数据清洗报告")
        print("="*60)
        
        print(f"原始数据: {self.cleaning_stats['original_shape']}")
        print(f"去重后: {self.cleaning_stats.get('after_dedup_shape', 'N/A')}")
        print(f"删除教育缺失后: {self.cleaning_stats.get('after_edu_filter_shape', 'N/A')}")
        print(f"最终数据: {self.df.shape}")
        
        print(f"\n数据保留率: {len(self.df) / self.cleaning_stats['original_shape'][0] * 100:.1f}%")
        
        # 生成详细统计
        print("\n字段完整性统计:")
        completeness = (1 - self.df.isnull().sum() / len(self.df)) * 100
        for col in self.df.columns:
            print(f"  {col}: {completeness[col]:.1f}%")
    
    def save_cleaned_data(self, filename='cleaned_offer_data.csv'):
        """保存清洗后的数据"""
        if self.df is None:
            return
            
        # 确保输出目录存在
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        output_path = DATA_PROCESSED_DIR / filename
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"清洗后数据已保存至: {output_path}")
        
        return output_path
    
    def run_full_cleaning(self):
        """执行完整的数据清洗流程"""
        print("开始数据清洗流程...")
        print("="*50)
        
        # 1. 加载数据
        if not self.load_data():
            return None
        
        # 2. 去重
        self.remove_duplicates()
        
        # 3. 处理教育背景缺失
        self.handle_missing_education()
        
        # 4. 处理工作和语言缺失
        self.handle_missing_work_language()
        
        # 5. 清洗GPA
        self.clean_gpa()
        
        # 6. 清洗日期
        self.clean_dates()
        
        # 7. 标准化分类变量
        self.standardize_categorical()
        
        # 8. 生成报告
        self.generate_cleaning_report()
        
        # 9. 保存数据
        output_path = self.save_cleaned_data()
        
        return output_path

if __name__ == "__main__":
    cleaner = DataCleaner()
    output_path = cleaner.run_full_cleaning()