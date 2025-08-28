#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB电影爬虫包
提供从IMDB网站爬取电影数据的功能
"""

from .crawler import IMDBCrawler
from .config import IMDBConfig
from .data_processor import IMDBDataProcessor
from .parser import IMDBParser
from .network import IMDBNetwork

__version__ = "1.0.0"
__author__ = "推荐系统团队"

__all__ = [
    'IMDBCrawler',
    'IMDBConfig', 
    'IMDBDataProcessor',
    'IMDBParser',
    'IMDBNetwork'
]
