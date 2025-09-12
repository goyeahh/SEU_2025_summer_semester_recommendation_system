#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB配置文件模块
包含IMDB爬虫系统的所有配置参数
"""


class IMDBConfig:
    """IMDB配置类，包含所有系统配置"""
    
    # 基本配置 - 针对大规模爬取优化
    MAX_MOVIES = 1000 # 最大爬取电影数量
    DELAY_MIN = 2     # 最小延时（秒）- 大规模爬取增加延时
    DELAY_MAX = 5     # 最大延时（秒）- 大规模爬取增加延时
    REQUEST_TIMEOUT = 45  # 请求超时时间（秒）- 增加超时时间
    MAX_RETRIES = 2   # 最大重试次数 - 减少重试避免被检测
    
    # IMDB网站配置
    BASE_URL = "https://www.imdb.com"
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/imdb_posters"  # 封面图片存储目录
    
    # 支持的分类和类型
    SUPPORTED_CATEGORIES = [
        'top250', 'popular', 'upcoming', 'in_theaters', 
        'most_popular_movies', 'top_rated_movies', 'recent_movies'
    ]
    
    SUPPORTED_GENRES = [
        'action', 'adventure', 'animation', 'biography', 'comedy',
        'crime', 'documentary', 'drama', 'family', 'fantasy',
        'history', 'horror', 'music', 'mystery', 'romance',
        'sci-fi', 'sport', 'thriller', 'war', 'western'
    ]
    
    # Chrome浏览器配置（反爬虫优化版本）
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
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'imdb_crawler.log'
    }
    
    # 输出优化配置
    SUPPRESS_WEBDRIVER_LOGS = True  # 抑制WebDriver详细日志
    SHOW_PROGRESS_DETAILS = False   # 显示详细进度信息
    SHOW_PARSING_SUCCESS = True     # 显示解析成功信息
    
    # 重试配置
    MAX_RETRY_TIMES = 2  # 减少重试次数
    RETRY_DELAY = 2000   # 减少重试延迟（毫秒）
    
    @classmethod
    def get_movie_list_urls(cls, categories=['top250'], max_pages=10):
        """生成电影列表URL - 支持大量爬取"""
        urls = []
        
        for category in categories:
            if category == 'top250':
                # IMDB Top 250
                urls.append(f"{cls.BASE_URL}/chart/top/")
            
            elif category == 'popular':
                # 最受欢迎电影
                urls.append(f"{cls.BASE_URL}/chart/moviemeter/")
            
            elif category == 'upcoming':
                # 即将上映
                urls.append(f"{cls.BASE_URL}/chart/upcoming/")
            
            elif category == 'in_theaters':
                # 正在上映
                urls.append(f"{cls.BASE_URL}/chart/boxoffice/")
            
            elif category == 'most_popular_movies':
                # 最受欢迎电影（多页面）
                for start in range(1, min(max_pages + 1, 21)):  # 增加到20页
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=moviemeter,asc&start={1 + (start-1)*50}&ref_=adv_nxt")
            
            elif category == 'top_rated_movies':
                # 评分最高电影（多页面）
                for start in range(1, min(max_pages + 1, 21)):  # 增加到20页
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=user_rating,desc&start={1 + (start-1)*50}&ref_=adv_nxt")
            
            elif category == 'recent_movies':
                # 最新电影（多页面）
                for start in range(1, min(max_pages + 1, 11)):
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=release_date,desc&start={1 + (start-1)*50}&ref_=adv_nxt")
        
        return urls
    
    @classmethod
    def get_genre_urls(cls, genres=['action'], max_pages=5):
        """根据类型生成电影列表URL - 支持按类型大量爬取"""
        urls = []
        
        for genre in genres:
            for start in range(1, min(max_pages + 1, 11)):
                urls.append(f"{cls.BASE_URL}/search/title/?genres={genre.lower()}&sort=user_rating,desc&title_type=feature&start={1 + (start-1)*50}")
        
        return urls
