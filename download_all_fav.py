#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载抖音点赞作品媒体文件
使用修复后的存储逻辑，确保所有作品都有描述性文件夹名称和JSON信息文件
"""

import asyncio
import json
import sys
import os
import requests
from typing import List, Dict
from urllib.parse import urlparse
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import store.douyin as douyin_store
from tools import utils

def sanitize_folder_name(title: str, aweme_id: str) -> str:
    """
    快速清理文件夹名称，与存储类逻辑保持一致
    """
    import re
    invalid_chars = '<>:"/\\|?*'
    folder_name = title
    for char in invalid_chars:
        folder_name = folder_name.replace(char, '_')
    folder_name = folder_name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    folder_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', folder_name)
    folder_name = re.sub(r'\s+', ' ', folder_name)
    folder_name = re.sub(r'_+', '_', folder_name)
    if len(folder_name) > 80:
        folder_name = folder_name[:80]
    folder_name = folder_name.strip(' _')
    if not folder_name:
        folder_name = aweme_id
    return folder_name

def parse_har_file(har_file_path: str) -> List[Dict]:
    """
    解析 HAR 文件，提取抖音点赞作品数据
    
    Args:
        har_file_path: HAR 文件路径
        
    Returns:
        提取的作品列表
    """
    aweme_list = []
    total_entries = 0
    processed_requests = 0
    successful_responses = 0
    
    try:
        with open(har_file_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except Exception as e:
        print(f"❌ 读取HAR文件失败: {e}")
        return aweme_list
    
    print(f"📁 HAR文件读取成功: {har_file_path}")
    
    # 遍历 HAR 文件中的所有网络请求
    if 'log' in har_data and 'entries' in har_data['log']:
        total_entries = len(har_data['log']['entries'])
        print(f"📊 HAR文件包含 {total_entries} 个网络请求")
        
        for i, entry in enumerate(har_data['log']['entries']):
            # 检查是否是抖音点赞接口的请求
            if 'request' in entry and 'url' in entry['request']:
                url = entry['request']['url']
                if '/aweme/v1/web/aweme/favorite/' in url:
                    processed_requests += 1
                    print(f"\n🔍 [{processed_requests}] 找到点赞接口请求 (第{i+1}个请求)")
                    print(f"🌐 URL: {url[:100]}...")
                    
                    # 检查响应数据
                    if 'response' in entry:
                        response = entry['response']
                        status = response.get('status', 'unknown')
                        print(f"📋 响应状态: {status}")
                        
                        if status != 200:
                            print(f"⚠️  响应状态非200，跳过")
                            continue
                        
                        if 'content' in response:
                            response_content = response['content']
                            mime_type = response_content.get('mimeType', 'unknown')
                            print(f"📄 内容类型: {mime_type}")
                            print(f"📊 内容字段: {list(response_content.keys())}")
                            
                            # 检查内容大小
                            if 'size' in response_content:
                                print(f"📏 内容大小: {response_content['size']} 字节")
                            
                            # 尝试从不同字段获取响应文本
                            response_text = None
                            encoding = response_content.get('encoding', '')
                            
                            if 'text' in response_content:
                                raw_text = response_content['text']
                                print(f"📝 找到 text 字段，长度: {len(raw_text)}，编码: {encoding}")
                                
                                if encoding == 'base64':
                                    # base64解码
                                    import base64
                                    try:
                                        response_text = base64.b64decode(raw_text).decode('utf-8')
                                        print(f"🔓 base64解码成功，解码后长度: {len(response_text)}")
                                    except Exception as e:
                                        print(f"❌ base64解码失败: {e}")
                                        continue
                                else:
                                    response_text = raw_text
                            else:
                                print("⚠️  未找到 text 字段")
                                # 打印所有字段以便调试
                                for key, value in response_content.items():
                                    if isinstance(value, str):
                                        print(f"   {key}: {value[:50]}...")
                                    else:
                                        print(f"   {key}: {type(value)} - {value}")
                                continue
                            
                            if response_text:
                                print(f"🔍 响应文本前100字符: {response_text[:100]}")
                                try:
                                    # 解析响应 JSON 数据
                                    response_data = json.loads(response_text)
                                    print(f"📊 响应数据键: {list(response_data.keys())}")
                                    
                                    # 提取 aweme_list
                                    if 'aweme_list' in response_data:
                                        current_aweme_list = response_data['aweme_list']
                                        print(f"✅ 找到 {len(current_aweme_list)} 个作品")
                                        aweme_list.extend(current_aweme_list)
                                        successful_responses += 1
                                        
                                        # 打印一些额外信息
                                        if 'has_more' in response_data:
                                            print(f"📄 has_more: {response_data['has_more']}")
                                        if 'max_cursor' in response_data:
                                            print(f"📍 max_cursor: {response_data['max_cursor']}")
                                    else:
                                        print("⚠️  响应中未找到 aweme_list 字段")
                                        print(f"   可用字段: {list(response_data.keys())}")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"❌ JSON解析失败: {e}")
                                    print(f"   响应文本开头: {response_text[:200]}")
                                    continue
                        else:
                            print("⚠️  响应中没有 content 字段")
                    else:
                        print("⚠️  请求中没有 response 字段")
    else:
        print("❌ HAR文件格式不正确，缺少 log.entries 字段")
    
    print(f"\n📊 解析统计:")
    print(f"   - 总请求数: {total_entries} 个")
    print(f"   - 找到点赞接口请求: {processed_requests} 个")
    print(f"   - 成功解析响应: {successful_responses} 个")
    print(f"   - 总共提取作品: {len(aweme_list)} 个")
    
    return aweme_list

async def main():
    """
    主函数：下载所有点赞作品
    """
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
    
    print("🚀 开始下载抖音点赞作品")
    print(f"📁 读取 HAR 文件: {har_file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(har_file_path):
        print(f"❌ 文件不存在: {har_file_path}")
        print("请确保已经获取到 all.json HAR 文件")
        return
    
    try:
        # 解析 HAR 文件获取作品列表
        all_aweme_list = parse_har_file(har_file_path)
        
        if not all_aweme_list:
            print("⚠️  没有找到点赞作品")
            return
        
        # 去重处理（基于aweme_id）
        seen_ids = set()
        unique_aweme_list = []
        for aweme_item in all_aweme_list:
            aweme_id = aweme_item.get('aweme_id')
            if aweme_id and aweme_id not in seen_ids:
                seen_ids.add(aweme_id)
                unique_aweme_list.append(aweme_item)
        
        if len(unique_aweme_list) != len(all_aweme_list):
            print(f"🔄 去重后剩余 {len(unique_aweme_list)} 个唯一作品")
        
        aweme_list = unique_aweme_list
        
        print("\n=== 开始下载媒体文件 ===")
        
        for i, aweme_item in enumerate(aweme_list, 1):
            try:
                aweme_id = aweme_item.get('aweme_id')
                author_name = aweme_item.get('author', {}).get('nickname', '未知作者')
                aweme_type = aweme_item.get('aweme_type', 0)
                title = aweme_item.get('title', aweme_item.get('desc', aweme_id))
                
                print(f"\n[{i}/{len(aweme_list)}] 处理作品: {aweme_id}")
                print(f"👤 作者: {author_name}")
                print(f"📝 标题: {title[:50]}..." if len(title) > 50 else f"📝 标题: {title}")
                print(f"🎬 类型: {'视频' if aweme_type == 0 else '图片集' if aweme_type == 68 else '未知'}")
                
                if aweme_type == 0:  # 视频
                    await download_video(aweme_item)
                elif aweme_type == 68:  # 图片
                    await download_images(aweme_item)
                else:
                    print(f"⚠️  未知作品类型: {aweme_type}")
                
                print(f"✅ 作品 {aweme_id} 处理完成")
                
                # 减少延时，跳过已存在文件时无需等待
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ 处理作品失败: {e}")
                continue
        
        print(f"\n🎉 所有媒体文件下载完成！")
        print(f"📂 文件保存位置: data/douyin/love/")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON文件格式错误: {e}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

async def download_video(aweme_item: Dict):
    """
    下载视频文件
    """
    aweme_id = aweme_item.get('aweme_id')
    title = aweme_item.get('title', aweme_item.get('desc', aweme_id))
    
    # 快速检查：如果视频文件已存在，直接跳过
    folder_name = sanitize_folder_name(title, aweme_id)
    
    # 检查视频文件是否已存在
    video_dir = os.path.join("data/douyin/love", folder_name)
    video_file = os.path.join(video_dir, f"{aweme_id}.mp4")
    json_file = os.path.join(video_dir, f"{aweme_id}.json")
    
    if os.path.exists(video_file) and os.path.exists(json_file):
        print(f"⏭️  视频 {aweme_id} 已存在，跳过下载")
        return
    
    video_info = aweme_item.get('video', {})
    play_addr = video_info.get('play_addr', {})
    video_urls = play_addr.get('url_list', [])
    
    if not video_urls:
        print(f"⚠️  视频 {aweme_id} 没有可用的下载链接")
        return
    
    video_url = video_urls[0]
    print(f"📹 下载视频: {aweme_id}")
    print(f"🔗 视频链接: {video_url[:80]}...")
    
    try:
        # 下载视频内容
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/'
        }
        
        response = requests.get(video_url, headers=headers, timeout=30)
        if response.status_code == 200:
            video_content = response.content
            file_size = len(video_content)
            print(f"📦 视频大小: {file_size / 1024 / 1024:.2f} MB")
            
            # 获取文件扩展名
            extension = '.mp4'  # 抖音视频通常是mp4格式
            
            # 保存视频文件
            await douyin_store.update_douyin_aweme_video_for_love(
                aweme_item=aweme_item,
                video_content=video_content,
                extension_file_name=f"{aweme_id}{extension}"
            )
            print(f"✅ 视频下载成功")
        else:
            print(f"❌ 视频下载失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 视频下载异常: {e}")

async def download_images(aweme_item: Dict):
    """
    下载图片文件
    """
    aweme_id = aweme_item.get('aweme_id')
    title = aweme_item.get('title', aweme_item.get('desc', aweme_id))
    images = aweme_item.get('images', [])
    
    if not images:
        print(f"⚠️  作品 {aweme_id} 没有图片")
        return
    
    # 快速检查：如果图片文件已存在，直接跳过
    folder_name = sanitize_folder_name(title, aweme_id)
    
    # 检查图片文件是否已存在
    image_dir = os.path.join("data/douyin/love", folder_name)
    json_file = os.path.join(image_dir, f"{aweme_id}.json")
    first_image_file = os.path.join(image_dir, f"{aweme_id}_1.webp")
    
    if os.path.exists(json_file) and os.path.exists(first_image_file):
        print(f"⏭️  图片集 {aweme_id} 已存在，跳过下载")
        return
    
    print(f"🖼️  下载图片集: {aweme_id} ({len(images)}张图片)")
    
    for idx, image_info in enumerate(images, 1):
        try:
            # 获取图片URL（优先使用高清版本）
            url_list = []
            if 'url_list' in image_info:
                url_list = image_info['url_list']
            elif 'display_image' in image_info and 'url_list' in image_info['display_image']:
                url_list = image_info['display_image']['url_list']
            
            if not url_list:
                print(f"⚠️  图片 {idx} 没有可用的下载链接")
                continue
            
            image_url = url_list[0]
            print(f"📸 下载图片 {idx}/{len(images)}: {image_url[:80]}...")
            
            # 下载图片内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            if response.status_code == 200:
                image_content = response.content
                file_size = len(image_content)
                print(f"📦 图片大小: {file_size / 1024:.2f} KB")
                
                # 获取文件扩展名
                extension = '.jpg'  # 抖音图片通常是jpg格式
                if 'webp' in image_url.lower():
                    extension = '.webp'
                elif 'png' in image_url.lower():
                    extension = '.png'
                
                # 保存图片文件（使用修复后的存储逻辑，包含aweme_item参数）
                await douyin_store.update_douyin_aweme_image_for_love(
                    aweme_id=aweme_id,
                    pic_content=image_content,
                    extension_file_name=f"{aweme_id}_{idx}{extension}",
                    aweme_item=aweme_item  # 关键：传递完整的作品信息
                )
                print(f"✅ 图片 {idx} 下载成功")
            else:
                print(f"❌ 图片 {idx} 下载失败: HTTP {response.status_code}")
                
            # 图片间添加小延时
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"❌ 图片 {idx} 下载异常: {e}")
            continue

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 抖音点赞作品下载器")
    print("📋 功能说明:")
    print("   • 自动下载所有点赞作品的视频和图片")
    print("   • 使用作品标题创建文件夹")
    print("   • 保存完整的JSON信息文件")
    print("   • 智能处理文件名中的特殊字符")
    print("="*60 + "\n")
    
    asyncio.run(main())