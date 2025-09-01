#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主爬虫类
整合所有模块，提供统一的爬虫接口
"""

import os
import logging
from tqdm import tqdm
import random
import time

from .config import Config
from .network import NetworkManager
from .parser import PageParser
from .data_processor import DataProcessor


class DoubanMovieCrawler:
    """豆瓣电影爬虫主类"""
    
    def __init__(self, config=None):
        """初始化爬虫"""
        self.config = config or Config()
        self.network_manager = NetworkManager()
        self.parser = PageParser()
        self.data_processor = DataProcessor()
        
        # 创建输出目录
        if not os.path.exists(self.config.OUTPUT_DIR):
            os.makedirs(self.config.OUTPUT_DIR)
        
        # 设置日志
        self._setup_logging()
        
        self.logger.info("豆瓣电影爬虫初始化完成")
    
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
    
    def crawl_movies(self, categories=None, max_movies=None, max_pages=10):
        """
        爬取电影数据
        
        Args:
            categories: 要爬取的分类列表，默认['hot']
            max_movies: 最大爬取电影数量，默认使用配置值
            max_pages: 每个分类最大页数，默认10
            
        Returns:
            tuple: (原始数据, 清洗后数据, 保存文件信息)
        """
        categories = categories or ['hot']
        max_movies = max_movies or self.config.MAX_MOVIES
        
        self.logger.info(f"开始爬取电影数据 - 分类: {categories}, 最大数量: {max_movies}")
        
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
            
            self.logger.info(f"爬虫任务完成！成功获取 {len(cleaned_data)} 部电影信息")
            
            # 返回格式与其他爬虫保持一致
            return {
                'success': True,
                'data_count': len(cleaned_data),
                'file_paths': saved_files,
                'message': f'成功爬取 {len(cleaned_data)} 部电影'
            }
            
        except Exception as e:
            self.logger.error(f"爬虫运行出错: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'爬取失败: {str(e)}'
            }
        finally:
            self.network_manager.close()
    
    def _collect_movie_links(self, list_urls):
        """收集电影详情页链接 - 增强版"""
        all_movie_links = []
        failed_pages = 0
        max_consecutive_fails = 3  # 最大连续失败次数
        consecutive_fails = 0
        
        for i, url in enumerate(tqdm(list_urls, desc="解析电影列表页面")):
            try:
                # 动态调整延时
                if consecutive_fails > 0:
                    delay = random.uniform(
                        self.config.DELAY_MIN * (1 + consecutive_fails), 
                        self.config.DELAY_MAX * (1 + consecutive_fails)
                    )
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(
                        self.config.DELAY_MIN, 
                        self.config.DELAY_MAX
                    ))
                
                # 智能请求策略
                use_selenium = consecutive_fails >= 2  # 连续失败2次后使用Selenium
                response = self.network_manager.get_page(url, force_selenium=use_selenium)
                
                # 确定URL类型
                url_type = 'typerank' if 'typerank' in url else 'chart'
                
                movie_links = self.parser.parse_movie_list(response, url_type)
                
                if len(movie_links) == 0:
                    consecutive_fails += 1
                    failed_pages += 1
                    self.logger.warning(f"页面 {i+1}/{len(list_urls)} 解析失败: {url}")
                    
                    # 如果连续失败次数过多，可能遇到了反爬虫
                    if consecutive_fails >= max_consecutive_fails:
                        self.logger.error(f"连续{max_consecutive_fails}页解析失败，可能遇到反爬虫限制")
                        # 增加更长的延时
                        time.sleep(random.uniform(10, 20))
                        consecutive_fails = 0  # 重置计数器
                else:
                    all_movie_links.extend(movie_links)
                    consecutive_fails = 0  # 成功后重置失败计数
                    self.logger.info(f"页面 {i+1}/{len(list_urls)} 成功获取 {len(movie_links)} 个链接")
                
            except Exception as e:
                failed_pages += 1
                consecutive_fails += 1
                self.logger.warning(f"解析列表页面失败: {url}, 错误: {e}")
                
                # 失败时增加延时
                time.sleep(random.uniform(5, 10))
                continue
        
        # 去重
        unique_links = list(set(all_movie_links))
        success_rate = (len(list_urls) - failed_pages) / len(list_urls) * 100
        
        self.logger.info(f"收集完成 - 成功率: {success_rate:.1f}%, 总链接数: {len(unique_links)}, 失败页面: {failed_pages}")
        
        return unique_links
    
    def _crawl_movie_details(self, movie_links):
        """爬取电影详情"""
        movie_data = []
        
        for link in tqdm(movie_links, desc="爬取电影详情"):
            try:
                response = self.network_manager.get_page(link)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                if movie_info:
                    movie_data.append(movie_info)
                
                # 随机延时避免被封
                time.sleep(random.uniform(
                    self.config.DELAY_MIN, 
                    self.config.DELAY_MAX
                ))
                
            except Exception as e:
                self.logger.warning(f"爬取电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"成功爬取 {len(movie_data)} 部电影详情")
        return movie_data
    
    def get_movie_by_id(self, douban_id):
        """根据豆瓣ID获取单个电影信息"""
        url = f"{self.config.BASE_URL}/subject/{douban_id}/"
        
        try:
            response = self.network_manager.get_page(url)
            movie_info = self.parser.parse_movie_detail(response, url)
            
            if movie_info:
                cleaned_data = self.data_processor.clean_movie_data([movie_info])
                return cleaned_data[0] if cleaned_data else None
            
        except Exception as e:
            self.logger.error(f"获取电影信息失败 (ID: {douban_id}): {e}")
            
        return None
    
    def search_movies(self, keyword, max_results=20):
        """搜索电影（简化版本）"""
        # 注意：豆瓣的搜索可能需要更复杂的处理
        search_url = f"{self.config.BASE_URL}/search?q={keyword}"
        
        try:
            response = self.network_manager.get_page(search_url)
            # 这里需要实现搜索结果页面的解析
            # 由于豆瓣搜索页面结构复杂，这里先返回空列表
            self.logger.warning("搜索功能需要进一步实现")
            return []
            
        except Exception as e:
            self.logger.error(f"搜索电影失败: {e}")
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
            response = self.network_manager.get_page(self.config.BASE_URL)
            return response is not None
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.network_manager.close()
