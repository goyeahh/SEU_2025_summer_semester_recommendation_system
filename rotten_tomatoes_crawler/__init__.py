#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
烂番茄电影爬虫包
提供从烂番茄网站爬取电影数据的功能
"""

from .crawler import RTCrawler
from .config import RTConfig
from .data_processor import RTDataProcessor
from .parser import RTParser
from .network import RTNetwork

__version__ = "1.0.0"
__author__ = "推荐系统团队"

__all__ = [
    'RTCrawler',
    'RTConfig', 
    'RTDataProcessor',
    'RTParser',
    'RTNetwork'
]
