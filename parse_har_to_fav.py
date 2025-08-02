#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 HAR 文件中的抖音点赞作品数据
从 all.json (HAR格式) 中提取点赞作品信息并保存到 fav.json
"""

import json
import os
from typing import Dict, List, Any

def parse_har_file(har_file_path: str) -> List[Dict[str, Any]]:
    """
    解析 HAR 文件，提取抖音点赞作品数据
    
    Args:
        har_file_path: HAR 文件路径
        
    Returns:
        提取的作品列表
    """
    print(f"正在解析 HAR 文件: {har_file_path}")
    
    with open(har_file_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    aweme_list = []
    
    # 遍历 HAR 文件中的所有网络请求
    if 'log' in har_data and 'entries' in har_data['log']:
        for entry in har_data['log']['entries']:
            # 检查是否是抖音点赞接口的请求
            if 'request' in entry and 'url' in entry['request']:
                url = entry['request']['url']
                if '/aweme/v1/web/aweme/favorite/' in url:
                    print(f"找到点赞接口请求: {url[:100]}...")
                    
                    # 检查响应数据
                    if 'response' in entry:
                        response = entry['response']
                        print(f"响应状态码: {response.get('status', 'unknown')}")
                        
                        if 'content' in response:
                            response_content = response['content']
                            print(f"响应内容类型: {response_content.get('mimeType', 'unknown')}")
                            
                            if 'text' in response_content:
                                response_text = response_content['text']
                                print(f"响应文本长度: {len(response_text)}")
                                
                                try:
                                    # 解析响应 JSON 数据
                                    response_data = json.loads(response_text)
                                    print(f"响应数据键: {list(response_data.keys())}")
                                    
                                    # 提取 aweme_list
                                    if 'aweme_list' in response_data:
                                        current_aweme_list = response_data['aweme_list']
                                        print(f"找到 {len(current_aweme_list)} 个作品")
                                        aweme_list.extend(current_aweme_list)
                                    else:
                                        print("响应中未找到 aweme_list 字段")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"解析响应 JSON 失败: {e}")
                                    print(f"响应文本前100字符: {response_text[:100]}")
                                    continue
                            else:
                                print("响应内容中没有 text 字段")
                        else:
                            print("响应中没有 content 字段")
                    else:
                        print("请求条目中没有 response 字段")
    
    print(f"总共提取到 {len(aweme_list)} 个作品")
    return aweme_list

def save_fav_json(aweme_list: List[Dict[str, Any]], output_path: str):
    """
    保存作品列表到 fav.json 文件
    
    Args:
        aweme_list: 作品列表
        output_path: 输出文件路径
    """
    # 去重，基于 aweme_id
    unique_awemes = {}
    for aweme in aweme_list:
        if 'aweme_id' in aweme:
            aweme_id = aweme['aweme_id']
            if aweme_id not in unique_awemes:
                unique_awemes[aweme_id] = aweme
    
    final_aweme_list = list(unique_awemes.values())
    print(f"去重后剩余 {len(final_aweme_list)} 个作品")
    
    # 构造输出数据结构
    output_data = {
        "status_code": 0,
        "aweme_list": final_aweme_list,
        "max_cursor": 0,
        "min_cursor": 0,
        "has_more": False,
        "total": len(final_aweme_list)
    }
    
    # 保存到文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存到: {output_path}")

def main():
    """
    主函数
    """
    # 输入和输出文件路径
    input_file = "d:/github/MediaCrawler/data/douyin/fav/all.json"
    output_file = "d:/github/MediaCrawler/data/douyin/fav/fav.json"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 {input_file}")
        return
    
    try:
        # 解析 HAR 文件
        aweme_list = parse_har_file(input_file)
        
        if not aweme_list:
            print("警告: 未找到任何作品数据")
            return
        
        # 保存到 fav.json
        save_fav_json(aweme_list, output_file)
        
        print("\n解析完成!")
        print(f"输入文件: {input_file}")
        print(f"输出文件: {output_file}")
        print(f"作品数量: {len(aweme_list)}")
        
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()