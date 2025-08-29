import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_RAW_DIR, OFFER_DATA_FILE, COLUMNS_CONFIG

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class DataExplorer:
    def __init__(self):
        self.data_path = DATA_RAW_DIR / OFFER_DATA_FILE
        self.df = None
        
    def load_data(self):
        """加载数据"""
        try:
            self.df = pd.read_csv(self.data_path, encoding='utf-8')
            print(f"数据加载成功！数据形状: {self.df.shape}")
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def basic_info(self):
        """基本信息探索"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("=" * 50)
        print("数据基本信息")
        print("=" * 50)
        print(f"数据形状: {self.df.shape}")
        print(f"列数: {self.df.shape[1]}")
        print(f"行数: {self.df.shape[0]}")
        print("\n列名:")
        for i, col in enumerate(self.df.columns):
            print(f"{i+1:2d}. {col}")
        
        print("\n" + "=" * 50)
        print("数据类型")
        print("=" * 50)
        print(self.df.dtypes)
        
        print("\n" + "=" * 50)
        print("前5行数据预览")
        print("=" * 50)
        print(self.df.head())
        
    def missing_analysis(self):
        """缺失值分析"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n" + "=" * 50)
        print("缺失值分析")
        print("=" * 50)
        
        missing_stats = pd.DataFrame({
            '缺失数量': self.df.isnull().sum(),
            '缺失比例(%)': (self.df.isnull().sum() / len(self.df) * 100).round(2)
        })
        missing_stats = missing_stats[missing_stats['缺失数量'] > 0].sort_values('缺失比例(%)', ascending=False)
        
        if len(missing_stats) > 0:
            print("存在缺失值的字段:")
            print(missing_stats)
        else:
            print("数据中没有缺失值")
            
        return missing_stats
    
    def duplicate_analysis(self):
        """重复值分析"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n" + "=" * 50)
        print("重复值分析")
        print("=" * 50)
        
        duplicate_count = self.df.duplicated().sum()
        print(f"完全重复的行数: {duplicate_count}")
        print(f"重复比例: {duplicate_count/len(self.df)*100:.2f}%")
        
        if duplicate_count > 0:
            print("\n重复行示例:")
            print(self.df[self.df.duplicated()].head())
            
        return duplicate_count
    
    def categorical_analysis(self):
        """分类变量分析"""
        if self.df is None:
            print("请先加载数据")
            return
            
        print("\n" + "=" * 50)
        print("分类变量分析")
        print("=" * 50)
        
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            print(f"\n字段: {col}")
            print(f"唯一值数量: {self.df[col].nunique()}")
            
            if self.df[col].nunique() <= 20:  # 只显示唯一值较少的字段的详细分布
                print("值分布:")
                value_counts = self.df[col].value_counts()
                for value, count in value_counts.head(10).items():
                    percentage = count / len(self.df) * 100
                    print(f"  {value}: {count} ({percentage:.1f}%)")
                    
                if len(value_counts) > 10:
                    print(f"  ... 还有{len(value_counts)-10}个其他值")
            else:
                print("唯一值过多，显示前10个:")
                for value in self.df[col].value_counts().head(10).index:
                    count = self.df[col].value_counts()[value]
                    percentage = count / len(self.df) * 100
                    print(f"  {value}: {count} ({percentage:.1f}%)")
    
    def run_exploration(self):
        """运行完整的数据探索"""
        if not self.load_data():
            return
            
        self.basic_info()
        missing_stats = self.missing_analysis()
        duplicate_count = self.duplicate_analysis()
        self.categorical_analysis()
        
        return {
            'missing_stats': missing_stats,
            'duplicate_count': duplicate_count,
            'df': self.df
        }

if __name__ == "__main__":
    explorer = DataExplorer()
    results = explorer.run_exploration()