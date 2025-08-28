#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆瓣电影爬虫系统主程序
用于大数据真值推荐系统项目的数据采集模块
"""

import sys
import os
from douban_crawler import DoubanMovieCrawler, Config


def main():
    """主函数"""
    print("🎬 豆瓣电影爬虫系统 v1.0")
    print("=" * 50)
    print("适用于：大数据真值推荐系统项目")
    print("功能：从豆瓣官网爬取电影数据，为推荐算法提供数据支持")
    print("=" * 50)
    
    # 显示菜单
    show_menu()
    
    while True:
        try:
            choice = input("\n请选择功能 (1-4): ").strip()
            
            if choice == "1":
                run_simple_crawl()
            elif choice == "2":
                run_batch_crawl()
            elif choice == "3":
                run_custom_crawl()
            elif choice == "4":
                print("感谢使用豆瓣电影爬虫系统！")
                break
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，程序退出")
            break
        except Exception as e:
            print(f"❌ 程序运行出错: {e}")


def show_menu():
    """显示功能菜单"""
    print("\n📋 功能菜单:")
    print("1. 🔥 简单爬取 (推荐) - 爬取50部热门电影")
    print("2. 📦 批量爬取 - 爬取多个分类的电影数据")
    print("3. ⚙️  自定义爬取 - 自定义爬取参数")
    print("4. 🚪 退出程序")


def run_simple_crawl():
    """运行简单爬取"""
    print("\n🔥 开始简单爬取模式")
    print("-" * 30)
    
    try:
        with DoubanMovieCrawler() as crawler:
            raw_data, cleaned_data, saved_files = crawler.crawl_movies(
                categories=['hot'],
                max_movies=50,
                max_pages=5
            )
            
            show_results(cleaned_data, saved_files)
            
    except Exception as e:
        print(f"❌ 爬取失败: {e}")


def run_batch_crawl():
    """运行批量爬取"""
    print("\n📦 开始批量爬取模式")
    print("-" * 30)
    
    # 批量爬取配置
    batch_configs = [
        {"categories": ["hot"], "max_movies": 80, "name": "热门电影"},
        {"categories": ["new_movies"], "max_movies": 30, "name": "新片推荐"},
        {"categories": ["classic"], "max_movies": 40, "name": "经典电影"}
    ]
    
    all_data = []
    all_files = {}
    
    for i, config in enumerate(batch_configs, 1):
        print(f"\n第 {i}/{len(batch_configs)} 批：{config['name']}")
        
        try:
            with DoubanMovieCrawler() as crawler:
                raw_data, cleaned_data, saved_files = crawler.crawl_movies(
                    categories=config["categories"],
                    max_movies=config["max_movies"],
                    max_pages=5
                )
                
                all_data.extend(cleaned_data)
                all_files[config['name']] = saved_files
                
                print(f"✅ {config['name']} 完成: {len(cleaned_data)} 部电影")
                
        except Exception as e:
            print(f"❌ {config['name']} 失败: {e}")
    
    # 显示总结
    print(f"\n📊 批量爬取总结:")
    print(f"总计获得: {len(all_data)} 部电影")
    
    for name, files in all_files.items():
        print(f"\n{name} 数据文件:")
        for file_type, filepath in files.items():
            print(f"  - {file_type.upper()}: {filepath}")


def run_custom_crawl():
    """运行自定义爬取"""
    print("\n⚙️ 自定义爬取模式")
    print("-" * 30)
    
    try:
        # 获取用户输入
        print("📝 请设置爬取参数:")
        
        # 选择分类
        print("\n可选分类:")
        print("1. hot - 热门电影")
        print("2. new_movies - 新片推荐")
        print("3. classic - 经典电影")
        
        category_input = input("请输入要爬取的分类 (用逗号分隔，如: hot,new_movies): ").strip()
        categories = [c.strip() for c in category_input.split(',') if c.strip()]
        
        if not categories:
            categories = ['hot']
            print("使用默认分类: hot")
        
        # 设置数量
        try:
            max_movies = int(input("请输入最大爬取数量 (默认100): ") or 100)
        except ValueError:
            max_movies = 100
            print("使用默认数量: 100")
        
        # 设置页数
        try:
            max_pages = int(input("请输入每个分类的最大页数 (默认10): ") or 10)
        except ValueError:
            max_pages = 10
            print("使用默认页数: 10")
        
        print(f"\n开始爬取:")
        print(f"- 分类: {', '.join(categories)}")
        print(f"- 最大数量: {max_movies}")
        print(f"- 最大页数: {max_pages}")
        
        # 开始爬取
        with DoubanMovieCrawler() as crawler:
            raw_data, cleaned_data, saved_files = crawler.crawl_movies(
                categories=categories,
                max_movies=max_movies,
                max_pages=max_pages
            )
            
            show_results(cleaned_data, saved_files)
            
    except Exception as e:
        print(f"❌ 自定义爬取失败: {e}")


def show_results(cleaned_data, saved_files):
    """显示爬取结果"""
    print(f"\n🎉 爬取完成!")
    print(f"📊 成功获取 {len(cleaned_data)} 部电影信息")
    
    # 显示保存的文件
    print(f"\n📁 数据文件保存位置:")
    for file_type, filepath in saved_files.items():
        print(f"  - {file_type.upper()}: {filepath}")
    
    # 显示数据预览
    if cleaned_data:
        print(f"\n🎬 数据预览 (前3部电影):")
        for i, movie in enumerate(cleaned_data[:3], 1):
            print(f"\n{i}. {movie.get('title', '未知')}")
            print(f"   📅 年份: {movie.get('year', 'N/A')}")
            print(f"   ⭐ 评分: {movie.get('rating', 'N/A')}")
            print(f"   🎭 类型: {', '.join(movie.get('genres', []))}")
            print(f"   🎬 导演: {', '.join(movie.get('directors', []))}")
            print(f"   🎪 主演: {', '.join(movie.get('actors', [])[:3])}")
        
        if len(cleaned_data) > 3:
            print(f"\n   ... 还有 {len(cleaned_data) - 3} 部电影")
    
    # 数据统计
    if cleaned_data:
        print(f"\n📈 数据统计:")
        ratings = [m.get('rating', 0) for m in cleaned_data if m.get('rating')]
        if ratings:
            print(f"   平均评分: {sum(ratings)/len(ratings):.2f}")
            print(f"   评分范围: {min(ratings):.1f} - {max(ratings):.1f}")
        
        # 统计类型分布
        all_genres = []
        for movie in cleaned_data:
            all_genres.extend(movie.get('genres', []))
        
        if all_genres:
            from collections import Counter
            top_genres = Counter(all_genres).most_common(5)
            print(f"   热门类型: {', '.join([f'{g}({c})' for g, c in top_genres])}")


if __name__ == "__main__":
    main()
