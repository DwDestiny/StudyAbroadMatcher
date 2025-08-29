import requests
import json
import time
import pickle
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VolcanoLLMUniversityNormalizer:
    """
    基于火山引擎豆包1.6模型的院校名称标准化器
    支持OpenAI格式和REST API两种调用方式
    """
    
    def __init__(self, api_key: str, model_id: str = "doubao-seed-1-6-250615", 
                 cache_file: str = "university_normalization_cache.pkl",
                 use_openai_format: bool = True):
        """
        初始化LLM标准化器
        
        Args:
            api_key: 火山引擎API密钥
            model_id: 模型ID
            cache_file: 缓存文件路径
            use_openai_format: 是否使用OpenAI格式调用
        """
        self.api_key = api_key
        self.model_id = model_id
        self.use_openai_format = use_openai_format
        
        # 设置API端点
        if use_openai_format:
            self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
            self.endpoint = f"{self.base_url}/chat/completions"
        else:
            self.base_url = "https://open.volcengineapi.com"
            self.endpoint = f"{self.base_url}/api/v1/chat/completions"
        
        # 缓存设置
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        
        # API调用配置
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 30
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def _load_cache(self) -> Dict[str, str]:
        """加载缓存文件"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                logger.info(f"已加载缓存，包含 {len(cache)} 条记录")
                return cache
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}，将创建新缓存")
        return {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
            logger.info(f"缓存已保存，包含 {len(self.cache)} 条记录")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        if self.use_openai_format:
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        else:
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
    
    def _build_prompt(self, university_name: str) -> str:
        """构建标准化提示词"""
        prompt = f"""请将以下院校名称标准化为中国教育部认可的正式院校名称。

输入院校名称：{university_name}

要求：
1. 如果是中国大陆院校，返回教育部官方标准名称
2. 如果是港澳台院校，返回当地官方名称  
3. 如果是海外院校，返回"海外院校：[英文官方名称]"
4. 如果无法识别，返回"无法识别"
5. 只返回标准化后的院校名称，不要其他解释

示例：
- "上海外国语大学（211）" → "上海外国语大学"
- "山东大学（威海）" → "山东大学"
- "University of Sydney" → "海外院校：University of Sydney"
- "北京大学医学部" → "北京大学"
- "清华大学(Tsinghua University)" → "清华大学"

请直接返回标准化后的院校名称："""
        return prompt
    
    def _call_api(self, university_name: str) -> Optional[str]:
        """调用API获取标准化结果"""
        prompt = self._build_prompt(university_name)
        
        if self.use_openai_format:
            payload = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
        else:
            payload = {
                "model": self.model_id,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
        
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content'].strip()
                        logger.info(f"API调用成功: {university_name} → {content}")
                        return content
                    else:
                        logger.error(f"API响应格式错误: {result}")
                        return None
                        
                else:
                    logger.error(f"API调用失败，状态码: {response.status_code}, 响应: {response.text}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        return None
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
        
        return None
    
    def normalize_university_name(self, university_name: str) -> str:
        """
        标准化院校名称
        
        Args:
            university_name: 原始院校名称
            
        Returns:
            标准化后的院校名称
        """
        if not university_name or university_name.strip() == "":
            return "无法识别"
        
        university_name = university_name.strip()
        self.stats['total_requests'] += 1
        
        # 检查缓存
        if university_name in self.cache:
            self.stats['cache_hits'] += 1
            logger.debug(f"缓存命中: {university_name} → {self.cache[university_name]}")
            return self.cache[university_name]
        
        # 调用API
        self.stats['api_calls'] += 1
        result = self._call_api(university_name)
        
        if result:
            # 缓存结果
            self.cache[university_name] = result
            
            # 定期保存缓存
            if len(self.cache) % 10 == 0:
                self._save_cache()
                
            return result
        else:
            self.stats['errors'] += 1
            logger.error(f"标准化失败: {university_name}")
            return "无法识别"
    
    def batch_normalize(self, university_names: list) -> Dict[str, str]:
        """
        批量标准化院校名称
        
        Args:
            university_names: 院校名称列表
            
        Returns:
            原始名称到标准化名称的映射字典
        """
        results = {}
        total = len(university_names)
        
        logger.info(f"开始批量标准化 {total} 个院校名称")
        
        for i, name in enumerate(university_names, 1):
            if i % 10 == 0 or i == total:
                logger.info(f"进度: {i}/{total} ({i/total*100:.1f}%)")
            
            results[name] = self.normalize_university_name(name)
            
            # 避免API调用过于频繁
            if i % 5 == 0:
                time.sleep(0.5)
        
        # 保存最终缓存
        self._save_cache()
        
        logger.info(f"批量标准化完成，统计信息: {self.get_stats()}")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats['total_requests'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_requests'] * 100
        else:
            stats['cache_hit_rate'] = 0
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("缓存已清空")
    
    def __del__(self):
        """析构函数，确保缓存被保存"""
        if hasattr(self, 'cache') and self.cache:
            self._save_cache()


if __name__ == "__main__":
    # 测试代码
    api_key = "659fe68f-6edb-4936-9364-e6267be54ea1"
    model_id = "doubao-seed-1-6-250615"
    
    normalizer = VolcanoLLMUniversityNormalizer(api_key, model_id)
    
    # 测试单个标准化
    test_names = [
        "上海外国语大学（211）",
        "山东大学（威海）",
        "University of Sydney",
        "北京大学医学部",
        "清华大学(Tsinghua University)"
    ]
    
    print("=== 单个测试 ===")
    for name in test_names:
        result = normalizer.normalize_university_name(name)
        print(f"{name} → {result}")
    
    print(f"\n=== 统计信息 ===")
    print(normalizer.get_stats())