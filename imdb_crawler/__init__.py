#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB爬虫模块
用于从IMDB官网爬取电影数据
"""

try:
    from .crawler import IMDBMovieCrawler
    from .config import IMDBConfig
    __all__ = ['IMDBMovieCrawler', 'IMDBConfig']
except ImportError:
    # 如果相对导入失败，使用绝对导入
    pass
