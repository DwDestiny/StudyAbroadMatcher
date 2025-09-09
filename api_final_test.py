#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys

class APITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.success_count = 0
        self.fail_count = 0
    
    def log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_api_endpoint(self, endpoint, payload, expected_status=200, test_name=""):
        """测试API端点的通用方法"""
        self.log(f"开始测试: {test_name}")
        
        try:
            response = requests.post(f"{self.base_url}{endpoint}", 
                                   json=payload, 
                                   timeout=10)
            
            if response.status_code == expected_status:
                result = response.json() if response.content else {}
                self.log(f"PASS {test_name} - 状态码: {response.status_code}", "PASS")
                if result.get('success'):
                    self.log(f"   匹配度: {result.get('match_score', 'N/A')}分", "INFO")
                else:
                    self.log(f"   错误信息: {result.get('error', 'Unknown')}", "INFO")
                self.success_count += 1
                return True, result
            else:
                self.log(f"FAIL {test_name} - 期望状态码: {expected_status}, 实际: {response.status_code}", "FAIL")
                self.log(f"   响应: {response.text[:200]}...", "FAIL")
                self.fail_count += 1
                return False, None
                
        except requests.exceptions.Timeout:
            self.log(f"FAIL {test_name} - 请求超时", "FAIL")
            self.fail_count += 1
            return False, None
        except Exception as e:
            self.log(f"FAIL {test_name} - 异常: {str(e)}", "FAIL")
            self.fail_count += 1
            return False, None
    
    def test_id_based_matching(self):
        """测试ID基础的专业匹配API"""
        self.log("=== 测试ID基础专业匹配 ===")
        
        # 测试1: 使用有效的ID参数
        success, result = self.test_api_endpoint(
            "/api/match/student",
            {
                "university_id": 32,              # The University of Sydney
                "target_major_id": 157073,        # 数据充足的专业ID
                "gpa": 3.7,
                "current_major": "计算机科学"
            },
            test_name="有效ID匹配测试"
        )
        
        # 测试2: 使用数据不足的ID（应快速返回错误）
        start_time = time.time()
        success, result = self.test_api_endpoint(
            "/api/match/student",
            {
                "university_id": 999999,          # 不存在的院校ID
                "target_major_id": 999999,        # 不存在的专业ID
                "gpa": 3.5,
                "current_major": "经济学"
            },
            expected_status=400,
            test_name="数据不足快速响应测试"
        )
        response_time = time.time() - start_time
        if response_time < 2.0:
            self.log(f"PASS 快速响应测试通过 - 响应时间: {response_time:.3f}秒", "PASS")
        else:
            self.log(f"FAIL 响应时间过长: {response_time:.3f}秒", "FAIL")
        
        # 测试3: 名称回退机制
        success, result = self.test_api_endpoint(
            "/api/match/student",
            {
                "university": "The University of Sydney",
                "target_major": "Master of Commerce",
                "gpa": 3.6,
                "current_major": "商科"
            },
            expected_status=400,  # 可能数据不足
            test_name="名称回退机制测试"
        )
    
    def test_recommendation_api(self):
        """测试推荐API功能"""
        self.log("=== 测试推荐API ===")
        
        # 测试1: 使用ID进行推荐
        success, result = self.test_api_endpoint(
            "/api/recommend/student",
            {
                "university_id": 32,
                "gpa": 3.7,
                "current_major": "计算机科学",
                "top_n": 3
            },
            test_name="ID基础推荐测试"
        )
        
        # 测试2: 使用名称进行推荐
        success, result = self.test_api_endpoint(
            "/api/recommend/student",
            {
                "university": "北京大学",
                "gpa": 3.8,
                "current_major": "数学",
                "top_n": 5
            },
            test_name="名称基础推荐测试"
        )
    
    def test_error_handling(self):
        """测试错误处理机制"""
        self.log("=== 测试错误处理 ===")
        
        # 测试1: 缺少必要参数
        success, result = self.test_api_endpoint(
            "/api/match/student",
            {
                "gpa": 3.5
                # 缺少target_major_id和target_major
            },
            expected_status=400,
            test_name="缺少必要参数测试"
        )
        
        # 测试2: 无效的JSON格式
        try:
            response = requests.post(f"{self.base_url}/api/match/student", 
                                   data="invalid json", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=5)
            if response.status_code == 400:
                self.log("PASS 无效JSON处理测试通过", "PASS")
                self.success_count += 1
            else:
                self.log(f"FAIL 无效JSON处理失败 - 状态码: {response.status_code}", "FAIL")
                self.fail_count += 1
        except Exception as e:
            self.log(f"FAIL 无效JSON测试异常: {str(e)}", "FAIL")
            self.fail_count += 1
    
    def test_auxiliary_endpoints(self):
        """测试辅助端点"""
        self.log("=== 测试辅助端点 ===")
        
        # 测试系统状态
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                self.log(f"PASS 系统状态API - 运行时间: {status.get('uptime_seconds', 'N/A')}秒", "PASS")
                self.success_count += 1
            else:
                self.log(f"FAIL 系统状态API失败", "FAIL") 
                self.fail_count += 1
        except Exception as e:
            self.log(f"FAIL 系统状态API异常: {str(e)}", "FAIL")
            self.fail_count += 1
        
        # 测试专业列表
        try:
            response = requests.get(f"{self.base_url}/api/majors", timeout=5)
            if response.status_code == 200:
                majors = response.json()
                self.log(f"PASS 专业列表API - 支持专业数: {len(majors.get('majors', []))}", "PASS")
                self.success_count += 1
            else:
                self.log(f"FAIL 专业列表API失败", "FAIL")
                self.fail_count += 1
        except Exception as e:
            self.log(f"FAIL 专业列表API异常: {str(e)}", "FAIL")
            self.fail_count += 1
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始API全面测试")
        start_time = time.time()
        
        # 等待服务器完全启动
        self.log("等待API服务器响应...")
        for i in range(10):
            try:
                response = requests.get(f"{self.base_url}/api/status", timeout=2)
                if response.status_code == 200:
                    self.log("API服务器已就绪")
                    break
            except:
                time.sleep(1)
        else:
            self.log("FAIL API服务器无响应，测试中止", "FAIL")
            return
        
        # 执行所有测试
        self.test_id_based_matching()
        self.test_recommendation_api() 
        self.test_error_handling()
        self.test_auxiliary_endpoints()
        
        # 测试结果汇总
        total_time = time.time() - start_time
        total_tests = self.success_count + self.fail_count
        
        self.log("=" * 50)
        self.log(f"测试完成 - 总用时: {total_time:.2f}秒")
        self.log(f"总测试数: {total_tests}")
        self.log(f"成功: {self.success_count} | 失败: {self.fail_count}")
        self.log(f"成功率: {(self.success_count/total_tests*100):.1f}%" if total_tests > 0 else "成功率: 0%")
        
        if self.fail_count == 0:
            self.log("SUCCESS 所有测试通过！API系统运行正常", "SUCCESS")
            return True
        else:
            self.log(f"WARNING 有{self.fail_count}个测试失败", "WARNING")
            return False

def main():
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()