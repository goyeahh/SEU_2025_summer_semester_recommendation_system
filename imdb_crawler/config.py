#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB配置文件模块
包含IMDB爬虫系统的所有配置参数
"""


class IMDBConfig:
    """IMDB配置类，包含所有系统配置"""
    
    # 基本配置
    MAX_MOVIES = 200  # 最大爬取电影数量
    DELAY_MIN = 2     # 最小延时（秒）
    DELAY_MAX = 5     # 最大延时（秒）
    
    # IMDB网站配置
    BASE_URL = "https://www.imdb.com"
    
    # 爬取分类配置
    CRAWL_CATEGORIES = {
        'top250': 'IMDB Top 250',
        'popular': '最受欢迎电影',
        'upcoming': '即将上映',
        'in_theaters': '正在上映',
        'most_popular_movies': '最受欢迎电影',
        'top_rated_movies': '评分最高电影',
        'lowest_rated_movies': '评分最低电影'
    }
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/imdb_posters"  # 封面图片存储目录
    OUTPUT_FORMATS = ['json', 'csv']
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
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
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # 重试配置
    MAX_RETRY_TIMES = 3
    RETRY_DELAY = 3000  # 毫秒
    
    # 电影类型标准化列表
    STANDARD_GENRES = [
        'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 
        'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 
        'Film-Noir', 'History', 'Horror', 'Music', 'Musical', 
        'Mystery', 'Romance', 'Sci-Fi', 'Sport', 'Thriller', 
        'War', 'Western'
    ]
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'imdb_crawler.log'
    }
    
    @classmethod
    def get_movie_list_urls(cls, categories=['top250'], max_pages=10):
        """生成电影列表URL"""
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
                # 最受欢迎电影（更多页面）
                for start in range(1, min(max_pages + 1, 11)):
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=moviemeter,asc&start={1 + (start-1)*50}&ref_=adv_nxt")
            
            elif category == 'top_rated_movies':
                # 评分最高电影
                for start in range(1, min(max_pages + 1, 11)):
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=user_rating,desc&start={1 + (start-1)*50}&ref_=adv_nxt")
            
            elif category == 'lowest_rated_movies':
                # 评分最低电影
                for start in range(1, min(max_pages + 1, 11)):
                    urls.append(f"{cls.BASE_URL}/search/title/?title_type=feature&sort=user_rating,asc&start={1 + (start-1)*50}&ref_=adv_nxt")
        
        return urls
    
    @classmethod
    def get_genre_url(cls, genre, max_pages=5):
        """根据类型获取电影列表URL"""
        urls = []
        for start in range(1, min(max_pages + 1, 6)):
            urls.append(f"{cls.BASE_URL}/search/title/?genres={genre.lower()}&sort=user_rating,desc&title_type=feature&start={1 + (start-1)*50}")
        return urls
