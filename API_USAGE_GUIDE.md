# 学生专业匹配系统 API 使用指南

## 概述

本系统提供生产级API接口，接受原始学生信息，自动进行特征工程转换和专业匹配计算。用户无需进行复杂的特征预处理，直接输入学生的基本信息即可获得匹配结果。

## API 服务启动

### 1. 环境准备

```bash
# 激活虚拟环境
cd "E:\小希\python脚本\定校数据支撑方案"
.\venv\Scripts\activate

# 安装依赖包
pip install flask flask-cors requests
```

### 2. 启动服务

```bash
# 启动生产级API服务器
python production_api_server.py
```

服务将在以下地址启动：
- 本地访问: http://localhost:5000
- 网络访问: http://0.0.0.0:5000

## API 接口说明

### 基础 URL

```
http://localhost:5000/api
```

### 1. 系统状态查询

**端点**: `GET /status`

**说明**: 查询系统运行状态和基本信息

**响应示例**:
```json
{
  "status": "运行中",
  "initialization_time": 2.53,
  "total_majors": 50,
  "avg_confidence": 0.881,
  "api_version": "v2.0"
}
```

### 2. 获取支持的专业列表

**端点**: `GET /majors`

**说明**: 获取系统支持的所有专业名称

**响应示例**:
```json
{
  "success": true,
  "majors": [
    "master of commerce",
    "Master of Laws", 
    "Master of Computer Science",
    "..."
  ],
  "total_count": 50
}
```

### 3. 学生专业匹配

**端点**: `POST /match/student`

**说明**: 计算学生与指定专业的匹配度

**请求格式**:
```json
{
  "student_info": {
    "university": "北京大学",
    "gpa": 3.7,
    "current_major": "计算机科学",
    "target_major": "Master of Computer Science",
    "ielts_score": 7.0,
    "work_experience_years": 1,
    "work_field": "Technology"
  },
  "target_major": "Master of Computer Science"
}
```

**必需字段**:
- `university`: 学生当前就读院校名称
- `gpa`: 学生GPA成绩 (0-4.0制)
- `current_major`: 学生当前专业
- `target_major`: 目标申请专业

**可选字段**:
- `ielts_score`: 雅思成绩
- `toefl_score`: 托福成绩
- `pte_score`: PTE成绩
- `duolingo_score`: 多邻国成绩
- `work_experience_years`: 工作经验年数
- `work_field`: 工作领域
- `target_university`: 目标院校

**响应示例**:
```json
{
  "success": true,
  "major": "Master of Computer Science",
  "match_score": 69,
  "match_level": "中等匹配",
  "path_confidence": 0.559,
  "matched_path": "计算机科学 → 计算机硕士",
  "recommendations": [
    "建议提升语言成绩到7.5分以上",
    "相关工作经验有助于提高匹配度"
  ]
}
```

### 4. 最佳专业推荐

**端点**: `POST /recommend/student`

**说明**: 根据学生信息推荐最适合的专业

**请求格式**:
```json
{
  "student_info": {
    "university": "北京大学",
    "gpa": 3.7,
    "current_major": "计算机科学",
    "ielts_score": 7.0,
    "work_experience_years": 1,
    "work_field": "Technology"
  },
  "top_n": 5
}
```

**响应示例**:
```json
{
  "success": true,
  "best_matches": [
    {
      "major": "Bachelor of Business",
      "score": 91,
      "level": "高度匹配",
      "confidence": 0.92
    },
    {
      "major": "Bachelor of Commerce", 
      "score": 89,
      "level": "高度匹配",
      "confidence": 0.88
    },
    {
      "major": "Bachelor of Arts",
      "score": 84,
      "level": "较好匹配", 
      "confidence": 0.85
    }
  ],
  "total_evaluated": 50
}
```

## 使用示例

### Python 示例

