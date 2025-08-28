#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多平台电影数据爬虫系统
集成豆瓣、IMDB和烂番茄三大平台的电影数据爬取功能
"""

import os
import sys
import logging
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from douban_crawler import DoubanCrawler
from imdb_crawler import IMDBCrawler
from rotten_tomatoes_crawler import RTCrawler


class MultiPlatformCrawler:
    """多平台电影爬虫主控制器"""
    
    def __init__(self):
        """初始化多平台爬虫"""
        self.platforms = {
            'douban': {
                'name': '豆瓣电影',
                'crawler_class': DoubanCrawler,
                'enabled': True
            },
            'imdb': {
                'name': 'IMDB',
                'crawler_class': IMDBCrawler,
                'enabled': True
            },
            'rotten_tomatoes': {
                'name': '烂番茄',
                'crawler_class': RTCrawler,
                'enabled': True
            }
        }
        
        self.logger = self._setup_logging()
        self.logger.info("多平台电影爬虫系统初始化完成")
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('multi_platform_crawler.log', encoding='utf-8')
            ]
        )
        return logging.getLogger(__name__)
    
    def show_menu(self):
        """显示主菜单"""
        print("\n🎬 多平台电影数据爬虫系统 v1.0")
        print("=" * 60)
        print("支持平台：豆瓣电影 | IMDB | 烂番茄")
        print("适用于：大数据真值推荐系统项目")
        print("功能：从多个平台爬取电影数据，为推荐算法提供数据支持")
        print("=" * 60)
        print("\n📋 功能菜单:")
        print("1. 🔥 单平台爬取")
        print("2. 🌍 多平台并行爬取")
        print("3. 📊 平台支持测试")
        print("4. 📈 数据统计分析")
        print("5. 🚪 退出程序")
    
    def run(self):
        """运行主程序"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\n请选择功能 (1-5): ").strip()
                
                if choice == '1':
                    self.single_platform_crawl()
                elif choice == '2':
                    self.multi_platform_crawl()
                elif choice == '3':
                    self.test_platforms()
                elif choice == '4':
                    self.analyze_data()
                elif choice == '5':
                    print("感谢使用多平台电影爬虫系统！")
                    break
                else:
                    print("❌ 无效选择，请输入1-5之间的数字")
                    
            except KeyboardInterrupt:
                print("\n👋 程序被用户中断，退出系统")
                break
            except Exception as e:
                print(f"❌ 程序执行出错: {e}")
                self.logger.error(f"程序执行出错: {e}")
    
    def single_platform_crawl(self):
        """单平台爬取"""
        print("\n🔥 单平台爬取模式")
        print("-" * 30)
        
        # 显示平台选择
        platforms = list(self.platforms.keys())
        for i, platform_key in enumerate(platforms, 1):
            platform = self.platforms[platform_key]
            status = "✅" if platform['enabled'] else "❌"
            print(f"{i}. {status} {platform['name']}")
        
        try:
            choice = int(input(f"\n请选择平台 (1-{len(platforms)}): "))
            if 1 <= choice <= len(platforms):
                platform_key = platforms[choice - 1]
                self._crawl_platform(platform_key)
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
    
    def multi_platform_crawl(self):
        """多平台并行爬取"""
        print("\n🌍 多平台并行爬取模式")
        print("-" * 30)
        
        # 显示启用的平台
        enabled_platforms = [k for k, v in self.platforms.items() if v['enabled']]
        
        if not enabled_platforms:
            print("❌ 没有启用的平台，请检查配置")
            return
        
        print(f"将从以下 {len(enabled_platforms)} 个平台爬取数据：")
        for platform_key in enabled_platforms:
            print(f"• {self.platforms[platform_key]['name']}")
        
        max_movies = self._get_movie_count()
        if max_movies is None:
            return
        
        print(f"\n🚀 开始多平台爬取，每个平台最多 {max_movies} 部电影")
        
        results = {}
        total_movies = 0
        
        for platform_key in enabled_platforms:
            print(f"\n{'='*50}")
            print(f"🎯 正在爬取 {self.platforms[platform_key]['name']} 数据")
            print(f"{'='*50}")
            
            result = self._crawl_platform(platform_key, max_movies, show_details=False)
            results[platform_key] = result
            
            if result and result.get('success'):
                movie_count = len(result.get('data', []))
                total_movies += movie_count
                print(f"✅ {self.platforms[platform_key]['name']} 完成: {movie_count} 部电影")
            else:
                print(f"❌ {self.platforms[platform_key]['name']} 爬取失败")
        
        # 显示总结
        print(f"\n🎉 多平台爬取完成!")
        print(f"📊 总计获取 {total_movies} 部电影信息")
        
        for platform_key, result in results.items():
            if result and result.get('success'):
                count = len(result.get('data', []))
                print(f"  - {self.platforms[platform_key]['name']}: {count} 部")
    
    def _crawl_platform(self, platform_key, max_movies=None, show_details=True):
        """爬取指定平台数据"""
        platform = self.platforms.get(platform_key)
        if not platform or not platform['enabled']:
            print(f"❌ 平台 {platform_key} 未启用或不存在")
            return None
        
        if max_movies is None:
            max_movies = self._get_movie_count()
            if max_movies is None:
                return None
        
        try:
            # 初始化爬虫
            crawler = platform['crawler_class']()
            
            # 获取支持的分类
            categories = list(crawler.get_supported_categories().keys())
            
            # 选择默认分类
            if platform_key == 'douban':
                default_categories = ['hot']
            elif platform_key == 'imdb':
                default_categories = ['popular']
            else:  # rotten_tomatoes
                default_categories = ['most_popular']
            
            print(f"\n🎯 开始爬取 {platform['name']} 数据")
            print(f"📋 分类: {default_categories}")
            print(f"🔢 数量: {max_movies} 部电影")
            
            # 开始爬取
            start_time = time.time()
            result = crawler.crawl_movies(categories=default_categories, max_movies=max_movies)
            end_time = time.time()
            
            if result.get('success'):
                movie_count = len(result.get('data', []))
                elapsed_time = end_time - start_time
                
                if show_details:
                    print(f"\n🎉 爬取完成!")
                    print(f"📊 成功获取 {movie_count} 部电影信息")
                    print(f"⏱️  耗时: {elapsed_time:.1f} 秒")
                    
                    # 显示文件路径
                    file_paths = result.get('file_paths', {})
                    if file_paths:
                        print(f"\n📁 数据文件保存位置:")
                        for format_type, path in file_paths.items():
                            print(f"  - {format_type.upper()}: {path}")
                    
                    # 显示数据预览
                    self._show_data_preview(result.get('data', []), platform_key)
                
                return result
            else:
                error_msg = result.get('error', '未知错误')
                print(f"❌ 爬取失败: {error_msg}")
                return result
                
        except Exception as e:
            print(f"❌ 爬取过程中发生异常: {e}")
            self.logger.error(f"爬取 {platform_key} 时发生异常: {e}")
            return None
    
    def _get_movie_count(self):
        """获取用户输入的电影数量"""
        try:
            count = int(input("请输入要爬取的电影数量 (建议10-50): "))
            if count <= 0:
                print("❌ 数量必须大于0")
                return None
            elif count > 200:
                print("⚠️  数量较大，可能需要很长时间")
                confirm = input("是否继续? (y/n): ")
                if confirm.lower() != 'y':
                    return None
            return count
        except ValueError:
            print("❌ 请输入有效数字")
            return None
    
    def _show_data_preview(self, data, platform_key):
        """显示数据预览"""
        if not data:
            return
        
        print(f"\n🎬 {self.platforms[platform_key]['name']} 数据预览 (前3部电影):")
        print()
        
        for i, movie in enumerate(data[:3], 1):
            if platform_key == 'douban':
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'N/A')
                rating = movie.get('rating', 'N/A')
                genres = movie.get('genres', [])
                directors = movie.get('directors', [])
                actors = movie.get('actors', [])
                
                print(f"{i}. {title}")
                print(f"   📅 年份: {year}")
                print(f"   ⭐ 评分: {rating}")
                print(f"   🎭 类型: {', '.join(genres[:3]) if genres else 'N/A'}")
                print(f"   🎬 导演: {', '.join(directors[:2]) if directors else 'N/A'}")
                print(f"   🎪 主演: {', '.join(actors[:3]) if actors else 'N/A'}")
                
            elif platform_key == 'imdb':
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'N/A')
                rating = movie.get('rating', 'N/A')
                genres = movie.get('genres', [])
                directors = movie.get('directors', [])
                
                print(f"{i}. {title}")
                print(f"   📅 年份: {year}")
                print(f"   ⭐ IMDB评分: {rating}")
                print(f"   🎭 类型: {', '.join(genres[:3]) if genres else 'N/A'}")
                print(f"   🎬 导演: {', '.join(directors[:2]) if directors else 'N/A'}")
                
            else:  # rotten_tomatoes
                title = movie.get('title', 'Unknown')
                year = movie.get('year', 'N/A')
                tomatometer = movie.get('tomatometer_score', 'N/A')
                audience = movie.get('audience_score', 'N/A')
                genres = movie.get('genres', [])
                
                print(f"{i}. {title}")
                print(f"   📅 年份: {year}")
                print(f"   🍅 新鲜度: {tomatometer}%")
                print(f"   🍿 观众评分: {audience}%")
                print(f"   🎭 类型: {', '.join(genres[:3]) if genres else 'N/A'}")
            
            print()
        
        if len(data) > 3:
            print(f"   ... 还有 {len(data) - 3} 部电影")
    
    def test_platforms(self):
        """测试平台连接"""
        print("\n📊 平台支持测试")
        print("-" * 30)
        
        for platform_key, platform in self.platforms.items():
            print(f"🔍 测试 {platform['name']} 连接...", end=' ')
            
            try:
                if platform['enabled']:
                    crawler = platform['crawler_class']()
                    if crawler.test_connection():
                        print("✅ 连接正常")
                    else:
                        print("❌ 连接失败")
                else:
                    print("⚠️  平台未启用")
            except Exception as e:
                print(f"❌ 测试异常: {e}")
    
    def analyze_data(self):
        """分析已爬取的数据"""
        print("\n📈 数据统计分析")
        print("-" * 30)
        
        data_dir = "data"
        if not os.path.exists(data_dir):
            print("❌ 数据目录不存在，请先运行爬虫")
            return
        
        # 统计文件数量
        file_stats = {
            'douban': 0,
            'imdb': 0,
            'rt': 0,
            'total': 0
        }
        
        try:
            files = os.listdir(data_dir)
            for file in files:
                if file.endswith('.json'):
                    file_stats['total'] += 1
                    if 'douban' in file or 'cleaned_movies' in file:
                        file_stats['douban'] += 1
                    elif 'imdb' in file:
                        file_stats['imdb'] += 1
                    elif 'rt' in file:
                        file_stats['rt'] += 1
            
            print(f"📊 数据文件统计:")
            print(f"  - 总文件数: {file_stats['total']}")
            print(f"  - 豆瓣数据: {file_stats['douban']} 个文件")
            print(f"  - IMDB数据: {file_stats['imdb']} 个文件")
            print(f"  - 烂番茄数据: {file_stats['rt']} 个文件")
            
            # 检查海报图片
            poster_dirs = ['posters', 'imdb_posters', 'rt_posters']
            total_images = 0
            
            for poster_dir in poster_dirs:
                poster_path = os.path.join(data_dir, poster_dir)
                if os.path.exists(poster_path):
                    images = [f for f in os.listdir(poster_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    total_images += len(images)
                    print(f"  - {poster_dir}: {len(images)} 张图片")
            
            print(f"🖼️  海报图片总计: {total_images} 张")
            
        except Exception as e:
            print(f"❌ 统计数据时出错: {e}")


def main():
    """主函数"""
    try:
        crawler = MultiPlatformCrawler()
        crawler.run()
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        logging.error(f"程序启动失败: {e}")


if __name__ == "__main__":
    main()
