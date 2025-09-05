#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
专业分类体系模块
提供完整的专业分类功能，包括：
1. 中英文专业名称标准化
2. 7大专业类别分类（商科、工科、理科、文科、法学、艺术、医学）
3. 详细子分类
4. 智能匹配算法
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MajorClassificationSystem:
    """专业分类系统"""
    
    def __init__(self):
        """初始化分类系统"""
        self.major_hierarchy = self._build_major_hierarchy()
        self.name_mapping = self._build_name_mapping()
        self.keyword_weights = self._build_keyword_weights()
        
    def _build_major_hierarchy(self) -> Dict:
        """构建专业分类层次结构"""
        return {
            '商科': {
                'subcategories': {
                    '金融': {
                        'keywords': ['finance', 'banking', 'financial', '金融', '银行', '投资', 'investment', 
                                   'portfolio', 'wealth', 'treasury', 'capital', 'equity', 'bond', 'derivative'],
                        'exact_matches': ['Finance', 'Financial Management', '金融学', '金融管理', 'Banking', 
                                        'Investment', 'Financial Engineering', '金融工程']
                    },
                    '会计': {
                        'keywords': ['accounting', 'accountancy', '会计', 'audit', '审计', 'cpa', 'acca',
                                   'bookkeeping', 'financial reporting', 'taxation', '税务'],
                        'exact_matches': ['Accounting', 'Accountancy', '会计学', 'Professional Accounting',
                                        'Audit', '审计学', 'Taxation']
                    },
                    '工商管理': {
                        'keywords': ['business administration', 'management', 'mba', '工商管理', '企业管理',
                                   'corporate', 'executive', 'leadership', 'strategy', 'operations'],
                        'exact_matches': ['Business Administration', 'MBA', '工商管理', 'Management',
                                        'Executive Management', 'Strategic Management']
                    },
                    '市场营销': {
                        'keywords': ['marketing', 'sales', '市场营销', '销售', 'brand', 'advertising', 
                                   'promotion', 'customer', 'digital marketing', 'social media'],
                        'exact_matches': ['Marketing', '市场营销', 'Digital Marketing', 'Brand Management',
                                        'Sales Management', 'Advertising']
                    },
                    '经济学': {
                        'keywords': ['economics', 'economic', '经济学', '经济', 'macro', 'micro', 'econometrics',
                                   'trade', 'international economics', '国际经济', 'development economics'],
                        'exact_matches': ['Economics', '经济学', 'International Economics', '国际经济学',
                                        'Development Economics', 'Applied Economics']
                    },
                    '国际贸易': {
                        'keywords': ['international trade', 'global business', '国际贸易', '国际商务',
                                   'import', 'export', 'logistics', 'supply chain', 'international business',
                                   '物流', '供应链', '物流管理', '供应链管理', '进出口', '贸易'],
                        'exact_matches': ['International Trade', '国际贸易', 'International Business',
                                        '国际商务', 'Global Business', 'Supply Chain Management', '物流管理', '供应链管理']
                    },
                    '商务': {
                        'keywords': ['commerce', 'business', '商务', 'commercial', 'trade', 'mercantile',
                                   'e-commerce', 'retail', 'wholesale'],
                        'exact_matches': ['Commerce', 'Business', '商务', 'Commercial Law', 'E-commerce',
                                        'Master of Commerce', 'Bachelor of Commerce']
                    },
                    '人力资源': {
                        'keywords': ['human resource', 'hr', '人力资源', 'personnel', 'recruitment',
                                   'organizational behavior', 'talent management', 'workforce'],
                        'exact_matches': ['Human Resource Management', '人力资源管理', 'HR Management',
                                        'Organizational Behavior', 'Personnel Management']
                    },
                    '信息管理': {
                        'keywords': ['information management', '信息管理', '管理信息系统', '信息系统', 
                                   'data management', '数据管理', 'system analysis', '系统分析', 'mis',
                                   'information systems', 'database management', '数据库管理'],
                        'exact_matches': ['Information Management', '信息管理与信息系统', '管理信息系统',
                                        'Management Information Systems', 'Information Systems', 'MIS']
                    }
                }
            },
            '工科': {
                'subcategories': {
                    '计算机科学': {
                        'keywords': ['computer science', 'cs', '计算机科学', '计算机', 'programming', 'coding',
                                   'algorithm', 'data structure', 'software development', 'artificial intelligence'],
                        'exact_matches': ['Computer Science', '计算机科学与技术', 'Computer Science and Technology',
                                        'Applied Computer Science', 'Computer Systems']
                    },
                    '软件工程': {
                        'keywords': ['software engineering', '软件工程', 'software development', 'programming',
                                   'application development', 'system design', 'software architecture'],
                        'exact_matches': ['Software Engineering', '软件工程', 'Software Development',
                                        'Application Development', 'Software Systems']
                    },
                    '信息技术': {
                        'keywords': ['information technology', 'it', '信息技术', 'information systems',
                                   'network', 'database', 'cybersecurity', 'cloud computing'],
                        'exact_matches': ['Information Technology', '信息技术', 'Information Systems',
                                        'IT Management', 'Network Engineering', 'Database Systems']
                    },
                    '数据科学': {
                        'keywords': ['data science', '数据科学', 'big data', 'machine learning', 'analytics',
                                   'data mining', 'business intelligence', 'statistics', 'data analysis'],
                        'exact_matches': ['Data Science', '数据科学', 'Data Analytics', 'Machine Learning',
                                        'Business Intelligence', 'Data Mining']
                    },
                    '电子工程': {
                        'keywords': ['electrical engineering', 'electronics', '电子工程', '电气工程',
                                   'circuit', 'power', 'signal', 'communication', 'automation', '电子信息',
                                   '信息工程', '电子信息工程', '电子', '信息', '自动化', '电气'],
                        'exact_matches': ['Electrical Engineering', '电气工程', 'Electronics Engineering',
                                        '电子工程', 'Electrical and Electronic Engineering', '电子信息工程',
                                        '电气工程及其自动化', '自动化']
                    },
                    '机械工程': {
                        'keywords': ['mechanical engineering', '机械工程', 'mechanical', 'manufacturing',
                                   'automotive', 'aerospace', 'robotics', 'thermal'],
                        'exact_matches': ['Mechanical Engineering', '机械工程', 'Manufacturing Engineering',
                                        'Automotive Engineering', 'Aerospace Engineering']
                    },
                    '土木工程': {
                        'keywords': ['civil engineering', '土木工程', 'construction', 'infrastructure',
                                   'structural', 'environmental engineering', 'transportation'],
                        'exact_matches': ['Civil Engineering', '土木工程', 'Construction Engineering',
                                        'Structural Engineering', 'Transportation Engineering']
                    },
                    '通信工程': {
                        'keywords': ['communication engineering', '通信工程', 'telecommunications', 'wireless',
                                   'network communication', 'signal processing', '5g', 'mobile'],
                        'exact_matches': ['Communication Engineering', '通信工程', 'Telecommunications',
                                        'Wireless Communication', 'Network Engineering']
                    },
                    '环境工程': {
                        'keywords': ['environmental engineering', '环境工程', '环境', '环保', '生态', '污染',
                                   'environmental science', '环境科学', '环境保护', 'ecology', 'pollution',
                                   'sustainability', '可持续', 'waste management', '废物处理'],
                        'exact_matches': ['Environmental Engineering', '环境工程', 'Environmental Science',
                                        '环境科学', 'Environmental Protection', '环境保护']
                    },
                    '材料工程': {
                        'keywords': ['materials engineering', '材料工程', '材料', '材料科学', 'materials science',
                                   '金属', 'metal', '复合材料', 'composite', '纳米材料', 'nanomaterials',
                                   'polymer', '聚合物', 'ceramics', '陶瓷', 'metallurgy', '冶金'],
                        'exact_matches': ['Materials Engineering', '材料工程', 'Materials Science and Engineering',
                                        '材料科学与工程', 'Materials Science', '材料科学', 'Metallurgy', '冶金工程']
                    },
                    '食品工程': {
                        'keywords': ['food engineering', '食品工程', '食品', '食品科学', 'food science',
                                   '营养', 'nutrition', '食品安全', 'food safety', '食品技术', 'food technology',
                                   'food processing', '食品加工', 'biotechnology', '生物技术'],
                        'exact_matches': ['Food Engineering', '食品工程', 'Food Science and Engineering',
                                        '食品科学与工程', 'Food Science', '食品科学', 'Food Technology', '食品技术']
                    }
                }
            },
            '理科': {
                'subcategories': {
                    '数学': {
                        'keywords': ['mathematics', 'math', '数学', 'statistics', '统计', 'applied mathematics',
                                   'pure mathematics', 'mathematical', 'calculus', 'algebra'],
                        'exact_matches': ['Mathematics', '数学', 'Applied Mathematics', '应用数学',
                                        'Statistics', '统计学', 'Mathematical Sciences']
                    },
                    '物理学': {
                        'keywords': ['physics', '物理', 'theoretical physics', 'applied physics',
                                   'quantum', 'mechanics', 'thermodynamics', 'electromagnetism'],
                        'exact_matches': ['Physics', '物理学', 'Applied Physics', '应用物理',
                                        'Theoretical Physics', 'Mathematical Physics']
                    },
                    '化学': {
                        'keywords': ['chemistry', '化学', 'chemical', 'organic chemistry', 'inorganic',
                                   'analytical chemistry', 'biochemistry', 'physical chemistry'],
                        'exact_matches': ['Chemistry', '化学', 'Applied Chemistry', '应用化学',
                                        'Chemical Engineering', 'Biochemistry']
                    },
                    '生物学': {
                        'keywords': ['biology', '生物', 'biological', 'life science', 'biotechnology',
                                   'molecular biology', 'genetics', 'ecology', 'microbiology'],
                        'exact_matches': ['Biology', '生物学', 'Biological Sciences', 'Life Sciences',
                                        'Biotechnology', 'Molecular Biology']
                    },
                    '地理学': {
                        'keywords': ['geography', '地理', 'geological', 'earth science', 'environmental science',
                                   'geology', 'meteorology', 'oceanography'],
                        'exact_matches': ['Geography', '地理学', 'Geology', '地质学',
                                        'Earth Sciences', 'Environmental Science']
                    },
                    '心理学': {
                        'keywords': ['psychology', '心理学', 'psychological', 'cognitive', 'behavioral',
                                   'clinical psychology', 'social psychology', 'developmental psychology'],
                        'exact_matches': ['Psychology', '心理学', 'Applied Psychology', '应用心理学',
                                        'Clinical Psychology', 'Social Psychology']
                    },
                    '社会学': {
                        'keywords': ['sociology', '社会学', '社会', 'social', '社会工作', 'social work',
                                   '社会服务', 'social service', '社区', 'community', '社会管理',
                                   'social management', 'social welfare', '社会福利'],
                        'exact_matches': ['Sociology', '社会学', 'Social Work', '社会工作',
                                        'Social Service', '社会服务', 'Community Service']
                    }
                }
            },
            '文科': {
                'subcategories': {
                    '语言文学': {
                        'keywords': ['english', 'chinese', 'literature', 'linguistics', '英语', '中文', '文学',
                                   'language', 'translation', 'interpretation', 'comparative literature'],
                        'exact_matches': ['English', '英语', 'Chinese Language and Literature', '汉语言文学',
                                        'Literature', 'Linguistics', 'Translation Studies']
                    },
                    '教育学': {
                        'keywords': ['education', '教育', 'teaching', 'pedagogy', 'educational',
                                   'early childhood', 'primary education', 'secondary education', 'tesol'],
                        'exact_matches': ['Education', '教育学', 'Teaching', 'TESOL', 'Educational Psychology',
                                        'Early Childhood Education', 'Primary Education']
                    },
                    '新闻传播': {
                        'keywords': ['journalism', 'media', 'communication', '新闻', '传播', '媒体',
                                   'broadcasting', 'mass communication', 'digital media', 'public relations'],
                        'exact_matches': ['Journalism', '新闻学', 'Media Studies', '传媒学',
                                        'Communication Studies', 'Public Relations', 'Broadcasting']
                    },
                    '历史学': {
                        'keywords': ['history', '历史', 'historical', 'archaeology', 'heritage',
                                   'cultural studies', 'ancient history', 'modern history'],
                        'exact_matches': ['History', '历史学', 'Cultural Studies', '文化研究',
                                        'Archaeology', '考古学', 'Heritage Studies']
                    },
                    '哲学': {
                        'keywords': ['philosophy', '哲学', 'philosophical', 'ethics', 'logic',
                                   'metaphysics', 'epistemology', 'political philosophy'],
                        'exact_matches': ['Philosophy', '哲学', 'Ethics', '伦理学',
                                        'Political Philosophy', 'Applied Philosophy']
                    },
                    '政治学': {
                        'keywords': ['political science', '政治学', '政治', 'politics', '国际政治', 
                                   'international politics', '外交', 'diplomacy', '政策', 'policy',
                                   '公共管理', 'public administration', '行政', 'administration',
                                   'government', '政府', 'international relations', '国际关系'],
                        'exact_matches': ['Political Science', '政治学', 'International Politics', '国际政治',
                                        'Public Administration', '公共管理', 'International Relations', '国际关系',
                                        'Government', 'Policy Studies']
                    }
                }
            },
            '法学': {
                'subcategories': {
                    '法学': {
                        'keywords': ['law', 'legal', 'juris', '法学', '法律', 'jurisprudence',
                                   'legal studies', 'legislation', 'constitutional law'],
                        'exact_matches': ['Law', '法学', 'Legal Studies', '法律学',
                                        'Juris Doctor', 'Master of Laws', 'Bachelor of Laws']
                    },
                    '商法': {
                        'keywords': ['business law', 'commercial law', '商法', 'corporate law',
                                   'contract law', 'company law', 'securities law'],
                        'exact_matches': ['Business Law', '商法', 'Commercial Law', '商业法',
                                        'Corporate Law', 'Contract Law']
                    },
                    '国际法': {
                        'keywords': ['international law', '国际法', 'comparative law', 'human rights law',
                                   'diplomatic law', 'trade law', 'maritime law'],
                        'exact_matches': ['International Law', '国际法', 'Comparative Law',
                                        'Human Rights Law', 'International Trade Law']
                    }
                }
            },
            '艺术': {
                'subcategories': {
                    '设计': {
                        'keywords': ['design', '设计', 'graphic design', 'industrial design', 'fashion design',
                                   'interior design', 'web design', 'user experience', 'ux', 'ui'],
                        'exact_matches': ['Design', '设计学', 'Graphic Design', '平面设计',
                                        'Industrial Design', 'Fashion Design', 'Interior Design']
                    },
                    '艺术': {
                        'keywords': ['art', 'fine art', '艺术', '美术', 'painting', 'sculpture',
                                   'photography', 'contemporary art', 'visual arts'],
                        'exact_matches': ['Art', '艺术学', 'Fine Arts', '美术学',
                                        'Visual Arts', 'Contemporary Art', 'Applied Arts']
                    },
                    '音乐': {
                        'keywords': ['music', '音乐', 'musical', 'composition', 'performance',
                                   'music theory', 'music education', 'musicology'],
                        'exact_matches': ['Music', '音乐学', 'Music Performance', '音乐表演',
                                        'Music Composition', 'Music Education', 'Musicology']
                    },
                    '影视': {
                        'keywords': ['film', 'cinema', 'video', '电影', '影视', 'media production',
                                   'animation', 'documentary', 'screenwriting', 'cinematography'],
                        'exact_matches': ['Film Studies', '电影学', 'Media Production', '影视制作',
                                        'Animation', 'Cinematography', 'Film and Television']
                    },
                    '建筑': {
                        'keywords': ['architecture', '建筑', 'architectural', 'urban planning',
                                   'landscape architecture', 'building design', 'construction'],
                        'exact_matches': ['Architecture', '建筑学', 'Urban Planning', '城市规划',
                                        'Landscape Architecture', 'Architectural Engineering']
                    }
                }
            },
            '医学': {
                'subcategories': {
                    '临床医学': {
                        'keywords': ['medicine', 'medical', '医学', '临床', 'clinical', 'physician',
                                   'surgery', 'internal medicine', 'pediatrics', 'obstetrics'],
                        'exact_matches': ['Medicine', '医学', 'Clinical Medicine', '临床医学',
                                        'Internal Medicine', 'Surgery', 'Pediatrics']
                    },
                    '护理学': {
                        'keywords': ['nursing', '护理', 'nurse', 'healthcare', 'patient care',
                                   'clinical nursing', 'community health', 'nursing science'],
                        'exact_matches': ['Nursing', '护理学', 'Nursing Science', '护理科学',
                                        'Clinical Nursing', 'Community Health Nursing']
                    },
                    '药学': {
                        'keywords': ['pharmacy', 'pharmaceutical', '药学', '制药', 'pharmacology',
                                   'drug development', 'medicinal chemistry', 'clinical pharmacy'],
                        'exact_matches': ['Pharmacy', '药学', 'Pharmaceutical Sciences', '药物科学',
                                        'Pharmacology', 'Clinical Pharmacy']
                    },
                    '公共卫生': {
                        'keywords': ['public health', '公共卫生', 'health', 'epidemiology', 'health policy',
                                   'environmental health', 'health promotion', 'global health'],
                        'exact_matches': ['Public Health', '公共卫生', 'Health Sciences', '健康科学',
                                        'Epidemiology', 'Health Policy', 'Global Health']
                    },
                    '口腔医学': {
                        'keywords': ['dentistry', 'dental', '口腔', '牙科', 'oral health',
                                   'orthodontics', 'oral surgery', 'dental hygiene'],
                        'exact_matches': ['Dentistry', '口腔医学', 'Dental Sciences', '牙科学',
                                        'Oral Health', 'Orthodontics']
                    }
                }
            }
        }
    
    def _build_name_mapping(self) -> Dict[str, str]:
        """构建专业名称映射字典（标准化名称）"""
        return {
            # 商科相关
            'commerce': 'Commerce',
            'business': 'Business',
            'mba': 'MBA',
            'master of business administration': 'MBA',
            'master of commerce': 'Master of Commerce',
            'bachelor of commerce': 'Bachelor of Commerce',
            'master of business': 'Master of Business',
            'business administration': 'Business Administration',
            'international business': 'International Business',
            'global business': 'Global Business',
            
            # 金融相关
            'finance': 'Finance',
            'financial management': 'Financial Management',
            'financial engineering': 'Financial Engineering',
            'master of finance': 'Master of Finance',
            'banking': 'Banking',
            'investment': 'Investment',
            
            # 会计相关
            'accounting': 'Accounting',
            'professional accounting': 'Professional Accounting',
            'master of professional accounting': 'Master of Professional Accounting',
            'accountancy': 'Accountancy',
            
            # 经济学相关
            'economics': 'Economics',
            'master of economics': 'Master of Economics',
            'international economics and trade': 'International Economics and Trade',
            'applied economics': 'Applied Economics',
            
            # 市场营销相关
            'marketing': 'Marketing',
            'digital marketing': 'Digital Marketing',
            'brand management': 'Brand Management',
            
            # 管理相关
            'management': 'Management',
            'project management': 'Project Management',
            'master of management': 'Master of Management',
            'master of project management': 'Master of Project Management',
            'human resource management': 'Human Resource Management',
            'strategic management': 'Strategic Management',
            
            # 法学相关
            'law': 'Law',
            'laws': 'Law',
            'master of laws': 'Master of Laws',
            'juris doctor': 'Juris Doctor',
            'business law': 'Business Law',
            'master of business law': 'Master of Business Law',
            'legal studies': 'Legal Studies',
            
            # 工科相关
            'computer science': 'Computer Science',
            'master of computer science': 'Master of Computer Science',
            'computer science and technology': 'Computer Science and Technology',
            'software engineering': 'Software Engineering',
            'information technology': 'Information Technology',
            'master of information technology': 'Master of Information Technology',
            'data science': 'Data Science',
            'master of data science': 'Master of Data Science',
            'engineering': 'Engineering',
            'master of engineering': 'Master of Engineering',
            'electrical engineering': 'Electrical Engineering',
            'mechanical engineering': 'Mechanical Engineering',
            'civil engineering': 'Civil Engineering',
            'chemical engineering': 'Chemical Engineering',
            
            # 理科相关
            'mathematics': 'Mathematics',
            'mathematics and applied mathematics': 'Mathematics and Applied Mathematics',
            'statistics': 'Statistics',
            'physics': 'Physics',
            'chemistry': 'Chemistry',
            'biology': 'Biology',
            'psychology': 'Psychology',
            'applied psychology': 'Applied Psychology',
            
            # 文科相关
            'english': 'English',
            'education': 'Education',
            'master of education': 'Master of Education',
            'tesol': 'TESOL',
            'master of tesol': 'Master of TESOL',
            'journalism': 'Journalism',
            'media': 'Media',
            'communication': 'Communication',
            'media practice': 'Media Practice',
            'master of media practice': 'Master of Media Practice',
            'digital communication and culture': 'Digital Communication and Culture',
            'master of digital communication and culture': 'Master of Digital Communication and Culture',
            'strategic public relations': 'Strategic Public Relations',
            'master of strategic public relations': 'Master of Strategic Public Relations',
            'literature': 'Literature',
            'chinese language and literature': 'Chinese Language and Literature',
            'business english': 'Business English',
            
            # 艺术相关
            'design': 'Design',
            'visual communication design': 'Visual Communication Design',
            'interaction design and electronic arts': 'Interaction Design and Electronic Arts',
            'master of interaction design and electronic arts': 'Master of Interaction Design and Electronic Arts',
            'architecture': 'Architecture',
            'environmental design': 'Environmental Design',
            'art': 'Art',
            'fine arts': 'Fine Arts',
            'music': 'Music',
            'film': 'Film',
            'animation': 'Animation',
            
            # 医学相关
            'medicine': 'Medicine',
            'nursing': 'Nursing',
            'pharmacy': 'Pharmacy',
            'public health': 'Public Health',
            'health': 'Health',
            'medical': 'Medical',
            'clinical': 'Clinical',
            
            # 其他
            'science': 'Science',
            'bachelor of science': 'Bachelor of Science',
            'master of science': 'Master of Science',
            'bachelor of arts': 'Bachelor of Arts',
            'master of arts': 'Master of Arts',
            
            # 中文专业名称
            '金融学': 'Finance',
            '会计学': 'Accounting',
            '工商管理': 'Business Administration',
            '市场营销': 'Marketing',
            '国际经济与贸易': 'International Economics and Trade',
            '经济学': 'Economics',
            '法学': 'Law',
            '计算机科学与技术': 'Computer Science and Technology',
            '软件工程': 'Software Engineering',
            '电气工程及其自动化': 'Electrical Engineering and Automation',
            '机械工程': 'Mechanical Engineering',
            '土木工程': 'Civil Engineering',
            '英语': 'English',
            '汉语言文学': 'Chinese Language and Literature',
            '新闻学': 'Journalism',
            '广告学': 'Advertising',
            '教育学': 'Education',
            '心理学': 'Psychology',
            '数学与应用数学': 'Mathematics and Applied Mathematics',
            '物理学': 'Physics',
            '化学': 'Chemistry',
            '生物学': 'Biology',
            '建筑学': 'Architecture',
            '艺术设计': 'Art Design',
            '音乐学': 'Music',
            '医学': 'Medicine',
            '护理学': 'Nursing',
            '药学': 'Pharmacy'
        }
    
    def _build_keyword_weights(self) -> Dict[str, float]:
        """构建关键词权重字典"""
        return {
            # 高权重关键词（专业名称核心词）
            'finance': 2.0, 'accounting': 2.0, 'law': 2.0, 'medicine': 2.0,
            'engineering': 2.0, 'computer': 2.0, 'business': 2.0, 'management': 2.0,
            'design': 2.0, 'education': 2.0, 'psychology': 2.0, 'mathematics': 2.0,
            
            # 中等权重关键词（学科相关词）
            'master': 1.5, 'bachelor': 1.5, 'science': 1.5, 'arts': 1.5,
            'technology': 1.5, 'studies': 1.5, 'research': 1.5,
            
            # 低权重关键词（修饰词）
            'applied': 1.0, 'international': 1.0, 'advanced': 1.0, 'professional': 1.0,
            'strategic': 1.0, 'digital': 1.0, 'modern': 1.0, 'contemporary': 1.0
        }
    
    def standardize_major_name(self, major_name: str) -> str:
        """标准化专业名称"""
        if pd.isna(major_name) or not major_name:
            return ''
        
        # 转换为字符串并清理
        major_name = str(major_name).strip()
        
        # 移除多余空格和特殊字符
        major_name = re.sub(r'\s+', ' ', major_name)
        major_name = re.sub(r'[^\w\s\-&/()]', '', major_name)
        
        # 转换为小写进行匹配
        major_lower = major_name.lower()
        
        # 尝试精确匹配映射表
        if major_lower in self.name_mapping:
            return self.name_mapping[major_lower]
        
        # 尝试部分匹配
        for key, value in self.name_mapping.items():
            if key in major_lower or major_lower in key:
                return value
        
        # 如果没有匹配，返回标题格式的原名称
        return major_name.title()
    
    def _calculate_match_score(self, major_name: str, category_info: Dict) -> float:
        """计算专业名称与分类的匹配分数"""
        if pd.isna(major_name) or not major_name:
            return 0.0
        
        major_lower = str(major_name).lower()
        score = 0.0
        
        # 检查精确匹配
        if 'exact_matches' in category_info:
            for exact_match in category_info['exact_matches']:
                if exact_match.lower() == major_lower:
                    return 10.0  # 精确匹配最高分
                if exact_match.lower() in major_lower or major_lower in exact_match.lower():
                    score += 5.0
        
        # 检查关键词匹配
        if 'keywords' in category_info:
            for keyword in category_info['keywords']:
                if keyword.lower() in major_lower:
                    # 使用权重计算分数
                    weight = self.keyword_weights.get(keyword.lower(), 1.0)
                    # 完整词匹配得更高分
                    if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', major_lower):
                        score += 2.0 * weight
                    else:
                        score += 1.0 * weight
        
        return score
    
    def classify_major(self, major_name: str, return_subcategory: bool = True) -> Tuple[str, str, float]:
        """
        分类专业
        
        Args:
            major_name: 专业名称
            return_subcategory: 是否返回子分类
        
        Returns:
            (主分类, 子分类, 置信度分数)
        """
        if pd.isna(major_name) or not major_name:
            return ('未知', '未知', 0.0)
        
        # 标准化专业名称
        standardized_name = self.standardize_major_name(major_name)
        
        best_category = '其他'
        best_subcategory = '其他'
        best_score = 0.0
        
        # 遍历所有分类
        for main_category, main_info in self.major_hierarchy.items():
            if 'subcategories' in main_info:
                for subcategory, sub_info in main_info['subcategories'].items():
                    score = self._calculate_match_score(standardized_name, sub_info)
                    if score > best_score:
                        best_score = score
                        best_category = main_category
                        best_subcategory = subcategory
        
        # 如果分数太低，标记为其他
        if best_score < 1.0:
            best_category = '其他'
            best_subcategory = '其他'
        
        if return_subcategory:
            return (best_category, best_subcategory, best_score)
        else:
            return (best_category, '', best_score)
    
    def classify_dataframe(self, df: pd.DataFrame, 
                          target_column: str = '申请院校_专业名称',
                          education_column: str = '教育经历_所学专业') -> pd.DataFrame:
        """
        对DataFrame中的专业进行分类
        
        Args:
            df: 数据框
            target_column: 申请专业列名
            education_column: 教育专业列名
        
        Returns:
            添加了分类列的数据框
        """
        df_result = df.copy()
        
        # 分类申请专业
        if target_column in df_result.columns:
            classifications = df_result[target_column].apply(
                lambda x: self.classify_major(x, return_subcategory=True)
            )
            df_result['申请专业主分类'] = [c[0] for c in classifications]
            df_result['申请专业子分类'] = [c[1] for c in classifications]
            df_result['申请专业分类置信度'] = [c[2] for c in classifications]
        
        # 分类教育专业
        if education_column in df_result.columns:
            classifications = df_result[education_column].apply(
                lambda x: self.classify_major(x, return_subcategory=True)
            )
            df_result['教育专业主分类'] = [c[0] for c in classifications]
            df_result['教育专业子分类'] = [c[1] for c in classifications]
            df_result['教育专业分类置信度'] = [c[2] for c in classifications]
        
        logger.info(f"专业分类完成，处理了 {len(df_result)} 条记录")
        return df_result
    
    def get_category_statistics(self, df: pd.DataFrame) -> Dict:
        """获取分类统计信息"""
        stats = {}
        
        # 申请专业统计
        if '申请专业主分类' in df.columns:
            stats['申请专业主分类统计'] = df['申请专业主分类'].value_counts().to_dict()
            stats['申请专业子分类统计'] = df['申请专业子分类'].value_counts().to_dict()
            
            # 平均置信度
            if '申请专业分类置信度' in df.columns:
                stats['申请专业平均置信度'] = df['申请专业分类置信度'].mean()
        
        # 教育专业统计
        if '教育专业主分类' in df.columns:
            stats['教育专业主分类统计'] = df['教育专业主分类'].value_counts().to_dict()
            stats['教育专业子分类统计'] = df['教育专业子分类'].value_counts().to_dict()
            
            # 平均置信度
            if '教育专业分类置信度' in df.columns:
                stats['教育专业平均置信度'] = df['教育专业分类置信度'].mean()
        
        return stats
    
    def get_low_confidence_majors(self, df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
        """获取低置信度的专业分类结果，用于人工审核"""
        low_confidence_rows = []
        
        # 检查申请专业
        if '申请专业分类置信度' in df.columns:
            mask = df['申请专业分类置信度'] < threshold
            if mask.any():
                cols = ['申请院校_专业名称', '申请专业主分类', '申请专业子分类', '申请专业分类置信度']
                low_confidence_rows.append(df[mask][cols].copy())
        
        # 检查教育专业
        if '教育专业分类置信度' in df.columns:
            mask = df['教育专业分类置信度'] < threshold
            if mask.any():
                cols = ['教育经历_所学专业', '教育专业主分类', '教育专业子分类', '教育专业分类置信度']
                low_confidence_rows.append(df[mask][cols].copy())
        
        if low_confidence_rows:
            result = pd.concat(low_confidence_rows, ignore_index=True)
            return result.drop_duplicates()
        else:
            return pd.DataFrame()


def main():
    """测试和演示功能"""
    # 创建分类系统
    classifier = MajorClassificationSystem()
    
    # 测试一些专业名称
    test_majors = [
        'Master of Commerce',
        'Computer Science',
        'Master of Laws',
        'Information Technology',
        'Business Administration',
        'Software Engineering',
        'Master of Education',
        'Finance',
        'Digital Communication and Culture',
        '金融学',
        '计算机科学与技术',
        '法学',
        'Unknown Major'
    ]
    
    print("专业分类测试:")
    print("=" * 80)
    for major in test_majors:
        main_cat, sub_cat, score = classifier.classify_major(major)
        print(f"{major:40} -> {main_cat:10} | {sub_cat:15} | 置信度: {score:.2f}")


if __name__ == "__main__":
    main()