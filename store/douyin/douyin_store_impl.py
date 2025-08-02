# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  


# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 18:46
# @Desc    : 抖音存储实现类
import asyncio
import csv
import json
import os
import pathlib
from typing import Dict

import aiofiles

import config
from base.base_crawler import AbstractStore
from tools import utils, words
from var import crawler_type_var


def calculate_number_of_files(file_store_path: str) -> int:
    """计算数据保存文件的前部分排序数字，支持每次运行代码不写到同一个文件中
    Args:
        file_store_path;
    Returns:
        file nums
    """
    if not os.path.exists(file_store_path):
        return 1
    try:
        return max([int(file_name.split("_")[0]) for file_name in os.listdir(file_store_path)]) + 1
    except ValueError:
        return 1


class DouyinCsvStoreImplement(AbstractStore):
    csv_store_path: str = "data/douyin"
    file_count: int = calculate_number_of_files(csv_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        make save file name by store type
        Args:
            store_type: contents or comments

        Returns: eg: data/douyin/search_comments_20240114.csv ...

        """
        return f"{self.csv_store_path}/{self.file_count}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.csv"

    async def save_data_to_csv(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in CSV format.
        Args:
            save_item:  save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns: no returns

        """
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        async with aiofiles.open(save_file_name, mode='a+', encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            await writer.writerow(save_item.values())

    async def store_content(self, content_item: Dict):
        """
        Douyin content CSV storage implementation
        Args:
            content_item: note item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=content_item, store_type="contents")

    async def store_comment(self, comment_item: Dict):
        """
        Douyin comment CSV storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=comment_item, store_type="comments")

    async def store_creator(self, creator: Dict):
        """
        Douyin creator CSV storage implementation
        Args:
            creator: creator item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=creator, store_type="creator")


class DouyinDbStoreImplement(AbstractStore):
    async def store_content(self, content_item: Dict):
        """
        Douyin content DB storage implementation
        Args:
            content_item: content item dict

        Returns:

        """

        from .douyin_store_sql import (add_new_content,
                                       query_content_by_content_id,
                                       update_content_by_content_id)
        aweme_id = content_item.get("aweme_id")
        aweme_detail: Dict = await query_content_by_content_id(content_id=aweme_id)
        if not aweme_detail:
            content_item["add_ts"] = utils.get_current_timestamp()
            if content_item.get("title"):
                await add_new_content(content_item)
        else:
            await update_content_by_content_id(aweme_id, content_item=content_item)

    async def store_comment(self, comment_item: Dict):
        """
        Douyin content DB storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        from .douyin_store_sql import (add_new_comment,
                                       query_comment_by_comment_id,
                                       update_comment_by_comment_id)
        comment_id = comment_item.get("comment_id")
        comment_detail: Dict = await query_comment_by_comment_id(comment_id=comment_id)
        if not comment_detail:
            comment_item["add_ts"] = utils.get_current_timestamp()
            await add_new_comment(comment_item)
        else:
            await update_comment_by_comment_id(comment_id, comment_item=comment_item)

    async def store_creator(self, creator: Dict):
        """
        Douyin content DB storage implementation
        Args:
            creator: creator dict

        Returns:

        """
        from .douyin_store_sql import (add_new_creator,
                                       query_creator_by_user_id,
                                       update_creator_by_user_id)
        user_id = creator.get("user_id")
        user_detail: Dict = await query_creator_by_user_id(user_id)
        if not user_detail:
            creator["add_ts"] = utils.get_current_timestamp()
            await add_new_creator(creator)
        else:
            await update_creator_by_user_id(user_id, creator)


class DouyinStoreImage:
    """
    抖音图片存储实现类
    """
    
    def __init__(self):
        self.store_path = "data/douyin/images"
        pathlib.Path(self.store_path).mkdir(parents=True, exist_ok=True)
    
    async def store_image(self, image_item: Dict):
        """
        保存抖音图片到本地
        
        Args:
            image_item: 图片信息字典
        """
        aweme_id = image_item.get("aweme_id")
        pic_content = image_item.get("pic_content")
        extension_file_name = image_item.get("extension_file_name")
        
        # 创建以aweme_id命名的子目录
        aweme_dir = os.path.join(self.store_path, aweme_id)
        pathlib.Path(aweme_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存图片文件
        file_path = os.path.join(aweme_dir, extension_file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(pic_content)
        
        utils.logger.info(f"[DouyinStoreImage.store_image] 图片已保存: {file_path}")


class DouyinStoreVideo:
    """
    抖音视频存储实现类
    """
    
    def __init__(self):
        self.store_path = "data/douyin/videos"
        pathlib.Path(self.store_path).mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 替换不合法的文件名字符为下划线
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 替换换行符和制表符为空格
        filename = filename.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 移除其他控制字符
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # 移除连续的空格和下划线
        import re
        filename = re.sub(r'\s+', ' ', filename)
        filename = re.sub(r'_+', '_', filename)
        
        # 限制文件名长度
        if len(filename) > 80:
            filename = filename[:80]
        
        return filename.strip(' _')
    
    async def store_video(self, video_item: Dict):
        """
        保存抖音视频到本地
        
        Args:
            video_item: 视频信息字典
        """
        aweme_item = video_item.get("aweme_item")
        video_content = video_item.get("video_content")
        extension_file_name = video_item.get("extension_file_name")
        
        aweme_id = aweme_item.get("aweme_id")
        title = aweme_item.get("title", aweme_item.get("desc", aweme_id))
        
        # 清理标题作为文件夹名
        folder_name = self._sanitize_filename(title)
        if not folder_name:
            folder_name = aweme_id
        
        # 创建以作品标题命名的子目录
        aweme_dir = os.path.join(self.store_path, folder_name)
        pathlib.Path(aweme_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存视频文件
        file_path = os.path.join(aweme_dir, extension_file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(video_content)
        
        # 保存作品json数据
        json_file_path = os.path.join(aweme_dir, f"{aweme_id}.json")
        async with aiofiles.open(json_file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(aweme_item, ensure_ascii=False, indent=2))
        
        utils.logger.info(f"[DouyinStoreVideo.store_video] 视频已保存: {file_path}")
        utils.logger.info(f"[DouyinStoreVideo.store_video] JSON已保存: {json_file_path}")


class DouyinStoreImageForLove:
    """
    抖音点赞图片存储实现类
    """
    
    def __init__(self):
        self.store_path = "data/douyin/love"
        pathlib.Path(self.store_path).mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 替换不合法的文件名字符为下划线
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 替换换行符和制表符为空格
        filename = filename.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 移除其他控制字符
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # 移除连续的空格和下划线
        import re
        filename = re.sub(r'\s+', ' ', filename)
        filename = re.sub(r'_+', '_', filename)
        
        # 限制文件名长度
        if len(filename) > 80:
            filename = filename[:80]
        
        return filename.strip(' _')
    
    async def store_image(self, image_item: Dict):
        """
        保存抖音点赞图片到本地love目录
        
        Args:
            image_item: 图片信息字典
        """
        aweme_id = image_item.get("aweme_id")
        pic_content = image_item.get("pic_content")
        extension_file_name = image_item.get("extension_file_name")
        aweme_item = image_item.get("aweme_item")
        
        # 获取作品标题作为文件夹名
        title = aweme_item.get("title", aweme_item.get("desc", aweme_id)) if aweme_item else aweme_id
        
        # 清理标题作为文件夹名
        folder_name = self._sanitize_filename(title)
        if not folder_name:
            folder_name = aweme_id
        
        # 创建以作品标题命名的子目录
        aweme_dir = os.path.join(self.store_path, folder_name)
        pathlib.Path(aweme_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存图片文件
        file_path = os.path.join(aweme_dir, extension_file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(pic_content)
        
        # 保存作品json数据（如果有aweme_item信息）
        if aweme_item:
            json_file_path = os.path.join(aweme_dir, f"{aweme_id}.json")
            # 检查JSON文件是否已存在，避免重复保存
            if not os.path.exists(json_file_path):
                async with aiofiles.open(json_file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(aweme_item, ensure_ascii=False, indent=2))
                utils.logger.info(f"[DouyinStoreImageForLove.store_image] 点赞JSON已保存: {json_file_path}")
        
        utils.logger.info(f"[DouyinStoreImageForLove.store_image] 点赞图片已保存: {file_path}")


class DouyinStoreVideoForLove:
    """
    抖音点赞视频存储实现类
    """
    
    def __init__(self):
        self.store_path = "data/douyin/love"
        pathlib.Path(self.store_path).mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不合法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换不合法的文件名字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 处理换行符和制表符
        filename = filename.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 移除其他控制字符
        import re
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
        
        # 合并连续的空格和下划线
        filename = re.sub(r'\s+', ' ', filename)
        filename = re.sub(r'_+', '_', filename)
        
        # 限制文件名长度
        if len(filename) > 80:
            filename = filename[:80]
        
        return filename.strip(' _')
    
    async def store_video(self, video_item: Dict):
        """
        保存抖音点赞视频到本地love目录
        
        Args:
            video_item: 视频信息字典
        """
        aweme_item = video_item.get("aweme_item")
        video_content = video_item.get("video_content")
        extension_file_name = video_item.get("extension_file_name")
        
        aweme_id = aweme_item.get("aweme_id")
        title = aweme_item.get("title", aweme_item.get("desc", aweme_id))
        
        # 清理标题作为文件夹名
        folder_name = self._sanitize_filename(title)
        if not folder_name:
            folder_name = aweme_id
        
        # 创建以作品标题命名的子目录
        aweme_dir = os.path.join(self.store_path, folder_name)
        pathlib.Path(aweme_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存视频文件
        file_path = os.path.join(aweme_dir, extension_file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(video_content)
        
        # 保存作品json数据
        json_file_path = os.path.join(aweme_dir, f"{aweme_id}.json")
        async with aiofiles.open(json_file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(aweme_item, ensure_ascii=False, indent=2))
        
        utils.logger.info(f"[DouyinStoreVideoForLove.store_video] 点赞视频已保存: {file_path}")
        utils.logger.info(f"[DouyinStoreVideoForLove.store_video] 点赞JSON已保存: {json_file_path}")

class DouyinJsonStoreImplement(AbstractStore):
    json_store_path: str = "data/douyin/json"
    words_store_path: str = "data/douyin/words"

    lock = asyncio.Lock()
    file_count: int = calculate_number_of_files(json_store_path)
    WordCloud = words.AsyncWordCloudGenerator()

    def make_save_file_name(self, store_type: str) -> (str,str):
        """
        make save file name by store type
        Args:
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """

        return (
            f"{self.json_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.json",
            f"{self.words_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}"
        )
    async def save_data_to_json(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in json format.
        Args:
            save_item: save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.words_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name,words_file_name_prefix = self.make_save_file_name(store_type=store_type)
        save_data = []

        async with self.lock:
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, 'r', encoding='utf-8') as file:
                    save_data = json.loads(await file.read())

            save_data.append(save_item)
            async with aiofiles.open(save_file_name, 'w', encoding='utf-8') as file:
                await file.write(json.dumps(save_data, ensure_ascii=False))

            if config.ENABLE_GET_COMMENTS and config.ENABLE_GET_WORDCLOUD:
                try:
                    await self.WordCloud.generate_word_frequency_and_cloud(save_data, words_file_name_prefix)
                except:
                    pass

    async def store_content(self, content_item: Dict):
        """
        content JSON storage implementation
        Args:
            content_item:

        Returns:

        """
        await self.save_data_to_json(content_item, "contents")

    async def store_comment(self, comment_item: Dict):
        """
        comment JSON storage implementation
        Args:
            comment_item:

        Returns:

        """
        await self.save_data_to_json(comment_item, "comments")


    async def store_creator(self, creator: Dict):
        """
        Douyin creator CSV storage implementation
        Args:
            creator: creator item dict

        Returns:

        """
        await self.save_data_to_json(save_item=creator, store_type="creator")


class DouyinSqliteStoreImplement(AbstractStore):
    async def store_content(self, content_item: Dict):
        """
        Douyin content SQLite storage implementation
        Args:
            content_item: content item dict

        Returns:

        """

        from .douyin_store_sql import (add_new_content,
                                       query_content_by_content_id,
                                       update_content_by_content_id)
        aweme_id = content_item.get("aweme_id")
        aweme_detail: Dict = await query_content_by_content_id(content_id=aweme_id)
        if not aweme_detail:
            content_item["add_ts"] = utils.get_current_timestamp()
            if content_item.get("title"):
                await add_new_content(content_item)
        else:
            await update_content_by_content_id(aweme_id, content_item=content_item)

    async def store_comment(self, comment_item: Dict):
        """
        Douyin comment SQLite storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        from .douyin_store_sql import (add_new_comment,
                                       query_comment_by_comment_id,
                                       update_comment_by_comment_id)
        comment_id = comment_item.get("comment_id")
        comment_detail: Dict = await query_comment_by_comment_id(comment_id=comment_id)
        if not comment_detail:
            comment_item["add_ts"] = utils.get_current_timestamp()
            await add_new_comment(comment_item)
        else:
            await update_comment_by_comment_id(comment_id, comment_item=comment_item)

    async def store_creator(self, creator: Dict):
        """
        Douyin creator SQLite storage implementation
        Args:
            creator: creator dict

        Returns:

        """
        from .douyin_store_sql import (add_new_creator,
                                       query_creator_by_user_id,
                                       update_creator_by_user_id)
        user_id = creator.get("user_id")
        user_detail: Dict = await query_creator_by_user_id(user_id)
        if not user_detail:
            creator["add_ts"] = utils.get_current_timestamp()
            await add_new_creator(creator)
        else:
            await update_creator_by_user_id(user_id, creator)