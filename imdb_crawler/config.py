#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB配置文件模块
包含IMDB爬虫系统的所有配置参数
"""


class IMDBConfig:
    """IMDB配置类，包含所有系统配置"""
    
    # 基本配置（极速优化）
    MAX_MOVIES = 200  # 最大爬取电影数量
    DELAY_MIN = 0.5   # 最小延时（秒）- 极速模式
    DELAY_MAX = 1.5   # 最大延时（秒）- 极速模式
    
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
    
    # Chrome浏览器配置（极速优化版本）
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
        '--window-size=1024,600',  # 更小的窗口
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images',  # 禁用图片加载，大幅提速
        '--disable-javascript',  # 禁用JS（谨慎使用）
        '--no-first-run',
        '--disable-default-apps',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-sync',  # 禁用同步
        '--disable-translate',  # 禁用翻译
        '--disable-popup-blocking',
        '--disable-prompt-on-repost',
        '--disable-hang-monitor',
        '--disable-client-side-phishing-detection',
        '--disable-component-update',
        '--disable-domain-reliability',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--aggressive-cache-discard',  # 激进的缓存清理
        '--memory-pressure-off',  # 关闭内存压力检测
        '--max_old_space_size=4096',  # 限制内存使用
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # 重试配置（优化版本）
    MAX_RETRY_TIMES = 2  # 减少重试次数
    RETRY_DELAY = 2000   # 减少重试延迟（毫秒）
    
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
