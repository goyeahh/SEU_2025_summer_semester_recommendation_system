#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB主爬虫类
整合所有模块，提供统一的爬虫接口
"""

import os
import logging
from tqdm import tqdm
import random
import time

from .config import IMDBConfig
from .network import IMDBNetworkManager
from .parser import IMDBPageParser
from .data_processor import IMDBDataProcessor


class IMDBMovieCrawler:
    """IMDB电影爬虫主类"""
    
    def __init__(self, config=None):
        """初始化爬虫"""
        self.config = config or IMDBConfig()
        self.network_manager = IMDBNetworkManager()
        self.parser = IMDBPageParser()
        self.data_processor = IMDBDataProcessor()
        
        # 创建输出目录
        if not os.path.exists(self.config.OUTPUT_DIR):
            os.makedirs(self.config.OUTPUT_DIR)
        
        # 设置日志
        self._setup_logging()
        
        self.logger.info("IMDB电影爬虫初始化完成")
    
    def _setup_logging(self):
        """设置日志记录"""
        log_config = self.config.LOG_CONFIG
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_config['file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def crawl_movies(self, categories=None, max_movies=None, max_pages=5):
        """
        爬取电影数据
        
        Args:
            categories: 要爬取的分类列表，默认['top250']
            max_movies: 最大爬取电影数量，默认使用配置值
            max_pages: 每个分类最大页数，默认5
            
        Returns:
            dict: 爬取结果信息
        """
        categories = categories or ['top250']
        max_movies = max_movies or self.config.MAX_MOVIES
        
        self.logger.info(f"开始爬取IMDB电影数据 - 分类: {categories}, 最大数量: {max_movies}")
        
        try:
            # 第一步：获取电影列表URLs
            list_urls = self.config.get_movie_list_urls(categories, max_pages)
            self.logger.info(f"生成了 {len(list_urls)} 个列表页面URL")
            
            # 第二步：解析电影列表，获取详情页链接
            movie_links = self._collect_movie_links(list_urls)
            
            # 限制电影数量
            if len(movie_links) > max_movies:
                movie_links = random.sample(movie_links, max_movies)
            
            self.logger.info(f"将爬取 {len(movie_links)} 部电影的详情")
            
            # 第三步：爬取电影详情
            raw_movie_data = self._crawl_movie_details(movie_links)
            
            # 第四步：数据清洗和处理
            cleaned_data = self.data_processor.clean_movie_data(raw_movie_data)
            
            # 第五步：保存数据
            saved_files = self.data_processor.save_processed_data(
                cleaned_data, 
                self.config.OUTPUT_DIR
            )
            
            self.logger.info(f"IMDB爬虫任务完成！成功获取 {len(cleaned_data)} 部电影信息")
            
            # 返回格式与豆瓣爬虫保持一致
            return {
                'success': True,
                'data_count': len(cleaned_data),
                'file_paths': saved_files,
                'message': f'成功爬取 {len(cleaned_data)} 部IMDB电影'
            }
            
        except Exception as e:
            self.logger.error(f"IMDB爬虫运行出错: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'IMDB爬取失败: {str(e)}'
            }
        finally:
            self.network_manager.close()
    
    def _collect_movie_links(self, list_urls):
        """收集电影详情页链接（极速优化版本）"""
        all_movie_links = []
        
        for url in tqdm(list_urls, desc="解析IMDB电影列表页面"):
            try:
                # 列表页面优先使用requests，速度快10倍
                response = self.network_manager.get_page(url, use_selenium=False)
                
                # 确定URL类型
                if 'chart' in url:
                    url_type = 'chart'
                elif 'search' in url:
                    url_type = 'search'
                else:
                    url_type = 'chart'
                
                movie_links = self.parser.parse_movie_list(response, url_type)
                
                # 只有在requests完全失败时才使用Selenium
                if len(movie_links) == 0:
                    self.logger.info(f"requests未获取到链接，尝试Selenium: {url}")
                    response = self.network_manager.get_page(url, use_selenium=True)
                    movie_links = self.parser.parse_movie_list(response, url_type)
                
                all_movie_links.extend(movie_links)
                
                # 列表页面使用最小延时
                time.sleep(random.uniform(0.5, 1.2))
                
            except Exception as e:
                self.logger.warning(f"解析IMDB列表页面失败: {url}, 错误: {e}")
                continue
        
        # 去重
        unique_links = list(set(all_movie_links))
        self.logger.info(f"收集到 {len(unique_links)} 个唯一IMDB电影链接")
        
        return unique_links
    
    def _crawl_movie_details(self, movie_links):
        """爬取电影详情（高度优化版本）"""
        movie_data = []
        selenium_failures = 0
        
        for i, link in enumerate(tqdm(movie_links, desc="爬取IMDB电影详情")):
            try:
                # 首先尝试requests（速度快）
                response = self.network_manager.get_page(link, use_selenium=False)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                # 如果requests解析失败或数据不完整，再尝试Selenium
                if not movie_info or not self._is_movie_info_complete(movie_info):
                    self.logger.info(f"requests数据不完整，使用Selenium重试: {link}")
                    response = self.network_manager.get_page(link, use_selenium=True)
                    movie_info = self.parser.parse_movie_detail(response, link)
                    
                    if not movie_info:
                        selenium_failures += 1
                        
                        # 如果Selenium失败率过高，后续优先使用requests
                        if selenium_failures > 3 and i > 10:
                            self.logger.warning("Selenium失败率高，后续优先使用requests")
                
                if movie_info:
                    movie_data.append(movie_info)
                
                # 动态调整延时：成功率高时减少延时
                success_rate = len(movie_data) / (i + 1) if i > 0 else 1.0
                if success_rate > 0.8:
                    delay = random.uniform(0.5, 1.5)  # 高成功率时快速处理
                else:
                    delay = random.uniform(1.5, 2.5)  # 成功率低时谨慎处理
                
                time.sleep(delay)
                
            except Exception as e:
                self.logger.warning(f"爬取IMDB电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"成功爬取 {len(movie_data)} 部IMDB电影详情")
        return movie_data
    
    def _is_movie_info_complete(self, movie_info):
        """检查电影信息是否完整 - 放宽标准"""
        if not movie_info:
            return False
        
        # 至少需要有标题或ID之一
        has_title = bool(movie_info.get('title', '').strip())
        has_id = bool(movie_info.get('imdb_id', '').strip())
        
        if not has_title and not has_id:
            return False
        
        # 如果有基本信息，就认为是完整的
        # 评分可能为None或0，这是正常的
        return True
    
    def get_movie_by_id(self, imdb_id):
        """根据IMDB ID获取单个电影信息"""
        url = f"{self.config.BASE_URL}/title/{imdb_id}/"
        
        try:
            response = self.network_manager.get_page(url, use_selenium=True)
            movie_info = self.parser.parse_movie_detail(response, url)
            
            if movie_info:
                cleaned_data = self.data_processor.clean_movie_data([movie_info])
                return cleaned_data[0] if cleaned_data else None
            
        except Exception as e:
            self.logger.error(f"获取IMDB电影信息失败 (ID: {imdb_id}): {e}")
            
        return None
    
    def search_movies(self, keyword, max_results=20):
        """搜索电影"""
        search_url = f"{self.config.BASE_URL}/find?q={keyword}&s=tt&ttype=ft"
        
        try:
            response = self.network_manager.get_page(search_url, use_selenium=True)
            movie_links = self.parser.parse_movie_list(response, 'search')
            
            # 限制结果数量
            if len(movie_links) > max_results:
                movie_links = movie_links[:max_results]
            
            # 获取电影详情
            movie_data = []
            for link in movie_links:
                try:
                    detail_response = self.network_manager.get_page(link, use_selenium=True)
                    movie_info = self.parser.parse_movie_detail(detail_response, link)
                    if movie_info:
                        movie_data.append(movie_info)
                except Exception as e:
                    self.logger.warning(f"获取搜索结果详情失败: {link}, {e}")
                    continue
            
            return self.data_processor.clean_movie_data(movie_data)
            
        except Exception as e:
            self.logger.error(f"搜索IMDB电影失败: {e}")
            return []
    
    def get_movies_by_genre(self, genre, max_movies=50):
        """根据类型获取电影"""
        try:
            urls = self.config.get_genre_url(genre)
            movie_links = self._collect_movie_links(urls)
            
            if len(movie_links) > max_movies:
                movie_links = random.sample(movie_links, max_movies)
            
            raw_data = self._crawl_movie_details(movie_links)
            return self.data_processor.clean_movie_data(raw_data)
            
        except Exception as e:
            self.logger.error(f"根据类型获取电影失败: {e}")
            return []
    
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
            bool: 连接是否成功
        """
        try:
            response = self.network_manager.get_page(self.config.BASE_URL, use_selenium=True)
            return response is not None
        except Exception as e:
            self.logger.error(f"IMDB连接测试失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.network_manager.close()
