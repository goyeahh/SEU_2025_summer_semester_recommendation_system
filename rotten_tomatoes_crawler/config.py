#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
烂番茄爬虫配置文件
包含烂番茄爬虫系统的所有配置参数
"""


class RTConfig:
    """烂番茄配置类，包含所有系统配置"""
    
    # 基本配置
    MAX_MOVIES = 100  # 最大爬取电影数量
    DELAY_MIN = 0.5   # 最小延时（秒）- 减少延时
    DELAY_MAX = 1.5   # 最大延时（秒）- 减少延时
    
    # 烂番茄网站配置
    BASE_URL = "https://www.rottentomatoes.com"
    
    # 烂番茄电影分类URL配置
    CATEGORY_URLS = {
        'top_movies': 'https://www.rottentomatoes.com/top/bestofrt/',
        'in_theaters': 'https://www.rottentomatoes.com/browse/movies_in_theaters/',
        'coming_soon': 'https://www.rottentomatoes.com/browse/upcoming/',
        'most_popular': 'https://www.rottentomatoes.com/browse/movies_at_home/audience:upright~critics:upright?sortBy=popularity',
        'action_adventure': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:action~adventure?sortBy=popularity',
        'comedy': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:comedy?sortBy=popularity',
        'drama': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:drama?sortBy=popularity',
        'horror': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:horror?sortBy=popularity',
        'mystery_suspense': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:mystery~suspense?sortBy=popularity',
        'romance': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:romance?sortBy=popularity',
        'sci_fi_fantasy': 'https://www.rottentomatoes.com/browse/movies_at_home/genres:sci-fi~fantasy?sortBy=popularity'
    }
    
    # 爬取分类配置
    CRAWL_CATEGORIES = {
        'top_movies': '顶级电影',
        'in_theaters': '院线上映',
        'coming_soon': '即将上映',
        'most_popular': '最受欢迎',
        'action_adventure': '动作冒险',
        'comedy': '喜剧片',
        'drama': '剧情片',
        'horror': '恐怖片',
        'mystery_suspense': '悬疑惊悚',
        'romance': '爱情片',
        'sci_fi_fantasy': '科幻奇幻'
    }
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/rt_posters"  # 烂番茄封面图片存储目录
    OUTPUT_FORMATS = ['json', 'xlsx', 'csv']
    DOWNLOAD_POSTERS = False  # 是否下载海报（设置为False提升速度）
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN,zh;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    # Chrome浏览器配置 - 优化启动速度
    CHROME_OPTIONS = [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1366,768',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-images',  # 禁用图片加载提升速度
        '--disable-javascript-harmony-shipping',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-client-side-phishing-detection',
        '--disable-sync',
        '--disable-translate',
        '--hide-scrollbars',
        '--mute-audio',
        '--no-first-run',
        '--safebrowsing-disable-auto-update',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ]
    
    # 重试配置
    RETRY_TIMES = 3   # 减少重试次数
    RETRY_DELAY = 3   # 减少重试延时
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 烂番茄评分类型
    RATING_TYPES = {
        'tomatometer': '新鲜度',     # 专业影评人评分
        'audience': '爆米花指数',    # 观众评分
        'verified': '已验证观众评分'
    }
    
    @classmethod
    def get_category_url(cls, category, page=1):
        """
        获取分类页面URL
        
        Args:
            category: 分类名称
            page: 页面数
            
        Returns:
            str: 完整的URL
        """
        base_url = cls.CATEGORY_URLS.get(category)
        if not base_url:
            return None
            
        # 为某些URL添加分页参数
        if 'browse/' in base_url and page > 1:
            separator = '&' if '?' in base_url else '?'
            return f"{base_url}{separator}page={page}"
        
        return base_url
    
    @classmethod
    def get_all_categories(cls):
        """
        获取所有支持的分类
        
        Returns:
            list: 分类名称列表
        """
        return list(cls.CRAWL_CATEGORIES.keys())
