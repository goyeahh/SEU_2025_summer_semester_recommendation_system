#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置文件模块
包含爬虫系统的所有配置参数
"""


class Config:
    """配置类，包含所有系统配置"""
    
    # 基本配置
    MAX_MOVIES = 200  # 最大爬取电影数量
    DELAY_MIN = 2     # 最小延时（秒）
    DELAY_MAX = 5     # 最大延时（秒）
    
    # 豆瓣网站配置
    BASE_URL = "https://movie.douban.com"
    
    # 爬取分类配置
    CRAWL_CATEGORIES = {
        'hot': '豆瓣电影热门榜',
        'top250': '豆瓣电影Top250',
        'new_movies': '新片榜',
        'weekly_best': '一周口碑榜',
        'north_america': '北美票房榜',
        'classic': '经典电影',
        'comedy': '喜剧片',
        'action': '动作片',
        'romance': '爱情片',
        'sci_fi': '科幻片'
    }
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/douban_posters"  # 封面图片存储目录
    OUTPUT_FORMATS = ['json', 'csv']
    
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
        '--disable-software-rasterizer',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-logging',
        '--log-level=3',
        '--window-size=1920,1080',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images'
    ]
    
    # 重试配置
    MAX_RETRY_TIMES = 3
    RETRY_DELAY = 2000  # 毫秒
    
    # 电影类型标准化列表（用于神经网络特征工程）
    STANDARD_GENRES = [
        '剧情', '喜剧', '动作', '爱情', '科幻', '动画', 
        '悬疑', '惊悚', '恐怖', '纪录片', '短片', '情色', 
        '音乐', '歌舞', '家庭', '儿童', '传记', '历史', 
        '战争', '犯罪', '西部', '奇幻', '冒险', '灾难', 
        '武侠', '古装', '运动', '黑色电影'
    ]
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'douban_crawler.log'
    }
    
    @classmethod
    def get_movie_list_urls(cls, categories=['hot'], max_pages=10):
        """生成电影列表URL - 优化版"""
        urls = []
        
        for category in categories:
            if category == 'hot':
                # 热门电影榜单 - 最多10页
                for start in range(0, min(max_pages * 25, 250), 25):
                    urls.append(f"{cls.BASE_URL}/chart?start={start}&type=11")
            
            elif category == 'top250':
                # 豆瓣Top250 - 固定10页
                for start in range(0, min(max_pages * 25, 250), 25):
                    urls.append(f"{cls.BASE_URL}/top250?start={start}")
            
            elif category == 'new_movies':
                # 新片榜 - 单页
                urls.append(f"{cls.BASE_URL}/chart?type=5")
            
            elif category == 'weekly_best':
                # 一周口碑榜 - 单页
                urls.append(f"{cls.BASE_URL}/chart?type=12")
            
            elif category == 'north_america':
                # 北美票房榜 - 单页
                urls.append(f"{cls.BASE_URL}/chart?type=2")
            
            elif category == 'classic':
                # 经典电影 - 限制页数，避免过度请求
                max_classic_pages = min(max_pages, 4)  # 最多4页
                for start in range(0, max_classic_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=剧情&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'comedy':
                # 喜剧片 - 限制页数
                max_comedy_pages = min(max_pages, 4)  # 最多4页
                for start in range(0, max_comedy_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=喜剧&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'action':
                # 动作片 - 限制页数
                max_action_pages = min(max_pages, 4)  # 最多4页
                for start in range(0, max_action_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=动作&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'romance':
                # 爱情片 - 限制页数
                max_romance_pages = min(max_pages, 4)  # 最多4页
                for start in range(0, max_romance_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=爱情&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'sci_fi':
                # 科幻片 - 限制页数
                max_scifi_pages = min(max_pages, 4)  # 最多4页
                for start in range(0, max_scifi_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=科幻&type=11&interval_id=100:90&action=&start={start}")
        
        return urls
