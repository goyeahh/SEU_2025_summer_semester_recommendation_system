#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大数据真值推荐系统 - 爬虫模块主入口
支持豆瓣和IMDB多平台电影数据爬取
"""

import argparse
import sys
import os
from datetime import datetime

from run_multi_platform_crawler import MultiPlatformCrawler


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='大数据真值推荐系统 - 电影爬虫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --platform all --max-movies 100
  D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --platform douban --categories hot top250
  D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --platform imdb --categories top250 popular
  D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --test-connection
        """
    )
    
    parser.add_argument(
        '--platform', 
        choices=['all', 'douban', 'imdb'],
        default='all',
        help='选择爬取平台 (默认: all)'
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        help='选择爬取分类'
    )
    
    parser.add_argument(
        '--max-movies',
        type=int,
        default=100,
        help='每个平台最大爬取电影数量 (默认: 100)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data',
        help='数据输出目录 (默认: data)'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='测试平台连接状态'
    )
    
    parser.add_argument(
        '--list-categories',
        action='store_true',
        help='列出支持的分类'
    )
    
    parser.add_argument(
        '--merge-data',
        nargs=2,
        metavar=('DOUBAN_FILE', 'IMDB_FILE'),
        help='合并豆瓣和IMDB数据文件'
    )
    
    args = parser.parse_args()
    
    # 创建爬虫实例
    crawler = MultiPlatformCrawler(output_dir=args.output_dir)
    
    # 处理不同命令
    if args.test_connection:
        test_connections(crawler)
        return
    
    if args.list_categories:
        list_categories(crawler)
        return
    
    if args.merge_data:
        merge_data(crawler, args.merge_data[0], args.merge_data[1])
        return
    
    # 执行爬取任务
    execute_crawl(crawler, args)


def test_connections(crawler):
    """测试平台连接"""
    print("正在测试平台连接...")
    print("=" * 50)
    
    connections = crawler.test_all_connections()
    
    for platform, status in connections.items():
        status_text = "✓ 连接成功" if status else "✗ 连接失败"
        platform_name = "豆瓣电影" if platform == 'douban' else "IMDB"
        print(f"{platform_name:10}: {status_text}")
    
    print("=" * 50)
    
    if any(connections.values()):
        print("至少有一个平台连接正常，可以开始爬取")
    else:
        print("所有平台连接失败，请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否需要配置代理")
        print("3. Chrome浏览器是否正确安装")


def list_categories(crawler):
    """列出支持的分类"""
    print("支持的平台和分类:")
    print("=" * 50)
    
    platforms = crawler.get_supported_platforms()
    
    for platform_key, platform_info in platforms.items():
        platform_name = platform_info['name']
        categories = platform_info['categories']
        
        print(f"\n{platform_name} ({platform_key}):")
        for category in categories:
            print(f"  - {category}")
    
    print("=" * 50)
    print("使用方法:")
    print("python main.py --platform douban --categories hot top250")
    print("python main.py --platform imdb --categories top250 popular")


def merge_data(crawler, douban_file, imdb_file):
    """合并数据文件"""
    print(f"正在合并数据文件...")
    print(f"豆瓣文件: {douban_file}")
    print(f"IMDB文件: {imdb_file}")
    
    if not os.path.exists(douban_file):
        print(f"错误: 豆瓣文件不存在: {douban_file}")
        return
    
    if not os.path.exists(imdb_file):
        print(f"错误: IMDB文件不存在: {imdb_file}")
        return
    
    merged_file = crawler.merge_platform_data(douban_file, imdb_file)
    
    if merged_file:
        print(f"✓ 数据合并成功: {merged_file}")
    else:
        print("✗ 数据合并失败")


def execute_crawl(crawler, args):
    """执行爬取任务"""
    print("大数据真值推荐系统 - 电影爬虫")
    print("=" * 50)
    print(f"爬取平台: {args.platform}")
    print(f"最大电影数: {args.max_movies}")
    print(f"输出目录: {args.output_dir}")
    if args.categories:
        print(f"指定分类: {', '.join(args.categories)}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        if args.platform == 'all':
            # 爬取所有平台
            douban_categories = args.categories if args.categories else ['hot', 'top250']
            imdb_categories = args.categories if args.categories else ['top250', 'popular']
            
            results = crawler.crawl_all_platforms(
                max_movies_per_platform=args.max_movies,
                douban_categories=douban_categories,
                imdb_categories=imdb_categories
            )
            
            print_all_results(results)
            
        elif args.platform == 'douban':
            # 只爬取豆瓣
            categories = args.categories if args.categories else ['hot', 'top250']
            result = crawler.crawl_douban_only(
                categories=categories,
                max_movies=args.max_movies
            )
            
            print_single_result('豆瓣', result)
            
        elif args.platform == 'imdb':
            # 只爬取IMDB
            categories = args.categories if args.categories else ['top250', 'popular']
            result = crawler.crawl_imdb_only(
                categories=categories,
                max_movies=args.max_movies
            )
            
            print_single_result('IMDB', result)
        
    except KeyboardInterrupt:
        print("\n用户中断爬取任务")
        sys.exit(1)
    except Exception as e:
        print(f"\n爬取任务执行失败: {e}")
        sys.exit(1)


def print_all_results(results):
    """打印所有平台结果"""
    print("\n爬取结果汇总:")
    print("=" * 50)
    
    summary = results.get('summary', {})
    total_movies = summary.get('total_movies', 0)
    successful_platforms = summary.get('successful_platforms', 0)
    total_platforms = summary.get('total_platforms', 0)
    
    print(f"总爬取电影数: {total_movies}")
    print(f"成功平台数: {successful_platforms}/{total_platforms}")
    
    print("\n各平台详情:")
    for platform, result in results.items():
        if platform != 'summary':
            platform_name = "豆瓣" if platform == 'douban' else "IMDB"
            status = "成功" if result.get('success', False) else "失败"
            count = result.get('data_count', 0)
            message = result.get('message', '')
            
            print(f"  {platform_name}: {status} - {count}部电影")
            if message:
                print(f"    消息: {message}")
            
            # 显示保存的文件
            files = result.get('file_paths', {})
            if files:
                print(f"    保存文件:")
                for file_type, file_path in files.items():
                    print(f"      {file_type}: {file_path}")
    
    # 显示汇总文件
    if 'summary_file' in summary:
        print(f"\n汇总报告: {summary['summary_file']}")


def print_single_result(platform_name, result):
    """打印单个平台结果"""
    print(f"\n{platform_name}爬取结果:")
    print("=" * 50)
    
    status = "成功" if result.get('success', False) else "失败"
    count = result.get('data_count', 0)
    message = result.get('message', '')
    
    print(f"状态: {status}")
    print(f"获取电影数: {count}")
    if message:
        print(f"消息: {message}")
    
    # 显示保存的文件
    files = result.get('file_paths', {})
    if files:
        print("\n保存文件:")
        for file_type, file_path in files.items():
            print(f"  {file_type}: {file_path}")


if __name__ == "__main__":
    main()

# 爬取命令示例：
# 豆瓣 - 250部，8个不同分类
# D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --platform douban --max-movies 25 --categories hot top250 new_movies weekly_best classic comedy action romance
# IMDB - 250部，4个不同分类
# D:\Anaconda_envs\envs\Recommendation_System\python.exe main.py --platform imdb --max-movies 25 --categories top250