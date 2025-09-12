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
        """清洗单个电影数据 - 仅保留数据库需要的字段"""
        cleaned = {
            'title': self._clean_string(movie.get('title', '')),
            'genres': self._clean_list(movie.get('genres', [])),
            'year': self._clean_year(movie.get('year')),
            'countries': self._clean_list(movie.get('countries', [])),
            'directors': self._clean_list(movie.get('directors', [])),
            'actors': self._clean_list(movie.get('actors', [])),
            'duration': self._clean_number(movie.get('duration')),
            'plot': self._clean_text(movie.get('plot', '')),
            'rating': self._clean_rating(movie.get('rating')),
            'rating_distribution': movie.get('rating_distribution', {}),
            'poster_url': self._clean_string(movie.get('poster_url', ''))
        }
        
        # 验证必要字段
        if not cleaned['title']:
            self.logger.warning(f"电影缺少标题信息")
            return None
        
        return cleaned
    
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

    def save_processed_data(self, data, output_dir):
        """
        保存处理后的数据 - 仅数据库格式
        
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
        
        saved_files = {}
        
        try:
            # 只保存数据库格式
            db_path = self.save_database_format(data, output_dir)
            if db_path:
                saved_files['database_csv'] = db_path
                self.logger.info(f"数据库格式CSV已保存: {db_path}")
            else:
                self.logger.error("保存数据库格式失败")
            
        except Exception as e:
            self.logger.error(f"保存数据时发生错误: {e}")
            
        return saved_files

    def save_database_format(self, data, output_dir):
        """按数据库格式保存数据"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_file = os.path.join(output_dir, f"imdb_database_{timestamp}.csv")
            
            # 创建数据库格式的DataFrame
            db_data = []
            for index, movie in enumerate(data, start=1):  # 从1开始的自定义ID
                db_row = self._convert_to_database_format(movie, custom_id=index)
                if db_row:
                    db_data.append(db_row)
            
            if not db_data:
                self.logger.warning("没有有效的电影数据用于数据库格式保存")
                return None
            
            # 创建DataFrame并保存为CSV
            df = pd.DataFrame(db_data)
            
            # 设置列的顺序
            column_order = [
                'id', 'name', 'genres', 'year', 'countries', 'directors', 
                'actors', 'duration_minutes', 'plot', 
                'rating_10', 'rating_9', 'rating_8', 'rating_7', 'rating_6',
                'rating_5', 'rating_4', 'rating_3', 'rating_2', 'rating_1',
                'processed_rating', 'poster_path'
            ]
            
            # 重新排序列
            df = df.reindex(columns=column_order)
            
            # 保存为CSV
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"数据库格式数据保存成功: {csv_file}")
            return csv_file
            
        except Exception as e:
            self.logger.error(f"保存数据库格式数据失败: {e}")
            return None

    def _convert_to_database_format(self, movie, custom_id):
        """将电影数据转换为数据库格式"""
        try:
            # 提取评分分布
            rating_dist = movie.get('rating_distribution', {})
            
            # 如果没有评分分布数据，创建默认值
            if not rating_dist:
                rating_dist = {str(i): 0.0 for i in range(1, 11)}
            
            # 下载海报并重命名为自定义ID
            poster_path = self._download_poster_with_custom_id(
                movie.get('poster_url'), custom_id
            )
            
            db_row = {
                'id': custom_id,  # 使用自定义的顺序ID
                'name': movie.get('title', ''),
                'genres': ','.join(movie.get('genres', [])),
                'year': movie.get('year', ''),
                'countries': ','.join(movie.get('countries', [])),
                'directors': ','.join(movie.get('directors', [])),
                'actors': ','.join(movie.get('actors', [])[:5]),  # 限制前5个主要演员
                'duration_minutes': movie.get('duration', ''),
                'plot': movie.get('plot', ''),
                'rating_10': rating_dist.get('10', 0.0),
                'rating_9': rating_dist.get('9', 0.0),
                'rating_8': rating_dist.get('8', 0.0),
                'rating_7': rating_dist.get('7', 0.0),
                'rating_6': rating_dist.get('6', 0.0),
                'rating_5': rating_dist.get('5', 0.0),
                'rating_4': rating_dist.get('4', 0.0),
                'rating_3': rating_dist.get('3', 0.0),
                'rating_2': rating_dist.get('2', 0.0),
                'rating_1': rating_dist.get('1', 0.0),
                'processed_rating': movie.get('rating', 0.0),  # 满分十分的处理后评分
                'poster_path': poster_path if poster_path else ''  # 海报相对路径
            }
            
            return db_row
            
        except Exception as e:
            self.logger.warning(f"转换电影数据为数据库格式失败: {e}")
            return None

    def _download_poster_with_custom_id(self, poster_url, custom_id):
        """使用自定义ID下载海报"""
        if not poster_url:
            return ''
        
        try:
            # 从URL中提取文件扩展名
            ext = '.jpg'  # 默认扩展名
            if '.' in poster_url:
                url_ext = poster_url.split('.')[-1].lower()
                if url_ext in ['jpg', 'jpeg', 'png', 'webp']:
                    ext = f'.{url_ext}'
            
            # 使用自定义ID作为文件名
            filename = f"{custom_id}{ext}"
            local_path = os.path.join(self.poster_dir, filename)
            
            # 如果文件已存在，返回相对路径
            if os.path.exists(local_path):
                relative_path = f"data/imdb_posters/{filename}"
                return relative_path
            
            # 下载海报
            response = requests.get(poster_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            response.raise_for_status()
            
            # 保存到本地
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # 返回相对路径
            relative_path = f"data/imdb_posters/{filename}"
            self.logger.info(f"成功下载IMDB海报: {filename}")
            return relative_path
            
        except Exception as e:
            self.logger.warning(f"下载IMDB海报失败 (ID: {custom_id}): {e}")
            return ''
