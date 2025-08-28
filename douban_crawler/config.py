#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件模块
包含爬虫系统的所有配置参数
"""


class Config:
    """配置类，包含所有系统配置"""
    
    # 基本配置 - 优化延时
    MAX_MOVIES = 100  # 最大爬取电影数量
    DELAY_MIN = 0.5   # 最小延时（秒）- 优化速度
    DELAY_MAX = 1.5   # 最大延时（秒）- 优化速度
    
    # 豆瓣网站配置
    BASE_URL = "https://movie.douban.com"
    
    # 爬取分类配置
    CRAWL_CATEGORIES = {
        'hot': '热门电影',
        'new_movies': '新片榜',
        'classic': '经典电影'
    }
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/posters"  # 封面图片存储目录
    OUTPUT_FORMATS = ['json', 'xlsx', 'csv']
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Chrome浏览器配置
    CHROME_OPTIONS = [
        '--headless',  # 无头模式
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080'
    ]
    
    # 重试配置
    MAX_RETRY_TIMES = 3
    RETRY_DELAY = 1000  # 毫秒 - 减少重试延时
    
    # 电影类型标准化列表（用于神经网络特征工程）
    STANDARD_GENRES = [
        '剧情', '喜剧', '动作', '爱情', '科幻', '动画', 
        '悬疑', '惊悚', '恐怖', '纪录片', '短片', '情色', 
        '音乐', '歌舞', '家庭', '儿童', '传记', '历史', 
        '战争', '犯罪', '西部', '奇幻', '冒险', '灾难', 
        '武侠', '古装', '运动', '黑色电影'
    ]
    
    # 特征工程配置
    FEATURE_CONFIG = {
        'rating_max': 10.0,      # 评分最大值
        'runtime_max': 300.0,    # 电影时长最大值（分钟）
        'rating_count_log': True, # 是否对评分人数取对数
        'summary_max_length': 500 # 简介最大长度
    }
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'douban_crawler.log'
    }
    
    @classmethod
    def get_movie_list_urls(cls, categories=['hot'], max_pages=10):
        """生成电影列表URL"""
        urls = []
        
        for category in categories:
            if category == 'hot':
                # 热门电影榜单
                for start in range(0, min(max_pages * 25, 250), 25):
                    urls.append(f"{cls.BASE_URL}/chart?start={start}&type=11")
            
            elif category == 'new_movies':
                # 新片榜
                urls.append(f"{cls.BASE_URL}/chart?type=5")
            
            elif category == 'classic':
                # 经典电影
                for start in range(0, min(max_pages * 25, 100), 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=剧情&type=11&interval_id=100:90&action=&start={start}")
        
        return urls
