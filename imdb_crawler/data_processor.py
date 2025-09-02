#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB数据处理模块
负责清洗和格式化电影数据
"""

import pandas as pd
import json
import os
import logging
from datetime import datetime
import re
import requests
import urllib.parse


class IMDBDataProcessor:
    """IMDB数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 创建IMDB海报存储目录
        self.poster_dir = "data/imdb_posters"
        if not os.path.exists(self.poster_dir):
            os.makedirs(self.poster_dir)
    
    def clean_movie_data(self, raw_data):
        """
        清洗电影数据
        
        Args:
            raw_data: 原始电影数据列表
            
        Returns:
            list: 清洗后的电影数据列表
        """
        cleaned_data = []
        
        for movie in raw_data:
            if not movie:
                continue
                
            try:
                cleaned_movie = self._clean_single_movie(movie)
                if cleaned_movie:
                    cleaned_data.append(cleaned_movie)
            except Exception as e:
                self.logger.warning(f"清洗电影数据失败: {e}")
                continue
        
        self.logger.info(f"数据清洗完成，有效电影数据: {len(cleaned_data)} 部")
        return cleaned_data
    
    def _clean_single_movie(self, movie):
        """清洗单个电影数据"""
        cleaned = {
            'platform': movie.get('platform', 'IMDB'),
            'imdb_id': self._clean_string(movie.get('imdb_id', '')),
            'url': self._clean_string(movie.get('url', '')),
            'title': self._clean_string(movie.get('title', '')),
            'original_title': self._clean_string(movie.get('original_title', '')),
            'year': self._clean_year(movie.get('year')),
            'rating': self._clean_rating(movie.get('rating')),
            'rating_count': self._clean_number(movie.get('rating_count')),
            'genres': self._clean_list(movie.get('genres', [])),
            'duration': self._clean_number(movie.get('duration')),
            'directors': self._clean_list(movie.get('directors', [])),
            'actors': self._clean_list(movie.get('actors', [])),
            'plot': self._clean_text(movie.get('plot', '')),
            'poster_url': self._clean_string(movie.get('poster_url', '')),
            'poster_path': self._download_poster(movie.get('poster_url'), self._clean_string(movie.get('imdb_id', ''))),  # 修复引用问题
            'countries': self._clean_list(movie.get('countries', [])),
            'languages': self._clean_list(movie.get('languages', [])),
            'release_date': self._clean_string(movie.get('release_date', '')),
            'budget': self._clean_string(movie.get('budget', '')),
            'box_office': self._clean_string(movie.get('box_office', '')),
            'awards': self._clean_list(movie.get('awards', [])),
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 验证必要字段 - 放宽验证条件
        if not cleaned['title'] and not cleaned['imdb_id']:
            self.logger.warning(f"电影缺少基本信息: title='{cleaned['title']}', imdb_id='{cleaned['imdb_id']}'")
            return None
        
        # 如果有基本信息，就保留
        if cleaned['title'] or cleaned['imdb_id']:
            return cleaned
            
        return None
    
    def _clean_string(self, value):
        """清洗字符串"""
        if not value:
            return ''
        return str(value).strip()
    
    def _clean_text(self, value):
        """清洗文本内容"""
        if not value:
            return ''
        
        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', str(value))
        return text.strip()
    
    def _clean_year(self, value):
        """清洗年份"""
        if not value:
            return None
        
        try:
            year = int(value)
            if 1880 <= year <= datetime.now().year + 2:
                return year
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_rating(self, value):
        """清洗评分"""
        if not value:
            return None
        
        try:
            rating = float(value)
            if 0 <= rating <= 10:
                return round(rating, 1)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_number(self, value):
        """清洗数字"""
        if not value:
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _clean_list(self, value):
        """清洗列表"""
        if not value:
            return []
        
        if isinstance(value, list):
            return [self._clean_string(item) for item in value if item]
        elif isinstance(value, str):
            # 如果是字符串，尝试按逗号分割
            return [self._clean_string(item) for item in value.split(',') if item.strip()]
        
        return []
    
    def _download_poster(self, poster_url, imdb_id):
        """下载电影封面图片"""
        if not poster_url or not imdb_id:
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
            
            # 生成本地文件名 (使用IMDB ID)
            filename = f"{imdb_id}{file_ext}"
            local_path = os.path.join(self.poster_dir, filename)
            
            # 如果文件已存在，直接返回路径
            if os.path.exists(local_path):
                return os.path.abspath(local_path)
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.imdb.com/'
            }
            
            response = requests.get(poster_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 保存图片
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"成功下载IMDB封面图片: {filename}")
            return os.path.abspath(local_path)
            
        except Exception as e:
            self.logger.warning(f"下载IMDB封面图片失败 (ID: {imdb_id}): {e}")
            return None
    
    def save_processed_data(self, data, output_dir):
        """
        保存处理后的数据
        
        Args:
            data: 处理后的数据列表
            output_dir: 输出目录
            
        Returns:
            dict: 保存的文件路径信息
        """
        if not data:
            self.logger.warning("没有数据需要保存")
            return {}
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_files = {}
        
        try:
            # 保存为JSON格式
            json_filename = f"imdb_movies_{timestamp}.json"
            json_path = os.path.join(output_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            saved_files['json'] = json_path
            self.logger.info(f"JSON数据已保存: {json_path}")
            
            # 保存为CSV格式
            csv_filename = f"imdb_movies_{timestamp}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            # 转换为DataFrame并保存
            df = pd.DataFrame(data)
            
            # 处理列表类型的列
            list_columns = ['genres', 'directors', 'actors', 'countries', 'languages', 'awards']
            for col in list_columns:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
            
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            saved_files['csv'] = csv_path
            self.logger.info(f"CSV数据已保存: {csv_path}")
            
            # 保存统计信息
            stats_filename = f"imdb_stats_{timestamp}.json"
            stats_path = os.path.join(output_dir, stats_filename)
            
            stats = self._generate_statistics(data)
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            saved_files['stats'] = stats_path
            self.logger.info(f"统计信息已保存: {stats_path}")
            
        except Exception as e:
            self.logger.error(f"保存数据时发生错误: {e}")
            
        return saved_files
    
    def _generate_statistics(self, data):
        """生成数据统计信息"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        stats = {
            'total_movies': len(data),
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platform': 'IMDB',
            'data_quality': {
                'movies_with_rating': len(df[df['rating'].notna()]),
                'movies_with_plot': len(df[df['plot'].str.len() > 0]),
                'movies_with_poster_url': len(df[df['poster_url'].str.len() > 0]),
                'movies_with_poster_downloaded': len(df[df['poster_path'].notna()]) if 'poster_path' in df.columns else 0,
                'average_rating': float(df['rating'].mean()) if 'rating' in df.columns else None,
                'year_range': {
                    'min': int(df['year'].min()) if 'year' in df.columns and df['year'].notna().any() else None,
                    'max': int(df['year'].max()) if 'year' in df.columns and df['year'].notna().any() else None
                }
            }
        }
        
        # 类型统计
        if 'genres' in df.columns:
            all_genres = []
            for genres in df['genres']:
                if isinstance(genres, list):
                    all_genres.extend(genres)
            
            genre_counts = pd.Series(all_genres).value_counts().head(10).to_dict()
            stats['top_genres'] = genre_counts
        
        # 年份分布
        if 'year' in df.columns:
            year_counts = df['year'].value_counts().head(10).to_dict()
            stats['year_distribution'] = {str(k): int(v) for k, v in year_counts.items()}
        
        return stats
    
    def merge_with_douban_data(self, imdb_data, douban_data):
        """
        将IMDB数据与豆瓣数据合并（基于电影标题和年份）
        
        Args:
            imdb_data: IMDB电影数据列表
            douban_data: 豆瓣电影数据列表
            
        Returns:
            list: 合并后的数据列表
        """
        merged_data = []
        
        # 创建豆瓣数据的查找字典
        douban_dict = {}
        for movie in douban_data:
            key = f"{movie.get('title', '').lower()}_{movie.get('year', '')}"
            douban_dict[key] = movie
        
        for imdb_movie in imdb_data:
            # 尝试匹配豆瓣数据
            key = f"{imdb_movie.get('title', '').lower()}_{imdb_movie.get('year', '')}"
            douban_movie = douban_dict.get(key)
            
            merged_movie = imdb_movie.copy()
            if douban_movie:
                # 添加豆瓣数据
                merged_movie.update({
                    'douban_id': douban_movie.get('movie_id'),
                    'douban_rating': douban_movie.get('rating'),
                    'douban_rating_count': douban_movie.get('rating_count'),
                    'douban_url': douban_movie.get('url')
                })
            
            merged_data.append(merged_movie)
        
        self.logger.info(f"合并完成，共 {len(merged_data)} 部电影")
        return merged_data
    
    def save_raw_data(self, raw_data, file_path):
        """保存原始数据 - 用于进度保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            return file_path
        except Exception as e:
            self.logger.error(f"保存IMDB原始数据失败: {e}")
            return None
