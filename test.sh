#!/bin/bash

# MediaCrawler 抖音爬虫使用命令示例

# 基本搜索命令（搜索关键词并下载视频）
uv run main.py --platform dy --lt qrcode --type search --keywords "舞蹈教学" --get_comment false

# 搜索美食相关视频
uv run main.py --platform dy --lt qrcode --type search --keywords "美食" --get_comment false

# 搜索并获取评论
uv run main.py --platform dy --lt qrcode --type search --keywords "旅游" --get_comment true

# 获取指定视频详情
uv run main.py --platform dy --lt qrcode --type detail --keywords "视频ID" --get_comment false

# 获取当前用户的点赞作品（需要先配置DY_USER_ID）
uv run main.py --platform dy --lt qrcode --type love --get_comment false

# 参数说明：
# --platform dy: 指定平台为抖音
# --lt qrcode: 登录方式为二维码
# --type search: 搜索模式
# --type detail: 详情模式
# --type love: 点赞作品模式
# --keywords: 搜索关键词或视频ID
# --get_comment: 是否获取评论 (true/false)

# 注意：
# 1. 搜索的视频将保存到 data/douyin/videos/ 目录下
# 2. 点赞的视频和图片统一保存在 data/douyin/love/ 目录下
# 3. 每个视频会以作品标题命名文件夹
# 4. 文件夹内包含视频文件和对应的JSON数据
# 5. JSON数据保存在 data/douyin/json/ 目录下
# 6. 使用love模式前需要在 config/dy_config.py 中配置 DY_USER_ID
# 7. DY_USER_ID 获取方法：登录抖音后在浏览器开发者工具中查看网络请求