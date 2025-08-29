import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.config import DATA_RAW_DIR

# 读取中国院校文件
def preview_china_universities():
    file_path = DATA_RAW_DIR / '中国院校 校对.xlsx'
    
    try:
        # 尝试读取Excel文件
        df = pd.read_excel(file_path)
        print(f"中国院校文件形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        print("\n前10行数据:")
        print(df.head(10))
        
        # 检查是否有层次信息
        for col in df.columns:
            if '985' in col or '211' in col or '层次' in col or '等级' in col:
                print(f"\n{col}字段分布:")
                print(df[col].value_counts())
                
        return df
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

if __name__ == "__main__":
    df = preview_china_universities()