# 项目配置文件

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录配置
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"

# 输出目录配置
OUTPUT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_MODELS_DIR = PROJECT_ROOT / "outputs" / "models"
OUTPUT_VIZ_DIR = PROJECT_ROOT / "outputs" / "visualizations"

# 数据文件配置
OFFER_DATA_FILE = "近3年offer数据_整理表头.csv"

# 数据字段配置
COLUMNS_CONFIG = {
    "申请院校": ["申请院校_院校ID", "申请院校_专业ID", "申请院校_院校名称", "申请院校_专业名称", "申请院校_课程类型"],
    "教育经历": ["教育经历_毕业院校", "教育经历_所学专业", "教育经历_学历层次", "教育经历_就读国家", 
              "教育经历_入学时间", "教育经历_毕业时间", "教育经历_GPA成绩", "教育经历_是否有退学或开除经历"],
    "语言考试": ["语言考试_考试类型", "语言考试_考试成绩", "语言考试_考试时间"],
    "工作经历": ["工作经历_开始时间", "工作经历_结束时间", "工作经历_工作单位", "工作经历_职位名称", "工作经历_工作职责"]
}

# 模型配置
MODEL_CONFIG = {
    "random_state": 42,
    "test_size": 0.2,
    "cv_folds": 5
}