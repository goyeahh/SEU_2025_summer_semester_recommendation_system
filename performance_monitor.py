#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爬虫性能监控脚本
实时监控爬虫性能指标
"""

import time
import os
import json
from datetime import datetime
import threading


class CrawlerPerformanceMonitor:
    """爬虫性能监控器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = {
            'douban': {
                'movies_crawled': 0,
                'total_time': 0,
                'avg_time_per_movie': 0,
                'success_rate': 0,
                'requests_count': 0,
                'selenium_count': 0
            },
            'imdb': {
                'movies_crawled': 0,
                'total_time': 0,
                'avg_time_per_movie': 0,
                'success_rate': 0,
                'requests_count': 0,
                'selenium_count': 0
            }
        }
        self.is_monitoring = False
    
    def start_monitoring(self):
        """开始监控"""
        self.is_monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        print("🚀 爬虫性能监控已启动...")
        print("=" * 70)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            self._update_metrics()
            self._print_status()
            time.sleep(10)  # 每10秒更新一次
    
    def _update_metrics(self):
        """更新性能指标"""
        # 检查日志文件
        self._parse_douban_log()
        self._parse_imdb_log()
    
    def _parse_douban_log(self):
        """解析豆瓣爬虫日志"""
        log_file = "douban_crawler.log"
        if not os.path.exists(log_file):
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            movies_count = 0
            success_count = 0
            
            for line in lines:
                if "成功解析电影" in line:
                    movies_count += 1
                    success_count += 1
                elif "解析电影详情失败" in line:
                    movies_count += 1
            
            if movies_count > 0:
                self.metrics['douban']['movies_crawled'] = success_count
                self.metrics['douban']['success_rate'] = success_count / movies_count * 100
                
        except Exception:
            pass
    
    def _parse_imdb_log(self):
        """解析IMDB爬虫日志"""
        log_file = "imdb_crawler.log"
        if not os.path.exists(log_file):
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            movies_count = 0
            success_count = 0
            requests_used = 0
            selenium_used = 0
            
            for line in lines:
                if "成功解析电影" in line:
                    movies_count += 1
                    success_count += 1
                elif "解析电影详情失败" in line:
                    movies_count += 1
                elif "requests数据不完整" in line or "使用Selenium重试" in line:
                    selenium_used += 1
                elif "requests获取链接" in line:
                    requests_used += 1
            
            if movies_count > 0:
                self.metrics['imdb']['movies_crawled'] = success_count
                self.metrics['imdb']['success_rate'] = success_count / movies_count * 100
                self.metrics['imdb']['requests_count'] = requests_used
                self.metrics['imdb']['selenium_count'] = selenium_used
                
        except Exception:
            pass
    
    def _print_status(self):
        """打印当前状态"""
        current_time = datetime.now()
        elapsed = (current_time - self.start_time).total_seconds()
        
        print(f"\n⏰ 运行时间: {elapsed:.1f}秒 | {current_time.strftime('%H:%M:%S')}")
        print("=" * 70)
        
        # 豆瓣爬虫状态
        douban = self.metrics['douban']
        print(f"🎬 豆瓣爬虫:")
        print(f"   电影数量: {douban['movies_crawled']:>3} | 成功率: {douban['success_rate']:>5.1f}%")
        
        # IMDB爬虫状态
        imdb = self.metrics['imdb']
        print(f"🎭 IMDB爬虫:")
        print(f"   电影数量: {imdb['movies_crawled']:>3} | 成功率: {imdb['success_rate']:>5.1f}%")
        print(f"   Requests: {imdb['requests_count']:>3} | Selenium: {imdb['selenium_count']:>3}")
        
        # 性能对比
        if douban['movies_crawled'] > 0 and imdb['movies_crawled'] > 0:
            douban_speed = douban['movies_crawled'] / elapsed * 60
            imdb_speed = imdb['movies_crawled'] / elapsed * 60
            
            print("\n📊 性能对比 (电影/分钟):")
            print(f"   豆瓣: {douban_speed:.1f} | IMDB: {imdb_speed:.1f}")
            
            if imdb_speed > douban_speed:
                print("   ✅ IMDB优化成功！")
            elif imdb_speed == douban_speed:
                print("   ⚖️  性能相当")
            else:
                print("   🔧 IMDB仍需优化")
        
        print("=" * 70)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        print("\n📋 性能监控已停止")
        self._save_final_report()
    
    def _save_final_report(self):
        """保存最终报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"performance_report_{timestamp}.json"
        
        report = {
            'timestamp': timestamp,
            'total_runtime': (datetime.now() - self.start_time).total_seconds(),
            'metrics': self.metrics
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 性能报告已保存: {report_file}")


if __name__ == "__main__":
    monitor = CrawlerPerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
