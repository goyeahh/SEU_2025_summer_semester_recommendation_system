#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB爬虫配置文    # Chrome浏览器配置 - 优化启动速度
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
    ]虫系统的所有配置参数
"""


class IMDBConfig:
    """IMDB配置类，包含所有系统配置"""
    
    # 基本配置 - 优化延时
    MAX_MOVIES = 100  # 最大爬取电影数量
    DELAY_MIN = 0.5   # 最小延时（秒）- 优化速度
    DELAY_MAX = 1.5   # 最大延时（秒）- 优化速度
    
    # IMDB网站配置
    BASE_URL = "https://www.imdb.com"
    
    # IMDB电影分类URL配置
    CATEGORY_URLS = {
        'top250': 'https://www.imdb.com/chart/top/?ref_=nv_mv_250',
        'popular': 'https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm', 
        'now_playing': 'https://www.imdb.com/chart/boxoffice/?ref_=nv_ch_BO',
        'upcoming': 'https://www.imdb.com/coming-soon/?ref_=nv_mv_cs',
        'action': 'https://www.imdb.com/search/title/?genres=action&sort=user_rating,desc&title_type=feature&num_votes=25000,',
        'comedy': 'https://www.imdb.com/search/title/?genres=comedy&sort=user_rating,desc&title_type=feature&num_votes=25000,',
        'drama': 'https://www.imdb.com/search/title/?genres=drama&sort=user_rating,desc&title_type=feature&num_votes=25000,',
        'horror': 'https://www.imdb.com/search/title/?genres=horror&sort=user_rating,desc&title_type=feature&num_votes=25000,',
        'sci_fi': 'https://www.imdb.com/search/title/?genres=sci-fi&sort=user_rating,desc&title_type=feature&num_votes=25000,',
        'thriller': 'https://www.imdb.com/search/title/?genres=thriller&sort=user_rating,desc&title_type=feature&num_votes=25000,'
    }
    
    # 爬取分类配置
    CRAWL_CATEGORIES = {
        'top250': 'IMDB Top 250',
        'popular': '热门电影',
        'now_playing': '正在上映',
        'upcoming': '即将上映',
        'action': '动作片',
        'comedy': '喜剧片',
        'drama': '剧情片',
        'horror': '恐怖片',
        'sci_fi': '科幻片',
        'thriller': '惊悚片'
    }
    
    # 输出配置
    OUTPUT_DIR = "data"
    POSTER_DIR = "data/imdb_posters"  # IMDB封面图片存储目录
    OUTPUT_FORMATS = ['json', 'xlsx', 'csv']
    
    # 请求头配置
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN,zh;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    # Chrome浏览器配置
    CHROME_OPTIONS = [
        '--headless',  # 无头模式
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--disable-blink-features=AutomationControlled',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ]
    
    # 重试配置
    RETRY_TIMES = 3
    RETRY_DELAY = 3  # 减少重试延时
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_category_url(cls, category, start=1, count=50):
        """
        获取分类页面URL
        
        Args:
            category: 分类名称
            start: 起始位置
            count: 获取数量
            
        Returns:
            str: 完整的URL
        """
        base_url = cls.CATEGORY_URLS.get(category)
        if not base_url:
            return None
            
        # 对于搜索页面，添加分页参数
        if 'search/title' in base_url:
            return f"{base_url}&start={start}&count={count}"
        
        return base_url
    
    @classmethod
    def get_all_categories(cls):
        """
        获取所有支持的分类
        
        Returns:
            list: 分类名称列表
        """
        return list(cls.CRAWL_CATEGORIES.keys())
