#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生专业匹配系统 - 生产级API服务
接受原始学生信息，自动进行特征化转换和匹配计算
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import logging
import traceback
import time
import os
import sys
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.matching_engine.enhanced_matching_system import EnhancedStudentMajorMatchingSystem
from src.feature_engineering.student_feature_converter import StudentFeatureConverter

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
matching_system = None
feature_converter = None
quick_check_data = {}

# 加载快速检查数据
try:
    with open('data/processed/quick_check_data.json', 'r', encoding='utf-8') as f:
        quick_check_data = json.load(f)
    logger.info(f"加载快速检查数据: 院校{len(quick_check_data.get('university_name_to_id', {}))}个, 专业{len(quick_check_data.get('major_name_to_id', {}))}个")
except Exception as e:
    logger.warning(f"无法加载快速检查数据: {e}")
    quick_check_data = {}

system_status = {
    'initialized': False,
    'initialization_time': None,
    'total_requests': 0,
    'successful_requests': 0,
    'error_requests': 0,
    'avg_response_time': 0.0
}

def initialize_system():
    """初始化匹配系统"""
    global matching_system, feature_converter
    
    try:
        logger.info("开始初始化学生专业匹配系统...")
        start_time = time.time()
        
        # 初始化特征转换器
        feature_converter = StudentFeatureConverter()
        logger.info("特征转换器初始化完成")
        
        # 初始化匹配系统
        matching_system = EnhancedStudentMajorMatchingSystem()
        matching_system.initialize_system()
        logger.info("匹配系统初始化完成")
        
        initialization_time = time.time() - start_time
        system_status['initialized'] = True
        system_status['initialization_time'] = initialization_time
        
        logger.info(f"系统初始化完成，用时: {initialization_time:.2f}秒")
        return True
        
    except Exception as e:
        logger.error(f"系统初始化失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_data_sufficiency_by_id(university_id=None, major_id=None, university_name=None, major_name=None):
    """
    基于ID进行数据充足性检查，优先使用ID，备选使用名称
    
    Args:
        university_id: 院校ID（推荐）
        major_id: 专业ID（推荐）  
        university_name: 院校名称（备选）
        major_name: 专业名称（备选）
    
    Returns:
        dict: {'sufficient': bool, 'reason': str, 'suggestion': str, ...}
    """
    if not quick_check_data:
        return {'sufficient': True, 'reason': '快速检查数据未加载'}
    
    min_threshold = quick_check_data.get('min_data_threshold', 100)
    uni_mapping = quick_check_data.get('university_name_to_id', {})
    major_mapping = quick_check_data.get('major_name_to_id', {})
    uni_counts = quick_check_data.get('university_id_counts', {})
    major_counts = quick_check_data.get('major_id_counts', {})
    
    # 1. 院校数据检查 - 优先使用ID
    final_uni_id = None
    if university_id is not None:
        # 使用提供的ID
        final_uni_id = university_id
    elif university_name and university_name in uni_mapping:
        # 尝试名称映射到ID
        final_uni_id = uni_mapping[university_name]
    elif university_name:
        # 名称无法映射
        return {
            'sufficient': False,
            'reason': f'院校"{university_name}"无法映射到有效ID',
            'error_code': 'ID_MAPPING_FAILED',
            'suggestion': '建议直接使用university_id参数，或检查院校名称拼写'
        }
    
    # 检查院校ID的数据量
    if final_uni_id is not None:
        uni_count = int(uni_counts.get(str(final_uni_id), 0))
        if uni_count < min_threshold:
            # 获取数据充足的院校ID建议
            sufficient_unis = [uid for uid, count in uni_counts.items() if int(count) >= min_threshold][:5]
            return {
                'sufficient': False,
                'reason': f'院校ID {final_uni_id} 历史数据不足（{uni_count}条<{min_threshold}条）',
                'error_code': 'INSUFFICIENT_DATA',
                'suggestion': '建议选择数据更充足的院校',
                'available_university_ids': [int(uid) for uid in sufficient_unis]
            }
    
    # 2. 专业数据检查 - 优先使用ID
    final_major_id = None
    if major_id is not None:
        # 使用提供的ID
        final_major_id = major_id
    elif major_name and major_name in major_mapping:
        # 尝试名称映射到ID
        final_major_id = major_mapping[major_name]
    elif major_name:
        # 名称无法映射
        return {
            'sufficient': False,
            'reason': f'专业"{major_name}"无法映射到有效ID',
            'error_code': 'ID_MAPPING_FAILED',
            'suggestion': '建议直接使用target_major_id参数，或检查专业名称拼写'
        }
    
    # 检查专业ID的数据量
    if final_major_id is not None:
        major_count = int(major_counts.get(str(final_major_id), 0))
        if major_count < min_threshold:
            # 获取数据充足的专业ID建议
            sufficient_majors = [mid for mid, count in major_counts.items() if int(count) >= min_threshold][:5]
            return {
                'sufficient': False,
                'reason': f'专业ID {final_major_id} 历史数据不足（{major_count}条<{min_threshold}条）',
                'error_code': 'INSUFFICIENT_DATA',
                'suggestion': '建议选择数据更充足的专业',
                'sufficient_major_ids': [int(mid) for mid in sufficient_majors]
            }
    
    return {'sufficient': True}

def validate_student_info(student_info):
    """验证学生信息的完整性"""
    required_fields = ['university', 'gpa', 'current_major']
    missing_fields = []
    
    for field in required_fields:
        if field not in student_info or not student_info[field]:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"缺少必要字段: {missing_fields}"
    
    # 验证数据类型
    try:
        gpa = float(student_info['gpa'])
        if gpa < 0 or gpa > 4.5:  # 假设最高4.5分制
            return False, "GPA值超出合理范围(0-4.5)"
    except (ValueError, TypeError):
        return False, "GPA必须是有效数字"
    
    return True, "验证通过"

# API路由定义

@app.route('/', methods=['GET'])
def home():
    """API主页"""
    api_doc = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>学生专业匹配API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
            .method { color: #27ae60; font-weight: bold; }
            code { background: #ecf0f1; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <h1 class="header">🎓 学生专业匹配系统 API</h1>
        <p>基于94,021条历史成功申请数据的智能专业匹配服务</p>
        
        <h2>API接口列表</h2>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/match/student</h3>
            <p>根据原始学生信息进行专业匹配</p>
            <p><strong>输入</strong>: 原始学生信息（院校、GPA、专业等）</p>
            <p><strong>输出</strong>: 匹配度分数、置信度、推荐等级</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /api/recommend/student</h3>
            <p>为学生推荐最佳匹配专业（Top N）</p>
            <p><strong>输入</strong>: 原始学生信息 + 推荐数量</p>
            <p><strong>输出</strong>: 排序的专业推荐列表</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/majors</h3>
            <p>获取支持的专业列表</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/status</h3>
            <p>获取系统状态信息</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /api/schema</h3>
            <p>获取学生信息输入格式说明</p>
        </div>
        
        <h2>使用示例</h2>
        <pre><code>
curl -X POST http://localhost:5000/api/match/student \\
  -H "Content-Type: application/json" \\
  -d '{
    "university": "北京理工大学",
    "gpa": 3.5,
    "current_major": "计算机科学与技术",
    "target_major": "Master of Computer Science",
    "language_test": {"type": "IELTS", "score": 7.0}
  }'
        </code></pre>
        
        <p><strong>系统状态</strong>: {{ '🟢 运行正常' if status_initialized else '🔴 未初始化' }}</p>
        <p><strong>支持专业数</strong>: {{ major_count if status_initialized else '未知' }}</p>
    </body>
    </html>
    """
    
    context = {
        'status_initialized': system_status['initialized'],
        'major_count': len(matching_system.get_available_majors()) if matching_system else 0
    }
    
    return render_template_string(api_doc, **context)

@app.route('/api/match/student', methods=['POST'])
def match_student():
    """学生专业匹配API - 接受原始学生信息"""
    request_start_time = time.time()
    system_status['total_requests'] += 1
    
    try:
        # 检查系统状态
        if not system_status['initialized']:
            return jsonify({
                'success': False,
                'error': '系统未初始化，请稍后再试',
                'error_code': 'SYSTEM_NOT_INITIALIZED'
            }), 503
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供JSON格式的学生信息',
                'error_code': 'INVALID_JSON'
            }), 400
        
        # 提取学生信息和目标专业（支持ID优先）
        target_major_id = data.get('target_major_id')
        target_major = data.get('target_major')
        
        # 调试输出
        logger.info(f"DEBUG: target_major_id = {target_major_id}, type = {type(target_major_id)}")
        logger.info(f"DEBUG: target_major = {target_major}, type = {type(target_major)}")
        logger.info(f"DEBUG: not target_major_id = {not target_major_id}")
        logger.info(f"DEBUG: not target_major = {not target_major}")
        
        # 验证目标专业：优先使用ID，备选使用名称
        if not target_major_id and not target_major:
            return jsonify({
                'success': False,
                'error': 'DEBUG_TEST_MESSAGE: 缺少专业参数',
                'error_code': 'MISSING_TARGET_MAJOR'
            }), 400
        
        # 支持ID优先的参数处理
        university_id = data.get('university_id')
        university_name = data.get('university')
        
        # 如果提供了university_id但没有university名称，尝试从映射中获取
        if university_id and not university_name:
            # 这里我们允许不提供名称，因为有ID就足够了
            university_name = f"University_ID_{university_id}"  # 占位符
        
        # 学生信息字段
        student_info = {
            'university': university_name,
            'gpa': data.get('gpa'),
            'current_major': data.get('current_major'),
            'gpa_scale': data.get('gpa_scale'),
            'target_university': data.get('target_university'),
            'ielts_score': data.get('ielts_score'),
            'toefl_score': data.get('toefl_score'),
            'work_experience_years': data.get('work_experience_years'),
            'work_field': data.get('work_field'),
            'research_experience': data.get('research_experience')
        }
        
        # 验证学生信息 - 如果有university_id，university字段就不是必需的
        required_fields = ['gpa', 'current_major']
        if not university_id:  # 只有在没有university_id时才要求university名称
            required_fields.append('university')
            
        missing_fields = [field for field in required_fields if field not in student_info or not student_info[field]]
        if missing_fields:
            error_msg = f"缺少必要字段: {missing_fields}"
            if 'university' in missing_fields:
                error_msg += "，请提供university_id或university"
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'INVALID_STUDENT_INFO'
            }), 400
        
        # 数据充足性检查 - 支持ID和名称
        
        data_check = check_data_sufficiency_by_id(
            university_id=university_id,
            major_id=target_major_id, 
            university_name=university_name,
            major_name=target_major
        )
        
        if not data_check['sufficient']:
            response = {
                'success': False,
                'error': data_check['reason'],
                'error_code': data_check.get('error_code', 'INSUFFICIENT_DATA'),
                'suggestion': data_check.get('suggestion', '')
            }
            # 添加ID建议
            if 'available_university_ids' in data_check:
                response['available_university_ids'] = data_check['available_university_ids']
            if 'sufficient_major_ids' in data_check:
                response['sufficient_major_ids'] = data_check['sufficient_major_ids']
            
            return jsonify(response), 400
        
        # 将原始学生信息转换为特征
        logger.info(f"开始处理匹配请求: {student_info.get('university', 'Unknown')} -> {target_major}")
        
        try:
            features = feature_converter.convert_raw_student_info(student_info)
            logger.debug(f"特征转换完成，特征数量: {len(features)}")
        except Exception as e:
            logger.error(f"特征转换失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'特征转换失败: {str(e)}',
                'error_code': 'FEATURE_CONVERSION_ERROR'
            }), 500
        
        # 执行匹配计算
        try:
            result = matching_system.calculate_enhanced_single_match(features, target_major)
        except Exception as e:
            logger.error(f"匹配计算失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'匹配计算失败: {str(e)}',
                'error_code': 'MATCHING_CALCULATION_ERROR'
            }), 500
        
        # 添加原始输入信息到结果中
        if result.get('success', False):
            result['input_info'] = {
                'university': student_info.get('university'),
                'gpa': student_info.get('gpa'),
                'current_major': student_info.get('current_major'),
                'target_major': target_major
            }
            
            # 添加业务解释
            result['explanation'] = generate_match_explanation(
                student_info, target_major, result
            )
        
        # 更新统计信息
        response_time = time.time() - request_start_time
        system_status['successful_requests'] += 1
        system_status['avg_response_time'] = (
            (system_status['avg_response_time'] * (system_status['successful_requests'] - 1) + response_time) /
            system_status['successful_requests']
        )
        
        logger.info(f"匹配请求完成，用时: {response_time:.3f}秒，匹配度: {result.get('match_score', 'N/A')}分")
        
        return jsonify(result)
        
    except Exception as e:
        system_status['error_requests'] += 1
        logger.error(f"API请求处理失败: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'debug_info': str(e) if app.debug else None
        }), 500

@app.route('/api/recommend/student', methods=['POST'])
def recommend_majors():
    """为学生推荐最佳专业API"""
    request_start_time = time.time()
    system_status['total_requests'] += 1
    
    try:
        if not system_status['initialized']:
            return jsonify({
                'success': False,
                'error': '系统未初始化，请稍后再试'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供JSON格式的学生信息'
            }), 400
        
        # 支持ID优先的参数处理
        university_id = data.get('university_id')
        university_name = data.get('university')
        
        # 如果提供了university_id但没有university名称，允许不提供名称
        if university_id and not university_name:
            university_name = f"University_ID_{university_id}"  # 占位符
        
        # 简化为扁平结构
        student_info = {
            'university': university_name,
            'gpa': data.get('gpa'),
            'current_major': data.get('current_major'),
            'gpa_scale': data.get('gpa_scale'),
            'target_university': data.get('target_university'),
            'ielts_score': data.get('ielts_score'),
            'toefl_score': data.get('toefl_score'),
            'work_experience_years': data.get('work_experience_years'),
            'work_field': data.get('work_field'),
            'research_experience': data.get('research_experience')
        }
        
        top_n = data.get('top_n', 5)  # 默认推荐5个专业
        
        # 验证学生信息（推荐不需要target_major）- 支持ID优先
        required_fields = ['gpa', 'current_major']
        if not university_id:  # 只有在没有university_id时才要求university名称
            required_fields.append('university')
            
        missing_fields = [field for field in required_fields if field not in student_info or student_info[field] is None]
        if missing_fields:
            error_msg = f"缺少必要字段: {missing_fields}"
            if 'university' in missing_fields:
                error_msg += "，请提供university_id或university"
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 数据充足性检查（推荐场景只检查院校）
        
        data_check = check_data_sufficiency_by_id(
            university_id=university_id,
            major_id=None,  # 推荐场景不检查特定专业
            university_name=university_name,
            major_name=None
        )
        
        if not data_check['sufficient']:
            response = {
                'success': False,
                'error': data_check['reason'],
                'error_code': data_check.get('error_code', 'INSUFFICIENT_DATA'),
                'suggestion': data_check.get('suggestion', '')
            }
            # 添加ID建议  
            if 'available_university_ids' in data_check:
                response['available_university_ids'] = data_check['available_university_ids']
                
            return jsonify(response), 400
        
        # 特征转换
        features = feature_converter.convert_raw_student_info(student_info)
        
        # 获取推荐
        result = matching_system.find_enhanced_best_matches(features, top_n)
        
        if result.get('success', False):
            result['input_info'] = {
                'university': student_info.get('university'),
                'gpa': student_info.get('gpa'),
                'current_major': student_info.get('current_major')
            }
            
            # 为每个推荐添加解释
            for i, match in enumerate(result.get('best_matches', [])):
                match['explanation'] = generate_recommendation_explanation(
                    student_info, match, i + 1
                )
        
        system_status['successful_requests'] += 1
        response_time = time.time() - request_start_time
        
        logger.info(f"推荐请求完成，用时: {response_time:.3f}秒，推荐专业数: {len(result.get('best_matches', []))}")
        
        return jsonify(result)
        
    except Exception as e:
        system_status['error_requests'] += 1
        logger.error(f"推荐请求处理失败: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': '推荐服务暂时不可用',
            'debug_info': str(e) if app.debug else None
        }), 500

@app.route('/api/majors', methods=['GET'])
def get_available_majors():
    """获取支持的专业列表"""
    try:
        if not system_status['initialized']:
            return jsonify({
                'success': False,
                'error': '系统未初始化'
            }), 503
        
        majors = matching_system.get_available_majors()
        
        return jsonify({
            'success': True,
            'majors': majors,
            'count': len(majors),
            'categories': categorize_majors(majors)
        })
        
    except Exception as e:
        logger.error(f"获取专业列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '无法获取专业列表'
        }), 500

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        status_info = system_status.copy()
        
        if matching_system:
            enhanced_status = matching_system.get_enhanced_system_status()
            status_info.update(enhanced_status)
        
        return jsonify({
            'success': True,
            'status': status_info,
            'server_time': datetime.now().isoformat(),
            'version': '2.0.0'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'无法获取系统状态: {str(e)}'
        }), 500

@app.route('/api/schema', methods=['GET'])
def get_input_schema():
    """获取学生信息输入格式说明"""
    try:
        schema = feature_converter.get_raw_student_schema()
        return jsonify({
            'success': True,
            'schema': schema,
            'description': '学生信息输入格式说明'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'无法获取输入格式说明: {str(e)}'
        }), 500

# 辅助函数

def generate_match_explanation(student_info, target_major, result):
    """生成匹配结果解释"""
    university = student_info.get('university', '未知院校')
    gpa = student_info.get('gpa', 0)
    current_major = student_info.get('current_major', '未知专业')
    match_score = result.get('match_score', 0)
    match_level = result.get('match_level', '未知')
    
    explanation = {
        'match_summary': f"基于您的背景（{university}，GPA {gpa}，{current_major}专业），申请{target_major}的匹配度为{match_score}分（{match_level}）",
        'score_interpretation': get_score_interpretation(match_score),
        'recommendation': get_match_recommendation(match_score, match_level)
    }
    
    return explanation

def generate_recommendation_explanation(student_info, match_info, rank):
    """生成推荐解释"""
    major = match_info.get('major', '未知专业')
    score = match_info.get('score', 0)
    level = match_info.get('level', '未知')
    
    return {
        'rank': rank,
        'summary': f"第{rank}推荐：{major}（{score}分，{level}）",
        'reason': get_recommendation_reason(score, level, rank)
    }

def get_score_interpretation(score):
    """获取分数解释"""
    if score >= 85:
        return "非常高的匹配度，您的背景与该专业的历史成功申请者高度相似"
    elif score >= 70:
        return "较高的匹配度，您具备申请该专业的良好条件"
    elif score >= 55:
        return "中等匹配度，您的条件基本符合该专业要求"
    elif score >= 40:
        return "匹配度偏低，建议提升相关背景或考虑其他专业"
    else:
        return "匹配度较低，该专业可能不太适合您的背景"

def get_match_recommendation(score, level):
    """获取匹配建议"""
    if score >= 85:
        return "强烈推荐申请，成功概率很高"
    elif score >= 70:
        return "推荐申请，建议准备充分的申请材料"
    elif score >= 55:
        return "可以考虑申请，同时准备备选方案"
    else:
        return "建议先提升相关能力或考虑其他更适合的专业"

def get_recommendation_reason(score, level, rank):
    """获取推荐理由"""
    if rank <= 2:
        return f"基于您的背景分析，这是最适合您的专业之一（匹配度{score}分）"
    elif rank <= 5:
        return f"这个专业与您的背景有良好的匹配性（匹配度{score}分）"
    else:
        return f"这是一个值得考虑的备选专业（匹配度{score}分）"

def categorize_majors(majors):
    """将专业按类别分组"""
    categories = {
        '工程技术类': [],
        '商科管理类': [], 
        '计算机信息类': [],
        '理学类': [],
        '人文社科类': [],
        '医学健康类': [],
        '其他': []
    }
    
    for major in majors:
        major_lower = major.lower()
        
        if any(keyword in major_lower for keyword in ['engineering', 'engineer', 'technology']):
            categories['工程技术类'].append(major)
        elif any(keyword in major_lower for keyword in ['business', 'commerce', 'management', 'mba', 'finance']):
            categories['商科管理类'].append(major)
        elif any(keyword in major_lower for keyword in ['computer', 'computing', 'software', 'data', 'it']):
            categories['计算机信息类'].append(major)
        elif any(keyword in major_lower for keyword in ['science', 'physics', 'chemistry', 'biology', 'math']):
            categories['理学类'].append(major)
        elif any(keyword in major_lower for keyword in ['arts', 'literature', 'language', 'history', 'law']):
            categories['人文社科类'].append(major)
        elif any(keyword in major_lower for keyword in ['medicine', 'medical', 'health', 'nursing']):
            categories['医学健康类'].append(major)
        else:
            categories['其他'].append(major)
    
    # 移除空分类
    return {k: v for k, v in categories.items() if v}

# 错误处理

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API端点不存在',
        'error_code': 'NOT_FOUND'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': '请求方法不被允许',
        'error_code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'error_code': 'INTERNAL_SERVER_ERROR'
    }), 500

# 启动应用

if __name__ == '__main__':
    print("=" * 60)
    print("  学生专业匹配系统 - 生产级API服务")
    print("=" * 60)
    
    # 初始化系统
    if initialize_system():
        print("启动API服务...")
        
        # 开发环境配置
        app.config['DEBUG'] = False  # 生产环境设为False
        app.config['JSON_AS_ASCII'] = False  # 支持中文输出
        
        # 启动服务
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    else:
        print("❌ 系统初始化失败，无法启动API服务")
        exit(1)