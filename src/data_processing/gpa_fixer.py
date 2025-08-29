import pandas as pd
import numpy as np
import re
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_PROCESSED_DIR
from src.data_processing.gpa_converter import GPAConverter

class GPAFixer:
    """GPA异常值修复器"""
    
    def __init__(self):
        self.df = None
        self.gpa_converter = GPAConverter()
        
    def load_data(self):
        """加载清洗后的数据"""
        data_path = DATA_PROCESSED_DIR / 'cleaned_offer_data.csv'
        try:
            self.df = pd.read_csv(data_path, encoding='utf-8-sig')
            print(f"数据加载成功: {self.df.shape}")
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def analyze_gpa_anomalies(self):
        """分析GPA异常值"""
        if self.df is None:
            return
            
        gpa_original = '教育经历_GPA成绩'
        gpa_converted = '教育经历_GPA成绩_百分制'
        
        print("="*60)
        print("GPA异常值分析")
        print("="*60)
        
        # 分析转换后的异常值
        converted_gpa = self.df[gpa_converted].dropna()
        print(f"转换后GPA统计:")
        print(f"  记录数: {len(converted_gpa)}")
        print(f"  平均值: {converted_gpa.mean():.2f}")
        print(f"  中位数: {converted_gpa.median():.2f}")
        print(f"  最小值: {converted_gpa.min():.2f}")
        print(f"  最大值: {converted_gpa.max():.2f}")
        print(f"  95分位数: {converted_gpa.quantile(0.95):.2f}")
        print(f"  99分位数: {converted_gpa.quantile(0.99):.2f}")
        
        # 找出异常值
        anomalies = self.df[self.df[gpa_converted] > 100]
        print(f"\n>100的异常值数量: {len(anomalies)}")
        
        if len(anomalies) > 0:
            print("\n异常值样本:")
            for idx, row in anomalies.head(20).iterrows():
                original = row[gpa_original]
                converted = row[gpa_converted]
                print(f"  原始: '{original}' -> 转换: {converted}")
        
        # 分析原始GPA格式分布
        print(f"\n原始GPA格式分析:")
        format_counts = {}
        for gpa in self.df[gpa_original].dropna():
            format_type = self.gpa_converter.detect_gpa_format(gpa)
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        for format_type, count in sorted(format_counts.items()):
            print(f"  {format_type}: {count}条")
            
        return anomalies
    
    def fix_gpa_conversion_logic(self):
        """修复GPA转换逻辑"""
        print("\n" + "="*60)
        print("修复GPA转换逻辑")
        print("="*60)
        
        gpa_original = '教育经历_GPA成绩'
        
        # 重新转换所有GPA
        print("重新转换GPA...")
        
        fixed_gpa = []
        conversion_stats = {
            'success': 0,
            'failed': 0,
            'anomalies_fixed': 0
        }
        
        for idx, original_gpa in enumerate(self.df[gpa_original]):
            if pd.isna(original_gpa):
                fixed_gpa.append(np.nan)
                continue
                
            # 使用改进的转换逻辑
            converted = self._improved_gpa_conversion(original_gpa)
            fixed_gpa.append(converted)
            
            # 统计
            if pd.isna(converted):
                conversion_stats['failed'] += 1
            elif converted > 100:
                conversion_stats['anomalies_fixed'] += 1
                # 对于仍然异常的值，尝试进一步修复
                converted = self._handle_extreme_anomaly(original_gpa)
                fixed_gpa[-1] = converted
            else:
                conversion_stats['success'] += 1
        
        # 更新数据
        self.df['教育经历_GPA成绩_百分制_修复'] = fixed_gpa
        
        # 显示修复结果
        fixed_gpa_series = pd.Series(fixed_gpa).dropna()
        print(f"\n修复后GPA统计:")
        print(f"  成功转换: {conversion_stats['success']}")
        print(f"  转换失败: {conversion_stats['failed']}")
        print(f"  异常值修复: {conversion_stats['anomalies_fixed']}")
        print(f"  平均值: {fixed_gpa_series.mean():.2f}")
        print(f"  中位数: {fixed_gpa_series.median():.2f}")
        print(f"  最小值: {fixed_gpa_series.min():.2f}")
        print(f"  最大值: {fixed_gpa_series.max():.2f}")
        
        return conversion_stats
    
    def _improved_gpa_conversion(self, gpa_str):
        """改进的GPA转换逻辑"""
        if pd.isna(gpa_str) or gpa_str == '':
            return np.nan
            
        gpa_str = str(gpa_str).strip()
        
        # 特殊情况处理
        if gpa_str in ['', 'N/A', 'n/a', 'NULL', 'null']:
            return np.nan
            
        try:
            # 处理百分制格式
            if re.match(r'^\d{1,3}\.?\d*%$', gpa_str):
                value = float(gpa_str.replace('%', ''))
                return min(value, 100)  # 限制最大值为100
            
            # 处理分数格式
            if '/' in gpa_str:
                parts = gpa_str.split('/')
                if len(parts) == 2:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    
                    if denominator == 0:
                        return np.nan
                    elif denominator == 100:
                        return min(numerator, 100)
                    elif denominator <= 4.0:  # 4.0制或更小
                        if numerator <= denominator:
                            return self.gpa_converter._interpolate_gpa_4_0(numerator)
                        else:
                            return np.nan  # 分子大于分母，异常
                    elif denominator <= 5.0:  # 5.0制
                        if numerator <= denominator:
                            return self.gpa_converter._interpolate_gpa_5_0(numerator)
                        else:
                            return np.nan
                    else:
                        # 其他分制，按比例转换但限制在合理范围内
                        ratio = numerator / denominator
                        if ratio <= 1.0:
                            return min(ratio * 100, 100)
                        else:
                            return np.nan
            
            # 处理纯数字格式
            if re.match(r'^\d{1,3}\.?\d*$', gpa_str):
                value = float(gpa_str)
                
                if value > 100:
                    # 可能是异常值，尝试判断是否是其他进制
                    if value > 1000:
                        return np.nan  # 过大的值直接标记为缺失
                    else:
                        # 可能是10分制等
                        return min(value, 100)
                elif value > 20:
                    # 假设是百分制
                    return value
                elif value <= 5:
                    # 假设是4.0或5.0制
                    if value <= 4.0:
                        return self.gpa_converter._interpolate_gpa_4_0(value)
                    else:
                        return self.gpa_converter._interpolate_gpa_5_0(value)
                else:
                    # 10-20之间，可能是10分制
                    return value * 10 if value <= 10 else value
            
            return np.nan
            
        except (ValueError, ZeroDivisionError):
            return np.nan
    
    def _handle_extreme_anomaly(self, gpa_str):
        """处理极端异常值"""
        try:
            # 对于极端异常的情况，尝试从字符串中提取合理的数值
            numbers = re.findall(r'\d+\.?\d*', str(gpa_str))
            if numbers:
                # 取第一个数字，如果在合理范围内则使用
                first_num = float(numbers[0])
                if first_num <= 100:
                    return first_num
                elif first_num <= 1000:
                    # 可能是缺少小数点
                    return first_num / 10
            return np.nan
        except:
            return np.nan
    
    def validate_fixed_gpa(self):
        """验证修复结果"""
        print("\n" + "="*60)
        print("GPA修复结果验证")
        print("="*60)
        
        original_col = '教育经历_GPA成绩_百分制'
        fixed_col = '教育经历_GPA成绩_百分制_修复'
        
        # 比较修复前后
        original_valid = self.df[original_col].dropna()
        fixed_valid = self.df[fixed_col].dropna()
        
        print(f"修复前有效记录: {len(original_valid)}")
        print(f"修复后有效记录: {len(fixed_valid)}")
        
        # 异常值比较
        original_anomalies = (original_valid > 100).sum()
        fixed_anomalies = (fixed_valid > 100).sum()
        
        print(f"修复前异常值(>100): {original_anomalies}")
        print(f"修复后异常值(>100): {fixed_anomalies}")
        
        # 分布对比
        print(f"\n修复后GPA分布:")
        ranges = [(0, 60), (60, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 100), (100, float('inf'))]
        for low, high in ranges:
            count = ((fixed_valid >= low) & (fixed_valid < high)).sum()
            percentage = count / len(fixed_valid) * 100
            range_name = f"{low}-{high}" if high != float('inf') else f"{low}+"
            print(f"  {range_name}: {count} ({percentage:.1f}%)")
    
    def save_fixed_data(self):
        """保存修复后的数据"""
        output_path = DATA_PROCESSED_DIR / 'cleaned_offer_data_gpa_fixed.csv'
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n修复后数据已保存: {output_path}")
        return output_path
    
    def run_gpa_fix(self):
        """执行完整的GPA修复流程"""
        if not self.load_data():
            return None
            
        # 分析异常值
        anomalies = self.analyze_gpa_anomalies()
        
        # 修复转换逻辑
        stats = self.fix_gpa_conversion_logic()
        
        # 验证结果
        self.validate_fixed_gpa()
        
        # 保存数据
        output_path = self.save_fixed_data()
        
        return output_path, stats

if __name__ == "__main__":
    fixer = GPAFixer()
    result = fixer.run_gpa_fix()