#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆瓣配置文件模块 - 参考IMDB优化版本
包含豆瓣爬虫系统的所有配置参数
"""


class Config:
    """豆瓣配置类，包含所有系统配置"""
    
    # 基本配置 - 参考IMDB，针对大规模爬取优化
    MAX_MOVIES = 1000 # 最大爬取电影数量
    DELAY_MIN = 2     # 最小延时（秒）- 大规模爬取增加延时
    DELAY_MAX = 5     # 最大延时（秒）- 大规模爬取增加延时  
    REQUEST_TIMEOUT = 45  # 请求超时时间（秒）- 增加超时时间
    MAX_RETRIES = 2   # 最大重试次数 - 减少重试避免被检测
    
    # 豆瓣网站配置
    BASE_URL = "https://movie.douban.com"
    
    # 输出配置 - 参考IMDB
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/douban_posters"  # 封面图片存储目录
    
    # 支持的分类和类型 - 参考IMDB
    SUPPORTED_CATEGORIES = [
        'hot', 'top250', 'new_movies', 'weekly_best', 
        'north_america', 'classic', 'comedy', 'action', 
        'romance', 'sci_fi'
    ]
    
    # 豆瓣电影类型映射 - 新增
    GENRE_MAPPING = {
        'classic': '剧情',
        'comedy': '喜剧',
        'action': '动作',
        'romance': '爱情',
        'sci_fi': '科幻',
        'horror': '恐怖',
        'thriller': '惊悚',
        'documentary': '纪录片',
        'animation': '动画'
    }
    
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
    
    # 请求头配置 - 参考IMDB但适配中文
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    # Chrome浏览器配置（反爬虫优化版本） - 完全参考IMDB
    CHROME_OPTIONS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
        '--exclude-switches=enable-automation',
        '--disable-extensions-file-access-check',
        '--disable-extensions-http-throttling',
        '--disable-ipc-flooding-protection',
        '--window-size=1366,768',  # 常见屏幕分辨率
        '--start-maximized',
        '--disable-features=VizDisplayCompositor',
        '--disable-logging',
        '--log-level=3',
        '--disable-popup-blocking',
        '--disable-prompt-on-repost',
        '--disable-hang-monitor',
        '--disable-client-side-phishing-detection',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--ignore-ssl-errors',  # 忽略SSL错误
        '--ignore-certificate-errors',  # 忽略证书错误
        '--disable-web-security',  # 禁用web安全检查
        '--allow-running-insecure-content',  # 允许不安全内容
        '--silent',  # 静默模式
        '--no-first-run',  # 跳过首次运行提示
        '--disable-default-apps',  # 禁用默认应用
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    
    # 日志配置 - 参考IMDB
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'douban_crawler.log'
    }
    
    # 输出优化配置 - 参考IMDB
    SUPPRESS_WEBDRIVER_LOGS = True  # 抑制WebDriver详细日志
    SHOW_PROGRESS_DETAILS = False   # 显示详细进度信息
    SHOW_PARSING_SUCCESS = True     # 显示解析成功信息
    
    # 重试配置 - 参考IMDB
    MAX_RETRY_TIMES = 2  # 减少重试次数
    RETRY_DELAY = 2000   # 减少重试延迟（毫秒）
    
    @classmethod
    def get_movie_list_urls(cls, categories=['hot'], max_pages=10):
        """生成电影列表URL - 参考IMDB优化版"""
        urls = []
        
        for category in categories:
            if category == 'hot':
                # 热门电影榜单 - 支持更多页面
                for start in range(0, min(max_pages * 25, 500), 25):  # 增加到20页
                    urls.append(f"{cls.BASE_URL}/chart?start={start}&type=11")
            
            elif category == 'top250':
                # 豆瓣Top250 - 完整250部
                for start in range(0, min(max_pages * 25, 250), 25):
                    urls.append(f"{cls.BASE_URL}/top250?start={start}")
            
            elif category == 'new_movies':
                # 新片榜 - 支持多页
                for start in range(0, min(max_pages * 25, 100), 25):
                    urls.append(f"{cls.BASE_URL}/chart?type=5&start={start}")
            
            elif category == 'weekly_best':
                # 一周口碑榜 - 支持多页  
                for start in range(0, min(max_pages * 25, 100), 25):
                    urls.append(f"{cls.BASE_URL}/chart?type=12&start={start}")
            
            elif category == 'north_america':
                # 北美票房榜 - 支持多页
                for start in range(0, min(max_pages * 25, 100), 25):
                    urls.append(f"{cls.BASE_URL}/chart?type=2&start={start}")
            
            elif category == 'classic':
                # 经典电影 - 增加页数
                max_classic_pages = min(max_pages, 8)  # 增加到8页
                for start in range(0, max_classic_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=剧情&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'comedy':
                # 喜剧片 - 增加页数
                max_comedy_pages = min(max_pages, 8)  # 增加到8页
                for start in range(0, max_comedy_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=喜剧&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'action':
                # 动作片 - 增加页数
                max_action_pages = min(max_pages, 8)  # 增加到8页
                for start in range(0, max_action_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=动作&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'romance':
                # 爱情片 - 增加页数
                max_romance_pages = min(max_pages, 8)  # 增加到8页
                for start in range(0, max_romance_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=爱情&type=11&interval_id=100:90&action=&start={start}")
            
            elif category == 'sci_fi':
                # 科幻片 - 增加页数
                max_scifi_pages = min(max_pages, 8)  # 增加到8页
                for start in range(0, max_scifi_pages * 25, 25):
                    urls.append(f"{cls.BASE_URL}/typerank?type_name=科幻&type=11&interval_id=100:90&action=&start={start}")
        
        return urls
    
    @classmethod
    def get_genre_urls(cls, genres=['classic'], max_pages=5):
        """根据类型生成电影列表URL - 新增功能参考IMDB"""
        urls = []
        
        for genre in genres:
            genre_name = cls.GENRE_MAPPING.get(genre, '剧情')
            for start in range(0, min(max_pages * 25, 125), 25):
                urls.append(f"{cls.BASE_URL}/typerank?type_name={genre_name}&type=11&interval_id=100:90&action=&start={start}")
        
        return urls
