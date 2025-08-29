import pandas as pd
import numpy as np

def check_data_integrity():
    print("检查数据文件完整性...")
    
    # 加载数据
    df = pd.read_csv('data/processed/final_feature_dataset_latest.csv')
    print(f"数据形状: {df.shape}")
    
    # 检查目标专业列
    target_col = "申请院校_专业名称"
    print(f"目标专业列: {target_col}")
    print(f"总专业数量: {df[target_col].nunique()}")
    
    # 统计申请量≥100的专业
    major_counts = df[target_col].value_counts()
    eligible_majors = major_counts[major_counts >= 100]
    print(f"申请量≥100的专业数量: {len(eligible_majors)}")
    print(f"覆盖申请量: {eligible_majors.sum()}")
    print(f"覆盖率: {eligible_majors.sum() / len(df):.1%}")
    
    # 检查特征列
    exclude_patterns = ['ID', 'id', '名称', '时间', '日期', '描述', '类型', '开始', '结束', '单位', '职位', '职责']
    feature_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            if not any(pattern in col for pattern in exclude_patterns):
                feature_cols.append(col)
    
    print(f"识别到的特征列数量: {len(feature_cols)}")
    
    # 检查数据完整性
    missing_data = df[feature_cols].isnull().sum()
    high_missing_features = missing_data[missing_data > len(df) * 0.1]  # 缺失率>10%
    print(f"高缺失率特征数量(>10%): {len(high_missing_features)}")
    
    # 显示前几个符合条件的专业
    print("\n前10个符合条件的专业:")
    for i, (major, count) in enumerate(eligible_majors.head(10).items()):
        print(f"{i+1}. {major}: {count}申请")
    
    print(f"\n数据检查完成 ✓")
    return True

if __name__ == "__main__":
    check_data_integrity()