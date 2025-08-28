#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB电影爬虫主控制器
协调各个模块完成电影数据爬取任务
"""

import logging
import time
from tqdm import tqdm
from .config import IMDBConfig
from .network import IMDBNetwork
from .parser import IMDBParser
from .data_processor import IMDBDataProcessor


class IMDBCrawler:
    """IMDB电影爬虫主类"""
    
    def __init__(self, config=None):
        """
        初始化爬虫
        
        Args:
            config: 配置对象，默认使用IMDBConfig
        """
        self.config = config or IMDBConfig()
        self.network = IMDBNetwork(self.config)
        self.parser = IMDBParser(self.config)
        self.data_processor = IMDBDataProcessor(self.config)
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("IMDB电影爬虫初始化完成")
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL, logging.INFO),
            format=self.config.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('imdb_crawler.log', encoding='utf-8')
            ]
        )
    
    def crawl_movies(self, categories=None, max_movies=None):
        """
        爬取电影数据
        
        Args:
            categories: 要爬取的分类列表，None表示使用默认分类
            max_movies: 最大爬取数量，None表示使用配置中的值
            
        Returns:
            dict: 包含爬取结果和文件路径的字典
        """
        # 参数处理
        if categories is None:
            categories = ['popular']  # 默认爬取热门电影
        
        if max_movies is None:
            max_movies = self.config.MAX_MOVIES
        
        self.logger.info(f"开始爬取IMDB电影数据 - 分类: {categories}, 最大数量: {max_movies}")
        
        try:
            # 1. 获取电影链接
            movie_urls = self._collect_movie_urls(categories, max_movies)
            
            if not movie_urls:
                self.logger.warning("没有收集到电影链接")
                return {'success': False, 'data': [], 'file_paths': {}}
            
            self.logger.info(f"收集到 {len(movie_urls)} 个唯一电影链接")
            
            # 2. 爬取电影详情
            movies_data = self._crawl_movie_details(movie_urls)
            
            if not movies_data:
                self.logger.warning("没有成功爬取到电影详情")
                return {'success': False, 'data': [], 'file_paths': {}}
            
            self.logger.info(f"成功爬取 {len(movies_data)} 部电影详情")
            
            # 3. 处理数据
            result = self.data_processor.process_movies(movies_data)
            
            self.logger.info("爬虫任务完成！成功获取 {} 部电影信息".format(
                len(result.get('cleaned_data', []))
            ))
            
            return {
                'success': True,
                'data': result.get('cleaned_data', []),
                'file_paths': result.get('file_paths', {}),
                'features': result.get('features', {}),
                'total_crawled': len(movies_data),
                'total_processed': len(result.get('cleaned_data', []))
            }
            
        except Exception as e:
            self.logger.error(f"爬虫任务执行失败: {e}")
            return {'success': False, 'error': str(e), 'data': [], 'file_paths': {}}
        
        finally:
            # 清理资源
            self.network.close_driver()
    
    def _collect_movie_urls(self, categories, max_movies):
        """
        收集电影URL链接
        
        Args:
            categories: 分类列表
            max_movies: 最大数量
            
        Returns:
            list: 电影URL列表
        """
        all_movie_urls = set()
        movies_per_category = max_movies // len(categories)
        
        # 计算需要生成的页面数量
        pages_to_crawl = max(1, (movies_per_category + 49) // 50)  # 每页大约50部电影
        
        self.logger.info(f"生成了 {len(categories) * pages_to_crawl} 个列表页面URL")
        
        # 遍历每个分类
        for category in tqdm(categories, desc="解析电影列表页面"):
            category_urls = set()
            
            # 获取多页数据
            for page in range(pages_to_crawl):
                start_index = page * 50 + 1
                category_url = self.config.get_category_url(category, start=start_index, count=50)
                
                if not category_url:
                    self.logger.warning(f"无效的分类: {category}")
                    continue
                
                # IMDB需要JavaScript渲染，直接使用Selenium
                use_selenium = True
                wait_element = '.ipc-title'
                
                # 获取页面内容
                html = self.network.get_page(category_url, use_selenium=use_selenium, wait_element=wait_element)
                
                if not html:
                    self.logger.warning(f"获取页面失败: {category_url}")
                    continue
                
                # 解析电影链接
                page_urls = self.parser.parse_movie_list(html, category)
                category_urls.update(page_urls)
                
                # 如果获取的链接数量已经足够，则停止
                if len(category_urls) >= movies_per_category:
                    break
                
                # 适当延时
                time.sleep(1)
            
            # 限制每个分类的数量
            category_urls = list(category_urls)[:movies_per_category]
            all_movie_urls.update(category_urls)
            
            self.logger.info(f"从 {category} 分类收集到 {len(category_urls)} 个电影链接")
        
        # 转换为列表并限制总数量
        movie_urls = list(all_movie_urls)[:max_movies]
        
        return movie_urls
    
    def _crawl_movie_details(self, movie_urls):
        """
        爬取电影详情
        
        Args:
            movie_urls: 电影URL列表
            
        Returns:
            list: 电影详情数据列表
        """
        movies_data = []
        
        self.logger.info(f"将爬取 {len(movie_urls)} 部电影的详情")
        
        # 使用进度条显示爬取进度
        for url in tqdm(movie_urls, desc="爬取电影详情"):
            try:
                # IMDB详情页面需要JavaScript渲染，使用Selenium
                html = self.network.get_page(url, use_selenium=True, wait_element='.ipc-page-content-container')
                
                if not html:
                    self.logger.warning(f"获取电影页面失败: {url}")
                    continue
                
                # 解析电影详情
                movie_data = self.parser.parse_movie_detail(html, url)
                
                if movie_data:
                    movies_data.append(movie_data)
                else:
                    self.logger.warning(f"解析电影详情失败: {url}")
                
            except Exception as e:
                self.logger.error(f"处理电影详情时出错 {url}: {e}")
                continue
        
        return movies_data
    
    def get_supported_categories(self):
        """
        获取支持的分类列表
        
        Returns:
            dict: 分类字典，键为分类代码，值为分类名称
        """
        return self.config.CRAWL_CATEGORIES.copy()
    
    def test_connection(self):
        """
        测试网络连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            test_url = "https://www.imdb.com"
            html = self.network.get_page(test_url)
            
            if html and "IMDb" in html:
                self.logger.info("IMDB网络连接测试成功")
                return True
            else:
                self.logger.error("IMDB网络连接测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"IMDB网络连接测试异常: {e}")
            return False
    
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        if hasattr(self, 'network'):
            self.network.close_driver()
