import re
import pandas as pd
import numpy as np

class GPAConverter:
    """GPA转换器，将不同格式的GPA统一转换为百分制"""
    
    def __init__(self):
        # 4.0制转百分制映射
        self.gpa_4_0_mapping = {
            4.0: 90, 3.9: 89, 3.8: 88, 3.7: 87, 3.6: 86, 3.5: 85,
            3.4: 84, 3.3: 83, 3.2: 82, 3.1: 81, 3.0: 80, 2.9: 79,
            2.8: 78, 2.7: 77, 2.6: 76, 2.5: 75, 2.4: 74, 2.3: 73,
            2.2: 72, 2.1: 71, 2.0: 70, 1.9: 69, 1.8: 68, 1.7: 67,
            1.6: 66, 1.5: 65, 1.0: 60, 0.0: 0
        }
        
        # 5.0制转百分制映射
        self.gpa_5_0_mapping = {
            5.0: 90, 4.8: 88, 4.6: 86, 4.4: 84, 4.2: 82, 4.0: 80,
            3.8: 78, 3.6: 76, 3.4: 74, 3.2: 72, 3.0: 70, 2.5: 65,
            2.0: 60, 1.0: 50, 0.0: 0
        }
    
    def detect_gpa_format(self, gpa_str):
        """检测GPA格式"""
        if pd.isna(gpa_str) or gpa_str == '':
            return 'missing'
        
        gpa_str = str(gpa_str).strip()
        
        # 百分制格式：80%, 85%等
        if re.match(r'^\d{1,3}\.?\d*%$', gpa_str):
            return 'percentage'
            
        # 分数格式：80/100, 3.7/4等
        if re.match(r'^\d{1,3}\.?\d*/\d{1,3}\.?\d*$', gpa_str):
            return 'fraction'
            
        # 纯数字格式
        if re.match(r'^\d{1,3}\.?\d*$', gpa_str):
            num = float(gpa_str)
            if num > 20:  # 假设已经是百分制
                return 'hundred_scale'
            elif num <= 5:  # 假设是4.0或5.0制
                if num <= 4.0:
                    return 'four_scale'
                else:
                    return 'five_scale'
            else:  # 10-20之间的数字，可能是10分制
                return 'ten_scale'
        
        return 'unknown'
    
    def convert_to_hundred(self, gpa_str):
        """将GPA转换为百分制"""
        if pd.isna(gpa_str) or gpa_str == '':
            return np.nan
            
        gpa_str = str(gpa_str).strip()
        format_type = self.detect_gpa_format(gpa_str)
        
        try:
            if format_type == 'missing':
                return np.nan
                
            elif format_type == 'percentage':
                # 去除%号并转换
                return float(gpa_str.replace('%', ''))
                
            elif format_type == 'fraction':
                # 分数格式转换
                parts = gpa_str.split('/')
                numerator = float(parts[0])
                denominator = float(parts[1])
                
                if denominator == 0:
                    return np.nan
                elif denominator == 100:
                    return numerator
                elif denominator == 4.0:
                    # 4.0制转百分制
                    return self._interpolate_gpa_4_0(numerator)
                elif denominator == 5.0:
                    # 5.0制转百分制
                    return self._interpolate_gpa_5_0(numerator)
                else:
                    # 其他分制按比例转换到百分制
                    return (numerator / denominator) * 100
                    
            elif format_type == 'hundred_scale':
                return float(gpa_str)
                
            elif format_type == 'four_scale':
                return self._interpolate_gpa_4_0(float(gpa_str))
                
            elif format_type == 'five_scale':
                return self._interpolate_gpa_5_0(float(gpa_str))
                
            elif format_type == 'ten_scale':
                # 10分制转百分制
                return float(gpa_str) * 10
                
            else:
                return np.nan
                
        except (ValueError, IndexError):
            return np.nan
    
    def _interpolate_gpa_4_0(self, gpa_value):
        """4.0制GPA插值转换"""
        if gpa_value in self.gpa_4_0_mapping:
            return self.gpa_4_0_mapping[gpa_value]
        
        # 线性插值
        keys = sorted(self.gpa_4_0_mapping.keys())
        for i in range(len(keys) - 1):
            if keys[i] <= gpa_value <= keys[i + 1]:
                # 线性插值
                x1, y1 = keys[i], self.gpa_4_0_mapping[keys[i]]
                x2, y2 = keys[i + 1], self.gpa_4_0_mapping[keys[i + 1]]
                return y1 + (y2 - y1) * (gpa_value - x1) / (x2 - x1)
        
        # 超出范围的处理
        if gpa_value > 4.0:
            return 90  # 按最高分处理
        else:
            return 0   # 按最低分处理
    
    def _interpolate_gpa_5_0(self, gpa_value):
        """5.0制GPA插值转换"""
        if gpa_value in self.gpa_5_0_mapping:
            return self.gpa_5_0_mapping[gpa_value]
        
        # 线性插值
        keys = sorted(self.gpa_5_0_mapping.keys())
        for i in range(len(keys) - 1):
            if keys[i] <= gpa_value <= keys[i + 1]:
                x1, y1 = keys[i], self.gpa_5_0_mapping[keys[i]]
                x2, y2 = keys[i + 1], self.gpa_5_0_mapping[keys[i + 1]]
                return y1 + (y2 - y1) * (gpa_value - x1) / (x2 - x1)
        
        # 超出范围的处理
        if gpa_value > 5.0:
            return 90
        else:
            return 0
    
    def batch_convert(self, gpa_series):
        """批量转换GPA Series"""
        return gpa_series.apply(self.convert_to_hundred)
    
    def analyze_gpa_formats(self, gpa_series):
        """分析GPA格式分布"""
        format_counts = {}
        for gpa in gpa_series.dropna():
            format_type = self.detect_gpa_format(gpa)
            format_counts[format_type] = format_counts.get(format_type, 0) + 1
        
        return format_counts

# 测试函数
if __name__ == "__main__":
    converter = GPAConverter()
    
    # 测试用例
    test_cases = [
        "3.77/4", "80/100", "85%", "80", "3.5", "4.2", "90", 
        "2.8/4", "4.5/5", "75%", "3.0", np.nan, ""
    ]
    
    print("GPA转换测试:")
    print("-" * 40)
    for case in test_cases:
        result = converter.convert_to_hundred(case)
        format_type = converter.detect_gpa_format(case)
        print(f"{str(case):10} -> {result:6.1f} ({format_type})")