#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多平台电影爬虫系统
整合豆瓣和IMDB爬虫，提供统一接口
"""

import os
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from douban_crawler import DoubanMovieCrawler
from imdb_crawler import IMDBMovieCrawler


class MultiPlatformCrawler:
    """多平台电影爬虫管理器"""
    
    def __init__(self, output_dir="data"):
        """
        初始化多平台爬虫
        
        Args:
            output_dir: 数据输出目录
        """
        self.output_dir = output_dir
        self.douban_crawler = None
        self.imdb_crawler = None
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        self.logger.info("多平台电影爬虫系统初始化完成")
    
    def _setup_logging(self):
        """设置日志记录"""
        # 抑制第三方库的详细日志
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('WDM').setLevel(logging.WARNING)
        logging.getLogger('tensorflow').setLevel(logging.ERROR)
        
        # 抑制Chrome DevTools输出
        import os
        os.environ['WDM_LOG'] = '0'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('multi_platform_crawler.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def crawl_all_platforms(self, max_movies_per_platform=100, douban_categories=None, imdb_categories=None):
        """
        同时爬取所有平台数据
        
        Args:
            max_movies_per_platform: 每个平台最大爬取数量
            douban_categories: 豆瓣爬取分类
            imdb_categories: IMDB爬取分类
            
        Returns:
            dict: 包含所有平台爬取结果的字典
        """
        douban_categories = douban_categories or ['hot', 'top250']
        imdb_categories = imdb_categories or ['top250', 'popular']
        
        self.logger.info("开始多平台电影数据爬取")
        results = {}
        
        # 使用线程池并行爬取
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交任务
            futures = {}
            
            # 豆瓣爬虫任务
            douban_future = executor.submit(
                self._crawl_douban_safe, 
                douban_categories, 
                max_movies_per_platform
            )
            futures['douban'] = douban_future
            
            # IMDB爬虫任务
            imdb_future = executor.submit(
                self._crawl_imdb_safe, 
                imdb_categories, 
                max_movies_per_platform
            )
            futures['imdb'] = imdb_future
            
            # 收集结果
            for platform, future in futures.items():
                try:
                    result = future.result(timeout=3600)  # 1小时超时
                    results[platform] = result
                    self.logger.info(f"{platform}爬虫完成: {result.get('message', 'Unknown')}")
                except Exception as e:
                    self.logger.error(f"{platform}爬虫失败: {e}")
                    results[platform] = {
                        'success': False,
                        'data_count': 0,
                        'file_paths': {},
                        'message': f'爬取失败: {str(e)}'
                    }
        
        # 保存综合结果
        summary = self._save_crawl_summary(results)
        results['summary'] = summary
        
        self.logger.info("多平台爬取任务完成")
        return results
    
    def _crawl_douban_safe(self, categories, max_movies):
        """安全的豆瓣爬取方法"""
        try:
            with DoubanMovieCrawler() as crawler:
                self.douban_crawler = crawler
                return crawler.crawl_movies(
                    categories=categories, 
                    max_movies=max_movies
                )
        except Exception as e:
            self.logger.error(f"豆瓣爬虫异常: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'豆瓣爬取失败: {str(e)}'
            }
        finally:
            self.douban_crawler = None
    
    def _crawl_imdb_safe(self, categories, max_movies):
        """安全的IMDB爬取方法"""
        try:
            with IMDBMovieCrawler() as crawler:
                self.imdb_crawler = crawler
                return crawler.crawl_movies(
                    categories=categories, 
                    max_movies=max_movies
                )
        except Exception as e:
            self.logger.error(f"IMDB爬虫异常: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'IMDB爬取失败: {str(e)}'
            }
        finally:
            self.imdb_crawler = None
    
    def crawl_douban_only(self, categories=None, max_movies=100):
        """只爬取豆瓣数据"""
        categories = categories or ['hot', 'top250']
        
        self.logger.info("开始爬取豆瓣电影数据")
        
        try:
            with DoubanMovieCrawler() as crawler:
                result = crawler.crawl_movies(
                    categories=categories, 
                    max_movies=max_movies
                )
                
                self.logger.info(f"豆瓣爬取完成: {result.get('message', 'Unknown')}")
                return result
                
        except Exception as e:
            self.logger.error(f"豆瓣爬取失败: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'豆瓣爬取失败: {str(e)}'
            }
    
    def crawl_imdb_only(self, categories=None, max_movies=100):
        """只爬取IMDB数据"""
        categories = categories or ['top250', 'popular']
        
        self.logger.info("开始爬取IMDB电影数据")
        
        try:
            with IMDBMovieCrawler() as crawler:
                result = crawler.crawl_movies(
                    categories=categories, 
                    max_movies=max_movies
                )
                
                self.logger.info(f"IMDB爬取完成: {result.get('message', 'Unknown')}")
                return result
                
        except Exception as e:
            self.logger.error(f"IMDB爬取失败: {e}")
            return {
                'success': False,
                'data_count': 0,
                'file_paths': {},
                'message': f'IMDB爬取失败: {str(e)}'
            }
    
    def merge_platform_data(self, douban_file=None, imdb_file=None):
        """
        合并不同平台的数据
        
        Args:
            douban_file: 豆瓣数据文件路径
            imdb_file: IMDB数据文件路径
            
        Returns:
            str: 合并后文件路径
        """
        try:
            merged_data = []
            
            # 读取豆瓣数据
            if douban_file and os.path.exists(douban_file):
                with open(douban_file, 'r', encoding='utf-8') as f:
                    douban_data = json.load(f)
                    merged_data.extend(douban_data)
                    self.logger.info(f"加载豆瓣数据: {len(douban_data)} 部电影")
            
            # 读取IMDB数据
            if imdb_file and os.path.exists(imdb_file):
                with open(imdb_file, 'r', encoding='utf-8') as f:
                    imdb_data = json.load(f)
                    merged_data.extend(imdb_data)
                    self.logger.info(f"加载IMDB数据: {len(imdb_data)} 部电影")
            
            # 保存合并数据
            if merged_data:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                merged_file = os.path.join(self.output_dir, f"merged_movies_{timestamp}.json")
                
                with open(merged_file, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"数据合并完成: {merged_file}, 总计 {len(merged_data)} 部电影")
                return merged_file
            
        except Exception as e:
            self.logger.error(f"数据合并失败: {e}")
            
        return None
    
    def _save_crawl_summary(self, results):
        """保存爬取汇总信息"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        summary = {
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_platforms': len(results),
            'successful_platforms': sum(1 for r in results.values() if r.get('success', False)),
            'total_movies': sum(r.get('data_count', 0) for r in results.values()),
            'platform_details': results
        }
        
        summary_file = os.path.join(self.output_dir, f"crawl_summary_{timestamp}.json")
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"爬取汇总已保存: {summary_file}")
            summary['summary_file'] = summary_file
            
        except Exception as e:
            self.logger.error(f"保存爬取汇总失败: {e}")
        
        return summary
    
    def get_supported_platforms(self):
        """获取支持的平台列表"""
        return {
            'douban': {
                'name': '豆瓣电影',
                'categories': ['hot', 'top250', 'new_movies', 'weekly_best', 'classic']
            },
            'imdb': {
                'name': 'IMDB',
                'categories': ['top250', 'popular', 'upcoming', 'in_theaters']
            }
        }
    
    def test_all_connections(self):
        """测试所有平台连接"""
        results = {}
        
        # 测试豆瓣连接
        try:
            with DoubanMovieCrawler() as crawler:
                results['douban'] = crawler.test_connection()
        except Exception as e:
            self.logger.error(f"豆瓣连接测试失败: {e}")
            results['douban'] = False
        
        # 测试IMDB连接
        try:
            with IMDBMovieCrawler() as crawler:
                results['imdb'] = crawler.test_connection()
        except Exception as e:
            self.logger.error(f"IMDB连接测试失败: {e}")
            results['imdb'] = False
        
        return results


def main():
    """主函数 - 演示多平台爬虫使用"""
    # 创建多平台爬虫
    crawler = MultiPlatformCrawler()
    
    # 测试连接
    print("测试平台连接...")
    connections = crawler.test_all_connections()
    for platform, status in connections.items():
        print(f"{platform}: {'连接成功' if status else '连接失败'}")
    
    if not any(connections.values()):
        print("所有平台连接失败，请检查网络连接")
        return
    
    # 开始爬取
    print("\n开始多平台数据爬取...")
    results = crawler.crawl_all_platforms(
        max_movies_per_platform=50,  # 每个平台爬取50部电影用于演示
        douban_categories=['hot'],
        imdb_categories=['top250']
    )
    
    # 显示结果
    print(f"\n爬取结果汇总:")
    print(f"总爬取电影数: {results.get('summary', {}).get('total_movies', 0)}")
    print(f"成功平台数: {results.get('summary', {}).get('successful_platforms', 0)}")
    
    for platform, result in results.items():
        if platform != 'summary':
            status = "成功" if result.get('success', False) else "失败"
            count = result.get('data_count', 0)
            print(f"{platform}: {status} (获取 {count} 部电影)")


if __name__ == "__main__":
    main()
