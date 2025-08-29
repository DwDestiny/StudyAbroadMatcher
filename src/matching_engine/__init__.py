"""
匹配引擎模块
包含专业路径聚类分析、路径画像构建、匹配度计算的完整功能
"""

from .clustering_analysis import ProfessionalPathClustering
from .path_profile_builder import PathProfileBuilder  
from .matching_calculator import MatchingCalculator
from .matching_system import StudentMajorMatchingSystem

__all__ = [
    'ProfessionalPathClustering',
    'PathProfileBuilder', 
    'MatchingCalculator',
    'StudentMajorMatchingSystem'
]

__version__ = '1.0.0'