```python
import requests
import json

# API基础URL
base_url = "http://localhost:5000/api"

# 学生信息
student_data = {
    "university": "清华大学",
    "gpa": 3.8,
    "current_major": "电子工程",
    "target_major": "Master of Engineering",
    "ielts_score": 7.5,
    "work_experience_years": 2,
    "work_field": "Technology"
}

# 1. 专业匹配
match_response = requests.post(
    f"{base_url}/match/student",
    json={
        "student_info": student_data,
        "target_major": "Master of Engineering"
    }
)
match_result = match_response.json()
print(f"匹配结果: {match_result['match_score']}分")

# 2. 专业推荐
recommend_response = requests.post(
    f"{base_url}/recommend/student",
    json={
        "student_info": student_data,
        "top_n": 10
    }
)
recommend_result = recommend_response.json()
print("推荐专业:")
for match in recommend_result['best_matches'][:5]:
    print(f"- {match['major']}: {match['score']}分")
```

### JavaScript/Node.js 示例

```javascript
const axios = require('axios');

const baseUrl = 'http://localhost:5000/api';

const studentData = {
    university: "北京大学",
    gpa: 3.7,
    current_major: "计算机科学",
    ielts_score: 7.0,
    work_experience_years: 1,
    work_field: "Technology"
};

// 获取专业推荐
async function getRecommendations() {
    try {
        const response = await axios.post(`${baseUrl}/recommend/student`, {
            student_info: studentData,
            top_n: 5
        });
        
        console.log('推荐专业:');
        response.data.best_matches.forEach((match, index) => {
            console.log(`${index + 1}. ${match.major}: ${match.score}分`);
        });
    } catch (error) {
        console.error('请求失败:', error.response?.data || error.message);
    }
}

getRecommendations();
```

### cURL 示例

```bash
# 专业匹配
curl -X POST http://localhost:5000/api/match/student \
  -H "Content-Type: application/json" \
  -d '{
    "student_info": {
      "university": "北京大学",
      "gpa": 3.7,
      "current_major": "计算机科学",
      "target_major": "Master of Computer Science",
      "ielts_score": 7.0
    },
    "target_major": "Master of Computer Science"
  }'

# 专业推荐
curl -X POST http://localhost:5000/api/recommend/student \
  -H "Content-Type: application/json" \
  -d '{
    "student_info": {
      "university": "清华大学",
      "gpa": 3.8,
      "current_major": "电子工程",
      "ielts_score": 7.5
    },
    "top_n": 5
  }'
```

## 错误处理

### 常见错误码

- `400`: 请求参数错误
  - `MISSING_STUDENT_INFO`: 缺少学生信息
  - `INVALID_STUDENT_INFO`: 学生信息验证失败
  - `MISSING_TARGET_MAJOR`: 缺少目标专业

- `404`: 资源不存在
  - `MAJOR_NOT_FOUND`: 指定专业不存在

- `500`: 服务器内部错误
  - `INTERNAL_SERVER_ERROR`: 系统内部错误

### 错误响应示例

```json
{
  "success": false,
  "error": "缺少必要字段: ['university']",
  "error_code": "INVALID_STUDENT_INFO"
}
```

## 系统特性

### 1. 自动特征工程
- 自动将原始学生信息转换为75维特征向量
- 支持院校层次评分、GPA标准化、语言成绩归一化
- 智能处理缺失数据，提供合理默认值

### 2. 智能匹配算法
- 基于94,021条历史申请记录训练
- 使用增强匹配系统，平均置信度88.1%
- 支持多维度匹配评估

### 3. 生产级性能
- 支持并发请求处理
- 完整的错误处理和日志记录
- 跨域请求支持(CORS)

### 4. 灵活的输入格式
- 支持多种GPA制式(4.0制、5.0制、百分制)
- 支持多种语言考试成绩(IELTS、TOEFL、PTE、Duolingo)
- 可选字段允许部分信息缺失

## 注意事项

1. **数据隐私**: 系统不会存储用户提交的个人信息
2. **成绩格式**: GPA请使用对应制式的标准格式
3. **院校名称**: 建议使用中文全称，系统支持智能匹配
4. **专业名称**: 目标专业请使用英文标准名称
5. **服务稳定性**: 建议在生产环境使用专业WSGI服务器

## 技术支持

如有问题请参考：
- `DEPLOYMENT_GUIDE.md`: 详细部署指南
- `USAGE_GUIDE.md`: 系统使用说明
- `main.py`: 系统演示程序

---

*更新时间: 2025-09-05*  
*API版本: v2.0*  
*系统版本: 生产级增强版*