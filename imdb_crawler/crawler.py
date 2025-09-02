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
        分批爬取IMDB电影数据 - 收集一批链接，解析完毕后再收集下一批
        
        Args:
            categories: 要爬取的分类列表，默认['top250']
            max_movies: 最大爬取电影数量，默认使用配置值
            max_pages: 每个分类最大页数，默认5
            
        Returns:
            dict: 爬取结果信息
        """
        categories = categories or ['top250']
        max_movies = max_movies or self.config.MAX_MOVIES
        
        self.logger.info(f"开始分批爬取IMDB电影数据 - 分类: {categories}, 目标数量: {max_movies}")
        
        try:
            all_movie_data = []
            collected_links = set()  # 避免重复链接
            batch_size = 50  # 每批收集50个链接
            batch_count = 0
            
            while len(all_movie_data) < max_movies:
                batch_count += 1
                remaining = max_movies - len(all_movie_data)
                target_batch_links = min(batch_size, remaining * 2)  # 每批收集的链接数
                
                self.logger.info(f"=== 第 {batch_count} 批IMDB爬取 ===")
                self.logger.info(f"已获取: {len(all_movie_data)} 部电影，还需: {remaining} 部")
                
                # 阶段1：收集一批新的电影链接（不重复）
                self.logger.info(f"阶段1: 收集 {target_batch_links} 个IMDB电影链接...")
                new_links = self._collect_batch_links(categories, target_batch_links, collected_links, max_pages)
                
                if not new_links:
                    self.logger.warning("无法收集到更多IMDB电影链接，爬取结束")
                    break
                
                collected_links.update(new_links)
                self.logger.info(f"✓ 链接收集完成！本批收集 {len(new_links)} 个新链接")
                
                # 阶段2：完全解析这批电影（直到完成或失败）
                self.logger.info(f"阶段2: 开始解析本批 {len(new_links)} 个IMDB电影...")
                batch_movies = self._parse_batch_movies(list(new_links), remaining)
                
                if batch_movies:
                    all_movie_data.extend(batch_movies)
                    self.logger.info(f"✓ 本批解析完成！获取 {len(batch_movies)} 部电影，总计: {len(all_movie_data)}/{max_movies}")
                else:
                    self.logger.warning(f"✗ 本批链接解析失败，跳过继续下一批")
                
                # 如果已达到目标，停止
                if len(all_movie_data) >= max_movies:
                    self.logger.info(f"🎉 已达到目标数量 {max_movies}，爬取任务完成！")
                    break
                
                # 批次间休息
                self.logger.info("批次间休息 5-10 秒...")
                time.sleep(random.uniform(5, 10))
            
            # 数据清洗和最终保存
            if all_movie_data:
                # 限制到目标数量
                final_movies = all_movie_data[:max_movies]
                cleaned_data = self.data_processor.clean_movie_data(final_movies)
                saved_files = self.data_processor.save_processed_data(
                    cleaned_data, 
                    self.config.OUTPUT_DIR
                )
                
                self.logger.info(f"IMDB爬虫任务完成！最终获取 {len(cleaned_data)} 部电影信息")
                
                return {
                    'success': True,
                    'data_count': len(cleaned_data),
                    'file_paths': saved_files,
                    'message': f'成功爬取 {len(cleaned_data)} 部IMDB电影'
                }
            else:
                return {
                    'success': False,
                    'data_count': 0,
                    'file_paths': {},
                    'message': '未获取到任何有效IMDB电影数据'
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
    
    def _collect_batch_links(self, categories, target_count, exclude_links, max_pages):
        """收集一批新的IMDB电影链接（避免重复）"""
        new_links = []
        
        for category in categories:
            if len(new_links) >= target_count:
                break
            
            self.logger.info(f"从IMDB分类 '{category}' 收集链接...")
            category_urls = self.config.get_movie_list_urls([category], max_pages)
            
            for i, url in enumerate(tqdm(category_urls, desc=f"解析IMDB{category}列表页", leave=False)):
                if len(new_links) >= target_count:
                    self.logger.info(f"已收集足够IMDB链接 ({len(new_links)}个)，停止此分类")
                    break
                
                try:
                    # 延时
                    if i > 0:
                        time.sleep(random.uniform(2, 4))
                    
                    # IMDB完全使用Selenium，requests总是被拦截
                    response = self.network_manager.get_page(url, use_selenium=True)
                    
                    # 确定URL类型
                    if 'chart' in url:
                        url_type = 'chart'
                    elif 'search' in url:
                        url_type = 'search'
                    else:
                        url_type = 'chart'
                    
                    # 解析电影链接
                    movie_links = self.parser.parse_movie_list(response, url_type)
                    
                    # 过滤已收集的链接
                    filtered_links = [link for link in movie_links if link not in exclude_links]
                    new_links.extend(filtered_links)
                    
                    if filtered_links:
                        self.logger.info(f"从IMDB页面获取 {len(filtered_links)} 个新链接，累计: {len(new_links)}")
                    else:
                        self.logger.warning(f"IMDB页面无新链接: {url}")
                    
                except Exception as e:
                    self.logger.warning(f"解析IMDB列表页面失败: {url}, 错误: {e}")
                    continue
        
        # 去重并返回需要的数量
        unique_links = list(set(new_links))[:target_count]
        self.logger.info(f"IMDB批次链接收集完成 - 获得 {len(unique_links)} 个新链接")
        return unique_links
    
    def _parse_batch_movies(self, movie_links, max_count):
        """解析一批IMDB电影详情"""
        self.logger.info(f"开始解析 {len(movie_links)} 个IMDB电影详情（最多 {max_count} 部）")
        movie_data = []
        
        for i, link in enumerate(tqdm(movie_links, desc="解析IMDB电影详情", leave=False)):
            if len(movie_data) >= max_count:
                self.logger.info(f"已达到批次目标 {max_count}，停止解析")
                break
            
            try:
                # 延时
                time.sleep(random.uniform(
                    self.config.DELAY_MIN,
                    self.config.DELAY_MAX
                ))
                
                # IMDB完全使用Selenium，requests被拦截
                response = self.network_manager.get_page(link, use_selenium=True)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                if movie_info and movie_info.get('title'):
                    movie_data.append(movie_info)
                    self.logger.info(f"✓ IMDB解析成功: {movie_info.get('title')} ({len(movie_data)}/{max_count})")
                else:
                    self.logger.warning(f"✗ IMDB电影信息不完整: {link}")
                
            except Exception as e:
                self.logger.warning(f"✗ 解析IMDB电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"IMDB批次解析完成 - 成功获取 {len(movie_data)} 部电影")
        return movie_data

    def _collect_sufficient_links(self, categories, target_count, max_pages):
        """收集足够数量的IMDB电影链接"""
        all_movie_links = []
        
        for category in categories:
            if len(all_movie_links) >= target_count * 2:  # 收集足够的链接后停止
                self.logger.info(f"已收集足够IMDB链接 ({len(all_movie_links)}个)，停止解析列表页面")
                break
            
            self.logger.info(f"开始收集IMDB分类 '{category}' 的电影链接")
            category_urls = self.config.get_movie_list_urls([category], max_pages)
            
            for i, url in enumerate(tqdm(category_urls, desc=f"解析IMDB{category}列表页")):
                if len(all_movie_links) >= target_count * 2:  # 达到目标后立即停止
                    self.logger.info(f"已收集到 {len(all_movie_links)} 个IMDB链接，停止解析更多列表页")
                    break
                
                try:
                    # 列表页面延时
                    if i > 0:
                        time.sleep(random.uniform(1, 3))
                    
                    # IMDB完全使用Selenium
                    response = self.network_manager.get_page(url, use_selenium=True)
                    
                    # 确定URL类型
                    if 'chart' in url:
                        url_type = 'chart'
                    elif 'search' in url:
                        url_type = 'search'
                    else:
                        url_type = 'chart'
                    
                    # 解析电影链接
                    movie_links = self.parser.parse_movie_list(response, url_type)
                    
                    if len(movie_links) > 0:
                        all_movie_links.extend(movie_links)
                        self.logger.info(f"从IMDB页面获取 {len(movie_links)} 个链接，总计: {len(all_movie_links)}")
                    else:
                        self.logger.warning(f"IMDB页面无链接，可能被反爬虫拦截: {url}")
                        # 连续失败时增加延时
                        time.sleep(random.uniform(5, 10))
                
                except Exception as e:
                    self.logger.warning(f"解析IMDB列表页面失败: {url}, 错误: {e}")
                    continue
        
        # 去重
        unique_links = list(set(all_movie_links))
        self.logger.info(f"IMDB链接收集阶段完成 - 总链接数: {len(unique_links)}")
        
        return unique_links
    
    def _crawl_movie_details_with_limit(self, movie_links, max_movies):
        """爬取IMDB电影详情（带数量限制）"""
        movie_data = []
        selenium_failures = 0
        
        for i, link in enumerate(tqdm(movie_links, desc="爬取IMDB电影详情")):
            if len(movie_data) >= max_movies:
                self.logger.info(f"已达到IMDB目标数量 {max_movies}，停止爬取详情")
                break
            
            try:
                # 详情页延时
                time.sleep(random.uniform(
                    self.config.DELAY_MIN,
                    self.config.DELAY_MAX
                ))
                
                # IMDB完全使用Selenium，requests被拦截
                response = self.network_manager.get_page(link, use_selenium=True)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                if movie_info and movie_info.get('title'):
                    movie_data.append(movie_info)
                    self.logger.info(f"成功爬取IMDB: {movie_info.get('title')} ({len(movie_data)}/{max_movies})")
                else:
                    self.logger.warning(f"IMDB电影信息解析失败: {link}")
                
            except Exception as e:
                self.logger.warning(f"爬取IMDB电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"IMDB详情爬取完成 - 成功获取 {len(movie_data)} 部电影")
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
            # 使用新的两阶段方法
            movie_links = self._collect_sufficient_links([genre], max_movies, max_pages=3)
            
            if len(movie_links) > max_movies:
                movie_links = random.sample(movie_links, max_movies)
            
            raw_data = self._crawl_movie_details_with_limit(movie_links, max_movies)
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
