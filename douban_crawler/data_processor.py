#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆瓣数据处理模块 - 数据库格式专用
负责豆瓣数据清洗和数据库格式输出
"""

import pandas as pd
import json
import re
import os
import requests
import urllib.parse
from datetime import datetime
import logging

from .config import Config


class DataProcessor:
    """豆瓣数据处理器 - 数据库格式专用"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 创建海报存储目录
        self.poster_dir = "data/douban_posters"
        if not os.path.exists(self.poster_dir):
            os.makedirs(self.poster_dir)
    
    def clean_movie_data(self, raw_data):
        """清洗电影数据 - 只保留数据库格式所需字段"""
        cleaned_data = []
        
        for movie in raw_data:
            if not movie or not self._is_valid_movie(movie):
                continue
            
            cleaned_movie = self._clean_single_movie(movie)
            if cleaned_movie:
                cleaned_data.append(cleaned_movie)
        
        self.logger.info(f"数据清洗完成，有效电影数据: {len(cleaned_data)} 部")
        return cleaned_data
    
    def _is_valid_movie(self, movie):
        """验证电影数据是否有效"""
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
        """清洗单个电影数据 - 只保留数据库格式字段"""
        try:
            cleaned = {
                # 保留豆瓣ID用于内部处理（海报下载等）
                'douban_id': str(movie['douban_id']),
                'title': self._clean_text(movie['title']),
                'year': movie.get('year'),
                'rating': float(movie.get('rating', 0)),
                'directors': self._clean_list(movie.get('directors', [])),
                'actors': self._clean_list(movie.get('actors', [])),
                'genres': self._clean_list(movie.get('genres', [])),
                'countries': self._clean_list(movie.get('countries', [])),
                'runtime_minutes': movie.get('runtime_minutes'),
                'summary': self._clean_summary(movie.get('summary', '')),
                
                # 评分分布
                'star_5': float(movie.get('star_5', 0)),
                'star_4': float(movie.get('star_4', 0)),
                'star_3': float(movie.get('star_3', 0)),
                'star_2': float(movie.get('star_2', 0)),
                'star_1': float(movie.get('star_1', 0)),
            }
            
            # 处理封面图片
            cleaned['poster_path'] = self._download_poster(movie.get('poster_url'), cleaned['douban_id'])
            
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
            
            self.logger.info(f"成功下载豆瓣封面图片: {filename}")
            return os.path.abspath(local_path)
            
        except Exception as e:
            self.logger.warning(f"下载封面图片失败 (ID: {douban_id}): {e}")
            return None
    
    def _rename_poster_with_custom_id(self, movie, custom_id):
        """使用自定义ID重命名海报文件"""
        try:
            old_poster_path = movie.get('poster_path')
            if not old_poster_path or not os.path.exists(old_poster_path):
                return
            
            # 获取文件扩展名
            file_ext = os.path.splitext(old_poster_path)[1] or '.jpg'
            
            # 新文件名使用自定义ID
            new_filename = f"{custom_id}{file_ext}"
            new_poster_path = os.path.join(self.poster_dir, new_filename)
            
            # 如果新文件名与旧文件名不同，则重命名
            if old_poster_path != new_poster_path:
                if os.path.exists(new_poster_path):
                    # 如果目标文件已存在，删除旧文件
                    os.remove(old_poster_path)
                else:
                    # 重命名文件
                    os.rename(old_poster_path, new_poster_path)
                    self.logger.info(f"海报重命名: {os.path.basename(old_poster_path)} → {new_filename}")
                
                # 更新电影数据中的路径
                movie['poster_path'] = new_poster_path
                
        except Exception as e:
            self.logger.warning(f"海报重命名失败 (ID: {custom_id}): {e}")
    
    def save_database_format(self, cleaned_data, output_dir="data"):
        """保存数据库格式的数据 - 豆瓣专用"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 转换为数据库格式并重命名海报
            database_data = []
            for idx, movie in enumerate(cleaned_data):
                custom_id = idx + 1
                # 重命名海报文件
                self._rename_poster_with_custom_id(movie, custom_id)
                # 转换数据格式
                data = self._convert_to_database_format(movie, custom_id)
                if data:
                    database_data.append(data)
            
            # 创建DataFrame
            df = pd.DataFrame(database_data)
            
            # 确保字段顺序
            column_order = [
                'id', 'name', 'genres', 'year', 'countries', 'directors', 
                'actors', 'duration_minutes', 'plot', 
                'star_5', 'star_4', 'star_3', 'star_2', 'star_1',
                'processed_rating', 'poster_path'
            ]
            
            # 重新排序列
            df = df.reindex(columns=column_order)
            
            # 保存文件
            database_file = f"{output_dir}/douban_database_{timestamp}.csv"
            df.to_csv(database_file, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"数据库格式数据保存成功: {database_file}")
            self.logger.info(f"数据库格式CSV已保存: {database_file}")
            
            return database_file
            
        except Exception as e:
            self.logger.error(f"保存数据库格式数据失败: {e}")
            return None
    
    def _convert_to_database_format(self, movie, movie_id):
        """将豆瓣电影数据转换为统一的数据库格式"""
        try:
            # 处理海报路径 - 使用自定义ID生成相对路径
            poster_path = ""
            if movie.get('poster_path'):
                # 从绝对路径中提取文件名，生成相对路径
                abs_path = movie.get('poster_path')
                if os.path.exists(abs_path):
                    filename = os.path.basename(abs_path)
                    poster_path = f"data/douban_posters/{filename}"
                else:
                    # 使用自定义ID作为fallback
                    poster_path = f"data/douban_posters/{movie_id}.jpg"
            
            # 处理时长 - 确保是数字
            duration_minutes = movie.get('runtime_minutes', 0)
            if duration_minutes is None or duration_minutes == "":
                duration_minutes = 0
            
            # 处理评分 - 确保是数字
            processed_rating = movie.get('rating', 0)
            if processed_rating is None or processed_rating == "":
                processed_rating = 0.0
            
            # 处理列表字段 - 转换为字符串
            genres_str = ",".join(movie.get('genres', []))
            countries_str = ",".join(movie.get('countries', []))
            directors_str = ",".join(movie.get('directors', []))
            actors_str = ",".join(movie.get('actors', []))
            
            # 处理剧情简介
            plot = movie.get('summary', '')
            if not plot:
                plot = ''
            
            database_record = {
                'id': movie_id,
                'name': movie.get('title', ''),
                'genres': genres_str,
                'year': movie.get('year', ''),
                'countries': countries_str,
                'directors': directors_str,
                'actors': actors_str,
                'duration_minutes': int(duration_minutes),
                'plot': plot,
                'star_5': float(movie.get('star_5', 0)),
                'star_4': float(movie.get('star_4', 0)),
                'star_3': float(movie.get('star_3', 0)),
                'star_2': float(movie.get('star_2', 0)),
                'star_1': float(movie.get('star_1', 0)),
                'processed_rating': float(processed_rating),
                'poster_path': poster_path
            }
            
            return database_record
            
        except Exception as e:
            self.logger.error(f"转换数据库格式失败: {movie.get('title', 'Unknown')}, 错误: {e}")
            return None
    
    def save_raw_data(self, raw_data, file_path):
        """保存原始数据 - 用于进度保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            return file_path
        except Exception as e:
            self.logger.error(f"保存原始数据失败: {e}")
            return None
