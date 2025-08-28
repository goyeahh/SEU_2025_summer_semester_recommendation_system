#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
烂番茄数据处理模块
负责清洗、转换和保存烂番茄电影数据
"""

import os
import json
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from urllib.parse import urlparse
from .config import RTConfig
from .network import RTNetwork


class RTDataProcessor:
    """烂番茄数据处理器"""
    
    def __init__(self, config=None):
        """
        初始化数据处理器
        
        Args:
            config: 配置对象，默认使用RTConfig
        """
        self.config = config or RTConfig()
        self.network = RTNetwork(config)
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.config.POSTER_DIR, exist_ok=True)
    
    def process_movies(self, movies_data):
        """
        处理电影数据
        
        Args:
            movies_data: 原始电影数据列表
            
        Returns:
            dict: 包含处理后数据和文件路径的字典
        """
        if not movies_data:
            self.logger.warning("没有电影数据需要处理")
            return {'cleaned_data': [], 'file_paths': {}}
        
        # 清洗数据
        cleaned_movies = self._clean_data(movies_data)
        
        if not cleaned_movies:
            self.logger.warning("数据清洗后没有有效数据")
            return {'cleaned_data': [], 'file_paths': {}}
        
        self.logger.info(f"数据清洗完成，有效数据: {len(cleaned_movies)} 条")
        
        # 根据配置决定是否下载海报
        if self.config.DOWNLOAD_POSTERS:
            self._download_posters(cleaned_movies)
        else:
            self.logger.info("已配置跳过海报下载以提升处理速度")
        
        # 保存数据
        file_paths = self._save_data(cleaned_movies)
        
        return {
            'cleaned_data': cleaned_movies,
            'file_paths': file_paths
        }
    
    def _clean_data(self, movies_data):
        """
        清洗电影数据
        
        Args:
            movies_data: 原始电影数据列表
            
        Returns:
            list: 清洗后的电影数据
        """
        cleaned_movies = []
        
        for movie in movies_data:
            if not movie:
                continue
            
            # 验证必需字段
            if not self._validate_movie_data(movie):
                continue
            
            # 清洗和标准化数据
            cleaned_movie = self._standardize_movie_data(movie)
            
            if cleaned_movie:
                cleaned_movies.append(cleaned_movie)
        
        return cleaned_movies
    
    def _validate_movie_data(self, movie):
        """
        验证电影数据的有效性
        
        Args:
            movie: 电影数据字典
            
        Returns:
            bool: 数据是否有效
        """
        # 检查必需字段
        required_fields = ['rt_id', 'title']
        
        for field in required_fields:
            if not movie.get(field):
                self.logger.debug(f"电影数据缺少必需字段 {field}: {movie}")
                return False
        
        return True
    
    def _standardize_movie_data(self, movie):
        """
        标准化电影数据
        
        Args:
            movie: 原始电影数据
            
        Returns:
            dict: 标准化后的电影数据
        """
        try:
            standardized = {
                'rt_id': str(movie.get('rt_id', '')),
                'title': self._clean_text(movie.get('title')),
                'url': movie.get('url', ''),
                'year': self._parse_int(movie.get('year')),
                'mpaa_rating': self._clean_text(movie.get('mpaa_rating')),
                'runtime_minutes': self._parse_int(movie.get('runtime_minutes')),
                'release_date': self._clean_text(movie.get('release_date')),
                'studio': self._clean_text(movie.get('studio')),
                'directors': self._clean_list(movie.get('directors')),
                'writers': self._clean_list(movie.get('writers')),
                'actors': self._clean_list(movie.get('actors')),
                'genres': self._clean_list(movie.get('genres')),
                'synopsis': self._clean_text(movie.get('synopsis')),
                'critics_consensus': self._clean_text(movie.get('critics_consensus')),
                'poster_url': movie.get('poster_url'),
                'trailer_url': movie.get('trailer_url')
            }
            
            # 处理评分信息
            rating_data = movie.get('rating', {})
            if isinstance(rating_data, dict):
                standardized.update({
                    'tomatometer_score': self._parse_int(rating_data.get('tomatometer_score')),
                    'tomatometer_count': self._parse_int(rating_data.get('tomatometer_count')),
                    'audience_score': self._parse_int(rating_data.get('audience_score')),
                    'audience_count': self._parse_int(rating_data.get('audience_count')),
                    'critics_score_state': self._clean_text(rating_data.get('critics_score_state')),
                    'audience_score_state': self._clean_text(rating_data.get('audience_score_state'))
                })
            
            # 添加派生字段
            standardized.update(self._add_derived_fields(standardized))
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"标准化电影数据失败: {e}")
            return None
    
    def _clean_text(self, text):
        """清洗文本数据"""
        if not text:
            return None
        
        if isinstance(text, str):
            # 移除多余的空白字符
            cleaned = ' '.join(text.split())
            return cleaned if cleaned else None
        
        return str(text)
    
    def _clean_list(self, items):
        """清洗列表数据"""
        if not items:
            return None
        
        if isinstance(items, str):
            # 如果是字符串，尝试按逗号分割
            items = [item.strip() for item in items.split(',')]
        
        if isinstance(items, list):
            # 清洗每个元素
            cleaned_items = []
            for item in items:
                if item and str(item).strip():
                    cleaned_items.append(str(item).strip())
            
            return cleaned_items if cleaned_items else None
        
        return None
    
    def _parse_int(self, value):
        """解析整数"""
        if value is None:
            return None
        
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value):
        """解析浮点数"""
        if value is None:
            return None
        
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return None
    
    def _add_derived_fields(self, movie):
        """添加派生字段"""
        derived_fields = {}
        
        # Tomatometer评分标准化 (0-1)
        if movie.get('tomatometer_score'):
            derived_fields['tomatometer_normalized'] = movie['tomatometer_score'] / 100.0
        
        # 观众评分标准化 (0-1)
        if movie.get('audience_score'):
            derived_fields['audience_normalized'] = movie['audience_score'] / 100.0
        
        # 评分人数对数化
        if movie.get('tomatometer_count'):
            derived_fields['tomatometer_count_log'] = np.log10(movie['tomatometer_count'])
        if movie.get('audience_count'):
            derived_fields['audience_count_log'] = np.log10(movie['audience_count'])
        
        # 时长标准化 (0-1, 假设最长电影4小时)
        if movie.get('runtime_minutes'):
            derived_fields['runtime_normalized'] = min(movie['runtime_minutes'] / 240.0, 1.0)
        
        # 评分状态编码
        critics_state_mapping = {'certified_fresh': 3, 'fresh': 2, 'rotten': 1}
        audience_state_mapping = {'upright': 2, 'spilled': 1}
        
        critics_state = movie.get('critics_score_state')
        if critics_state:
            derived_fields['critics_state_encoded'] = critics_state_mapping.get(critics_state, 0)
        
        audience_state = movie.get('audience_score_state')
        if audience_state:
            derived_fields['audience_state_encoded'] = audience_state_mapping.get(audience_state, 0)
        
        # 统计字段
        derived_fields['genre_count'] = len(movie.get('genres', []) or [])
        derived_fields['actor_count'] = len(movie.get('actors', []) or [])
        derived_fields['director_count'] = len(movie.get('directors', []) or [])
        derived_fields['writer_count'] = len(movie.get('writers', []) or [])
        
        return derived_fields
    
    def _download_posters(self, movies):
        """
        下载电影海报
        
        Args:
            movies: 电影数据列表
        """
        for movie in movies:
            poster_url = movie.get('poster_url')
            if not poster_url:
                continue
            
            # 生成文件名
            rt_id = movie.get('rt_id', 'unknown')
            filename = f"{rt_id}.jpg"
            filepath = os.path.join(self.config.POSTER_DIR, filename)
            
            # 下载图片
            if self.network.download_image(poster_url, filepath):
                # 将绝对路径添加到数据中
                movie['poster_path'] = os.path.abspath(filepath)
                self.logger.info(f"成功下载烂番茄海报: {filename}")
            else:
                movie['poster_path'] = None
    
    def _save_data(self, movies):
        """
        保存处理后的数据
        
        Args:
            movies: 清洗后的电影数据
            
        Returns:
            dict: 文件路径字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_paths = {}
        
        try:
            # 保存JSON格式
            if 'json' in self.config.OUTPUT_FORMATS:
                json_path = os.path.join(self.config.OUTPUT_DIR, f"rt_movies_{timestamp}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(movies, f, ensure_ascii=False, indent=2, default=str)
                file_paths['json'] = json_path
            
            # 保存Excel和CSV格式
            df = pd.DataFrame(movies)
            
            if 'xlsx' in self.config.OUTPUT_FORMATS:
                xlsx_path = os.path.join(self.config.OUTPUT_DIR, f"rt_movies_{timestamp}.xlsx")
                df.to_excel(xlsx_path, index=False)
                file_paths['xlsx'] = xlsx_path
            
            if 'csv' in self.config.OUTPUT_FORMATS:
                csv_path = os.path.join(self.config.OUTPUT_DIR, f"rt_movies_{timestamp}.csv")
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                file_paths['csv'] = csv_path
            
            self.logger.info("处理后的数据已保存:")
            for format_type, path in file_paths.items():
                self.logger.info(f"- {format_type.upper()}: {path}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            return {}
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'network'):
            self.network.close_driver()
