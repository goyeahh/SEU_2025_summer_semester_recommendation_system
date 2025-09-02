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
        分批爬取电影数据 - 收集一批链接，解析完毕后再收集下一批
        
        Args:
            categories: 要爬取的分类列表，默认['hot']
            max_movies: 最大爬取电影数量，默认使用配置值
            max_pages: 每个分类最大页数，默认10
            
        Returns:
            dict: 爬取结果信息
        """
        categories = categories or ['hot']
        max_movies = max_movies or self.config.MAX_MOVIES
        
        self.logger.info(f"开始分批爬取豆瓣电影数据 - 分类: {categories}, 目标数量: {max_movies}")
        
        try:
            all_movie_data = []
            collected_links = set()  # 避免重复链接
            batch_size = 50  # 每批收集50个链接
            batch_count = 0
            
            while len(all_movie_data) < max_movies:
                batch_count += 1
                remaining = max_movies - len(all_movie_data)
                target_batch_links = min(batch_size, remaining * 2)  # 每批收集的链接数
                
                self.logger.info(f"=== 第 {batch_count} 批爬取 ===")
                self.logger.info(f"已获取: {len(all_movie_data)} 部电影，还需: {remaining} 部")
                
                # 阶段1：收集一批新的电影链接（不重复）
                self.logger.info(f"阶段1: 收集 {target_batch_links} 个豆瓣电影链接...")
                new_links = self._collect_batch_links(categories, target_batch_links, collected_links, max_pages)
                
                if not new_links:
                    self.logger.warning("无法收集到更多豆瓣电影链接，爬取结束")
                    break
                
                collected_links.update(new_links)
                self.logger.info(f"✓ 链接收集完成！本批收集 {len(new_links)} 个新链接")
                
                # 阶段2：完全解析这批电影（直到完成或失败）
                self.logger.info(f"阶段2: 开始解析本批 {len(new_links)} 个豆瓣电影...")
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
                
                self.logger.info(f"豆瓣爬虫任务完成！最终获取 {len(cleaned_data)} 部电影信息")
                
                return {
                    'success': True,
                    'data_count': len(cleaned_data),
                    'file_paths': saved_files,
                    'message': f'成功爬取 {len(cleaned_data)} 部豆瓣电影'
                }
            else:
                return {
                    'success': False,
                    'data_count': 0,
                    'file_paths': {},
                    'message': '未获取到任何有效豆瓣电影数据'
                }
            
        except Exception as e:
            self.logger.error(f"豆瓣爬虫运行出错: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'豆瓣爬取失败: {str(e)}'
            }
        finally:
            self.network_manager.close()
    
    def _collect_batch_links(self, categories, target_count, exclude_links, max_pages):
        """收集一批新的电影链接（避免重复）"""
        new_links = []
        
        for category in categories:
            if len(new_links) >= target_count:
                break
            
            self.logger.info(f"从分类 '{category}' 收集链接...")
            category_urls = self.config.get_movie_list_urls([category], max_pages)
            
            for i, url in enumerate(tqdm(category_urls, desc=f"解析{category}列表页", leave=False)):
                if len(new_links) >= target_count:
                    self.logger.info(f"已收集足够链接 ({len(new_links)}个)，停止此分类")
                    break
                
                try:
                    # 延时
                    if i > 0:
                        time.sleep(random.uniform(2, 4))
                    
                    # 获取页面内容
                    response = self.network_manager.get_page(url, use_selenium=False)
                    
                    # 解析电影链接
                    movie_links = self.parser.parse_movie_list(response)
                    
                    if not movie_links:
                        # 尝试Selenium
                        self.logger.info(f"requests未获取到链接，尝试Selenium: {url}")
                        response = self.network_manager.get_page(url, use_selenium=True)
                        movie_links = self.parser.parse_movie_list(response)
                    
                    # 过滤已收集的链接
                    filtered_links = [link for link in movie_links if link not in exclude_links]
                    new_links.extend(filtered_links)
                    
                    if filtered_links:
                        self.logger.info(f"从页面获取 {len(filtered_links)} 个新链接，累计: {len(new_links)}")
                    
                except Exception as e:
                    self.logger.warning(f"解析列表页面失败: {url}, 错误: {e}")
                    continue
        
        # 去重并返回需要的数量
        unique_links = list(set(new_links))[:target_count]
        self.logger.info(f"批次链接收集完成 - 获得 {len(unique_links)} 个新链接")
        return unique_links
    
    def _parse_batch_movies(self, movie_links, max_count):
        """解析一批电影详情"""
        self.logger.info(f"开始解析 {len(movie_links)} 个电影详情（最多 {max_count} 部）")
        movie_data = []
        
        for i, link in enumerate(tqdm(movie_links, desc="解析电影详情", leave=False)):
            if len(movie_data) >= max_count:
                self.logger.info(f"已达到批次目标 {max_count}，停止解析")
                break
            
            try:
                # 延时
                time.sleep(random.uniform(
                    self.config.DELAY_MIN,
                    self.config.DELAY_MAX
                ))
                
                # 首先尝试requests
                response = self.network_manager.get_page(link, use_selenium=False)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                # 如果数据不完整，尝试Selenium
                if not movie_info or not self._is_movie_info_complete(movie_info):
                    self.logger.info(f"requests数据不完整，使用Selenium重试: {link}")
                    response = self.network_manager.get_page(link, use_selenium=True)
                    movie_info = self.parser.parse_movie_detail(response, link)
                
                if movie_info and movie_info.get('title'):
                    movie_data.append(movie_info)
                    self.logger.info(f"✓ 解析成功: {movie_info.get('title')} ({len(movie_data)}/{max_count})")
                
            except Exception as e:
                self.logger.warning(f"✗ 解析电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"批次解析完成 - 成功获取 {len(movie_data)} 部电影")
        return movie_data

    def _collect_sufficient_links(self, categories, target_count, max_pages):
        all_movie_links = []
        
        for category in categories:
            if len(all_movie_links) >= target_count * 2:  # 收集足够的链接后停止
                self.logger.info(f"已收集足够链接 ({len(all_movie_links)}个)，停止解析列表页面")
                break
            
            self.logger.info(f"开始收集分类 '{category}' 的电影链接")
            category_urls = self.config.get_movie_list_urls([category], max_pages)
            
            for i, url in enumerate(tqdm(category_urls, desc=f"解析{category}列表页")):
                if len(all_movie_links) >= target_count * 2:  # 达到目标后立即停止
                    self.logger.info(f"已收集到 {len(all_movie_links)} 个链接，停止解析更多列表页")
                    break
                
                try:
                    # 添加延时
                    if i > 0:
                        time.sleep(random.uniform(
                            self.config.DELAY_MIN,
                            self.config.DELAY_MAX
                        ))
                    
                    # 使用Selenium获取页面
                    response = self.network_manager.get_page(url, force_selenium=True)
                    
                    # 确定URL类型
                    url_type = 'typerank' if 'typerank' in url else 'chart'
                    
                    # 解析电影链接
                    movie_links = self.parser.parse_movie_list(response, url_type)
                    
                    if len(movie_links) > 0:
                        all_movie_links.extend(movie_links)
                        self.logger.info(f"从页面获取 {len(movie_links)} 个链接，总计: {len(all_movie_links)}")
                    else:
                        self.logger.warning(f"页面无链接，可能被反爬虫拦截: {url}")
                        # 如果连续失败，增加延时
                        time.sleep(random.uniform(5, 10))
                
                except Exception as e:
                    self.logger.warning(f"解析列表页面失败: {url}, 错误: {e}")
                    continue
        
        # 去重
        unique_links = list(set(all_movie_links))
        self.logger.info(f"收集阶段完成 - 总链接数: {len(unique_links)}")
        
        return unique_links
    
    def _crawl_movie_details_with_limit(self, movie_links, max_movies):
        """爬取电影详情（带数量限制）"""
        movie_data = []
        
        for i, link in enumerate(tqdm(movie_links, desc="爬取电影详情")):
            if len(movie_data) >= max_movies:
                self.logger.info(f"已达到目标数量 {max_movies}，停止爬取详情")
                break
            
            try:
                # 详情页延时
                time.sleep(random.uniform(
                    self.config.DELAY_MIN,
                    self.config.DELAY_MAX
                ))
                
                # 爬取详情
                response = self.network_manager.get_page(link)
                movie_info = self.parser.parse_movie_detail(response, link)
                
                if movie_info and movie_info.get('title'):
                    movie_data.append(movie_info)
                    self.logger.info(f"成功爬取: {movie_info.get('title')} ({len(movie_data)}/{max_movies})")
                else:
                    self.logger.warning(f"电影信息解析失败: {link}")
                
            except Exception as e:
                self.logger.warning(f"爬取电影详情失败: {link}, 错误: {e}")
                continue
        
        self.logger.info(f"详情爬取完成 - 成功获取 {len(movie_data)} 部电影")
        return movie_data
    
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
    
    def _stream_crawl_category(self, category_urls, category_name, max_movies):
        """
        流式爬取分类电影 - 边解析边爬取
        
        Args:
            category_urls: 该分类的列表页URLs
            category_name: 分类名称
            max_movies: 该分类最大电影数量
            
        Returns:
            list: 爬取到的电影数据
        """
        collected_movies = []
        processed_urls = 0
        
        for url in tqdm(category_urls, desc=f"处理{category_name}分类"):
            if len(collected_movies) >= max_movies:
                self.logger.info(f"分类 {category_name} 已达到目标数量 {max_movies}")
                break
            
            try:
                # 添加随机延时，避免请求过快
                if processed_urls > 0:
                    delay = random.uniform(
                        self.config.DELAY_MIN * 2,  # 增加延时
                        self.config.DELAY_MAX * 2
                    )
                    time.sleep(delay)
                
                # 获取列表页
                response = self.network_manager.get_page(url, force_selenium=True)  # 优先使用Selenium
                
                # 确定URL类型
                url_type = 'typerank' if 'typerank' in url else 'chart'
                
                # 解析电影链接
                movie_links = self.parser.parse_movie_list(response, url_type)
                
                if len(movie_links) == 0:
                    self.logger.warning(f"列表页面无电影链接: {url}")
                    processed_urls += 1
                    continue
                
                # 立即爬取这批电影的详情
                for link in movie_links:
                    if len(collected_movies) >= max_movies:
                        break
                    
                    try:
                        # 随机延时
                        time.sleep(random.uniform(
                            self.config.DELAY_MIN,
                            self.config.DELAY_MAX
                        ))
                        
                        # 爬取详情
                        detail_response = self.network_manager.get_page(link)
                        movie_info = self.parser.parse_movie_detail(detail_response, link)
                        
                        if movie_info and movie_info.get('title'):  # 基本验证
                            collected_movies.append(movie_info)
                            self.logger.info(f"成功爬取: {movie_info.get('title')} ({len(collected_movies)}/{max_movies})")
                        
                    except Exception as e:
                        self.logger.warning(f"爬取电影详情失败: {link}, 错误: {e}")
                        continue
                
                processed_urls += 1
                
            except Exception as e:
                self.logger.warning(f"处理列表页面失败: {url}, 错误: {e}")
                processed_urls += 1
                continue
        
        return collected_movies

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
