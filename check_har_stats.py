#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查HAR文件解析统计信息
"""

import json
import os
from typing import List, Dict, Any

def parse_har_file_stats_only(har_file_path: str) -> Dict[str, int]:
    """
    只解析HAR文件统计信息，不返回具体数据
    """
    stats = {
        'total_entries': 0,
        'favorite_requests': 0,
        'successful_responses': 0,
        'total_awemes': 0
    }
    
    try:
        with open(har_file_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except Exception as e:
        print(f"❌ 读取HAR文件失败: {e}")
        return stats
    
    print(f"📁 HAR文件读取成功: {har_file_path}")
    
    # 遍历 HAR 文件中的所有网络请求
    if 'log' in har_data and 'entries' in har_data['log']:
        stats['total_entries'] = len(har_data['log']['entries'])
        print(f"📊 HAR文件包含 {stats['total_entries']} 个网络请求")
        
        for i, entry in enumerate(har_data['log']['entries']):
            # 检查是否是抖音点赞接口的请求
            if 'request' in entry and 'url' in entry['request']:
                url = entry['request']['url']
                if '/aweme/v1/web/aweme/favorite/' in url:
                    stats['favorite_requests'] += 1
                    print(f"🔍 [{stats['favorite_requests']}] 找到点赞接口请求 (第{i+1}个请求)")
                    
                    # 检查响应数据
                    if 'response' in entry:
                        response = entry['response']
                        status = response.get('status', 'unknown')
                        
                        if status == 200 and 'content' in response:
                            response_content = response['content']
                            encoding = response_content.get('encoding', '')
                            
                            if 'text' in response_content:
                                response_text = response_content['text']
                                
                                # 如果是base64编码，需要解码
                                if encoding == 'base64':
                                    try:
                                        import base64
                                        response_text = base64.b64decode(response_text).decode('utf-8')
                                    except Exception as e:
                                        print(f"❌ Base64解码失败: {e}")
                                        continue
                                
                                # 尝试解析JSON
                                try:
                                    response_data = json.loads(response_text)
                                    
                                    # 提取 aweme_list
                                    if 'aweme_list' in response_data:
                                        current_aweme_list = response_data['aweme_list']
                                        aweme_count = len(current_aweme_list)
                                        print(f"   ✅ 找到 {aweme_count} 个作品")
                                        stats['total_awemes'] += aweme_count
                                        stats['successful_responses'] += 1
                                        
                                        # 打印分页信息
                                        if 'has_more' in response_data:
                                            print(f"   📄 has_more: {response_data['has_more']}")
                                        if 'max_cursor' in response_data:
                                            print(f"   📄 max_cursor: {response_data['max_cursor']}")
                                    else:
                                        print(f"   ⚠️  响应中未找到 aweme_list 字段")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"   ❌ JSON解析失败: {e}")
                                    continue
    else:
        print("❌ HAR文件格式不正确，缺少 log.entries 字段")
    
    return stats

def main():
    # 尝试多个可能的 HAR 文件路径
    har_file_paths = [
        "d:\\github\\MediaCrawler\\data\\douyin\\fav\\www.douyin.com.har",
        "d:\\github\\MediaCrawler\\data\\douyin\\fav\\all.json"
    ]
    
    har_file_path = None
    for path in har_file_paths:
        if os.path.exists(path):
            har_file_path = path
            break
    
    if not har_file_path:
        print(f"❌ 未找到 HAR 文件，检查了以下路径:")
        for path in har_file_paths:
            print(f"   - {path}")
        return
    
    print("🚀 开始解析HAR文件统计信息")
    print("=" * 60)
    
    stats = parse_har_file_stats_only(har_file_path)
    
    print("\n" + "=" * 60)
    print(f"📊 最终解析统计:")
    print(f"   📁 总请求数: {stats['total_entries']}")
    print(f"   🔍 点赞接口请求数: {stats['favorite_requests']}")
    print(f"   ✅ 成功解析响应数: {stats['successful_responses']}")
    print(f"   🎯 总共提取作品数: {stats['total_awemes']}")
    print("=" * 60)

if __name__ == "__main__":
    main()