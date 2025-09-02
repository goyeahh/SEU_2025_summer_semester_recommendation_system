#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据处理模块
负责豆瓣数据清洗和文件输出
"""

import pandas as pd
import json
import re
import os
import requests
import urllib.parse
from datetime import datetime
import logging
import numpy as np

from .config import Config


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 创建图片存储目录
        self.poster_dir = "data/douban_posters"
        if not os.path.exists(self.poster_dir):
            os.makedirs(self.poster_dir)
    
    def clean_movie_data(self, raw_data):
        """清洗电影数据"""
        cleaned_data = []
        
        for movie in raw_data:
            if not movie or not self._is_valid_movie(movie):
                continue
            
            cleaned_movie = self._clean_single_movie(movie)
            if cleaned_movie:
                cleaned_data.append(cleaned_movie)
        
        self.logger.info(f"数据清洗完成，有效数据: {len(cleaned_data)} 条")
        return cleaned_data
    
    def _is_valid_movie(self, movie):
        """验证电影数据是否有效 - 放宽验证条件"""
        # 只要有豆瓣ID和标题之一即可，评分可以为空
        return (movie.get('douban_id') or 
                (movie.get('title') and movie.get('title').strip()))
    
    def save_raw_data(self, raw_data, file_path):
        """保存原始数据 - 用于进度保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            return file_path
        except Exception as e:
            self.logger.error(f"保存原始数据失败: {e}")
            return None
    
    def _clean_single_movie(self, movie):
        """清洗单个电影数据"""
        try:
            cleaned = {
                # 基本信息
                'douban_id': str(movie['douban_id']),
                'title': self._clean_text(movie['title']),
                'url': movie['url'],
                'year': movie.get('year'),
                
                # 评分信息
                'rating': float(movie.get('rating', 0)),
                'rating_count': int(movie.get('rating_count', 0)),
                
                # 演职人员
                'directors': self._clean_list(movie.get('directors', [])),
                'actors': self._clean_list(movie.get('actors', [])),
                
                # 电影信息
                'genres': self._clean_list(movie.get('genres', [])),
                'countries': self._clean_list(movie.get('countries', [])),
                'languages': self._clean_list(movie.get('languages', [])),
                'release_dates': self._clean_list(movie.get('release_dates', [])),
                
                # 技术信息
                'runtime_minutes': movie.get('runtime_minutes'),
                'imdb_id': movie.get('imdb_id'),
                
                # 文本信息
                'summary': self._clean_summary(movie.get('summary', '')),
                'tags': self._clean_list(movie.get('tags', [])),
                
                # 评分分布
                'star_5': float(movie.get('star_5', 0)),
                'star_4': float(movie.get('star_4', 0)),
                'star_3': float(movie.get('star_3', 0)),
                'star_2': float(movie.get('star_2', 0)),
                'star_1': float(movie.get('star_1', 0)),
            }
            
            # 处理封面图片
            cleaned['poster_path'] = self._download_poster(movie.get('poster_url'), cleaned['douban_id'])
            
            # 添加计算字段
            cleaned.update(self._add_computed_fields(cleaned))
            
            return cleaned
            
        except Exception as e:
            self.logger.warning(f"清洗电影数据失败: {movie.get('title', 'Unknown')}, 错误: {e}")
            return None
    
    def _clean_text(self, text):
        """清洗文本"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', str(text)).strip()
    
    def _clean_list(self, lst):
        """清洗列表"""
        if not lst:
            return []
        return [self._clean_text(item) for item in lst if item]
    
    def _clean_summary(self, summary):
        """清洗电影简介"""
        if not summary:
            return ""
        
        # 移除多余的空白字符
        summary = re.sub(r'\s+', ' ', str(summary)).strip()
        
        # 限制长度
        max_length = 500  # 简介最大长度
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def _add_computed_fields(self, movie):
        """添加计算字段"""
        computed = {}
        
        # 评分相关计算
        computed['rating_normalized'] = movie['rating'] / 10.0
        computed['rating_count_log'] = np.log1p(movie['rating_count'])
        
        # 时长标准化
        if movie['runtime_minutes']:
            computed['runtime_normalized'] = min(movie['runtime_minutes'] / 180.0, 2.0)
        else:
            computed['runtime_normalized'] = 0.0
        
        # 评分分布特征
        total_ratings = sum([movie[f'star_{i}'] for i in range(1, 6)])
        if total_ratings > 0:
            computed['rating_variance'] = self._calculate_rating_variance(movie)
        else:
            computed['rating_variance'] = 0.0
        
        # 内容特征
        computed['genre_count'] = len(movie['genres'])
        computed['actor_count'] = len(movie['actors'])
        computed['director_count'] = len(movie['directors'])
        computed['country_count'] = len(movie['countries'])
        
        return computed
    
    def _download_poster(self, poster_url, douban_id):
        """下载电影封面图片"""
        if not poster_url or not douban_id:
            return None
            
        try:
            # 清理URL，确保是有效的图片链接
            if not poster_url.startswith('http'):
                if poster_url.startswith('//'):
                    poster_url = 'https:' + poster_url
                else:
                    return None
            
            # 获取文件扩展名
            parsed_url = urllib.parse.urlparse(poster_url)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext or file_ext.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
                file_ext = '.jpg'  # 默认扩展名
            
            # 生成本地文件名
            filename = f"{douban_id}{file_ext}"
            local_path = os.path.join(self.poster_dir, filename)
            
            # 如果文件已存在，直接返回路径
            if os.path.exists(local_path):
                return os.path.abspath(local_path)
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://movie.douban.com/'
            }
            
            response = requests.get(poster_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 保存图片
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"成功下载封面图片: {filename}")
            return os.path.abspath(local_path)
            
        except Exception as e:
            self.logger.warning(f"下载封面图片失败 (ID: {douban_id}): {e}")
            return None
    
    def _calculate_rating_variance(self, movie):
        """计算评分方差（衡量评分分歧度）"""
        ratings = []
        weights = [movie[f'star_{i}'] for i in range(5, 0, -1)]  # 5星到1星
        
        for i, weight in enumerate(weights):
            ratings.extend([5-i] * int(weight))
        
        if len(ratings) < 2:
            return 0.0
        
        return np.var(ratings)
    

    
    def save_processed_data(self, cleaned_data, output_dir="data"):
        """保存处理后的数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存清洗后的原始数据
        json_file = f"{output_dir}/cleaned_movies_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        # 保存为DataFrame格式
        df = pd.DataFrame(cleaned_data)
        
        # 保存CSV文件
        csv_file = f"{output_dir}/cleaned_movies_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        # 保存数据摘要信息
        data_summary = self._create_data_summary(cleaned_data)
        
        info_file = f"{output_dir}/data_info_{timestamp}.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump({
                'sample_count': len(cleaned_data),
                'timestamp': timestamp,
                'data_summary': data_summary
            }, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"处理后的数据已保存:")
        self.logger.info(f"- JSON: {json_file}")
        self.logger.info(f"- CSV: {csv_file}")
        self.logger.info(f"- 数据信息: {info_file}")
        
        return {
            'json': json_file,
            'csv': csv_file,
            'info': info_file
        }
    
    def save_raw_data(self, raw_data, file_path):
        """保存原始数据 - 用于进度保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            return file_path
        except Exception as e:
            self.logger.error(f"保存原始数据失败: {e}")
            return None
    
    def _create_data_summary(self, data):
        """创建数据摘要"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        return {
            'total_movies': len(data),
            'avg_rating': float(df['rating'].mean()),
            'rating_range': [float(df['rating'].min()), float(df['rating'].max())],
            'year_range': [int(df['year'].min()), int(df['year'].max())] if 'year' in df else None,
            'top_genres': df['genres'].explode().value_counts().head(10).to_dict() if 'genres' in df else {},
            'avg_runtime': float(df['runtime_minutes'].mean()) if 'runtime_minutes' in df else None
        }
