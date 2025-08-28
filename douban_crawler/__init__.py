#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆瓣电影爬虫模块
用于大数据真值推荐系统项目的数据采集
"""

from .crawler import DoubanCrawler  # 修正类名
from .data_processor import DataProcessor
from .config import Config

__version__ = "1.0.0"
__author__ = "Jiang Chen"

__all__ = [
    'DoubanCrawler',
    'DataProcessor', 
    'Config'
]
