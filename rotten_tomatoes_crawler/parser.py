#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
烂番茄网页解析模块
负责解析烂番茄网页内容，提取电影信息
"""

import re
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .config import RTConfig


class RTParser:
    """烂番茄网页解析器"""
    
    def __init__(self, config=None):
        """
        初始化解析器
        
        Args:
            config: 配置对象，默认使用RTConfig
        """
        self.config = config or RTConfig()
        self.logger = logging.getLogger(__name__)
    
    def parse_movie_list(self, html, category='most_popular'):
        """
        解析电影列表页面
        
        Args:
            html: HTML内容
            category: 分类名称
            
        Returns:
            list: 电影URL列表
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            movie_urls = []
            
            # 烂番茄的电影链接模式
            link_patterns = [
                # 标准电影页面链接
                'a[href*="/m/"]',
                # 瓷砖链接
                'tile-link[href*="/m/"]',
                # 数据属性链接
                '[data-qa="discovery-media-list"] a[href*="/m/"]'
            ]
            
            for pattern in link_patterns:
                links = soup.select(pattern)
                for link in links:
                    href = link.get('href')
                    if href and '/m/' in href:
                        # 构建完整URL
                        if href.startswith('/'):
                            full_url = urljoin(self.config.BASE_URL, href)
                        else:
                            full_url = href
                        
                        # 清理URL参数
                        full_url = full_url.split('?')[0].split('#')[0]
                        
                        # 验证是否为有效的电影页面URL
                        if self._is_valid_movie_url(full_url) and full_url not in movie_urls:
                            movie_urls.append(full_url)
            
            # 如果没有找到标准链接，尝试从脚本标签中提取
            if not movie_urls:
                movie_urls = self._extract_urls_from_scripts(soup)
            
            # 去重
            unique_urls = list(dict.fromkeys(movie_urls))
            self.logger.info(f"从烂番茄列表页面解析到 {len(unique_urls)} 个电影链接")
            
            return unique_urls
            
        except Exception as e:
            self.logger.error(f"解析烂番茄电影列表失败: {e}")
            return []
    
    def _is_valid_movie_url(self, url):
        """验证是否为有效的电影URL"""
        if not url:
            return False
        
        # 排除不需要的URL
        exclude_patterns = [
            '/celebrity/', '/tv/', '/news/', '/critics/', '/browse/',
            '/top/', '/franchise/', '/oscar', '/awards'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url:
                return False
        
        # 必须包含电影路径
        return '/m/' in url and 'rottentomatoes.com' in url
    
    def _extract_urls_from_scripts(self, soup):
        """从脚本标签中提取电影URL"""
        movie_urls = []
        
        try:
            # 查找包含JSON数据的脚本标签
            script_tags = soup.find_all('script', string=re.compile(r'movies|media'))
            
            for script in script_tags:
                script_content = script.string
                if script_content:
                    # 使用正则表达式提取URL
                    url_matches = re.findall(r'(?:href|url)["\']\s*:\s*["\']([^"\']*\/m\/[^"\']*)', script_content)
                    for match in url_matches:
                        if self._is_valid_movie_url(match):
                            full_url = urljoin(self.config.BASE_URL, match)
                            movie_urls.append(full_url)
            
        except Exception as e:
            self.logger.warning(f"从脚本中提取URL失败: {e}")
        
        return movie_urls
    
    def parse_movie_detail(self, html, url):
        """
        解析电影详情页面
        
        Args:
            html: HTML内容
            url: 电影URL
            
        Returns:
            dict: 电影详细信息
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 基本信息
            movie_data = {
                'rt_id': self._extract_rt_id(url),
                'url': url,
                'title': self._parse_title(soup),
                'year': self._parse_year(soup),
                'rating': self._parse_ratings(soup),
                'critics_consensus': self._parse_critics_consensus(soup),
                'directors': self._parse_directors(soup),
                'writers': self._parse_writers(soup),
                'actors': self._parse_actors(soup),
                'genres': self._parse_genres(soup),
                'mpaa_rating': self._parse_mpaa_rating(soup),
                'runtime_minutes': self._parse_runtime(soup),
                'release_date': self._parse_release_date(soup),
                'studio': self._parse_studio(soup),
                'synopsis': self._parse_synopsis(soup),
                'poster_url': self._parse_poster_url(soup),
                'trailer_url': self._parse_trailer_url(soup)
            }
            
            # 清理数据
            movie_data = self._clean_movie_data(movie_data)
            
            if movie_data.get('title'):
                self.logger.info(f"成功解析烂番茄电影: {movie_data.get('title', 'Unknown')}")
                return movie_data
            else:
                self.logger.warning(f"无法获取电影标题: {url}")
                return None
            
        except Exception as e:
            self.logger.error(f"解析烂番茄电影详情失败 {url}: {e}")
            return None
    
    def _extract_rt_id(self, url):
        """从URL中提取烂番茄ID"""
        match = re.search(r'/m/([^/]+)', url)
        return match.group(1) if match else None
    
    def _parse_title(self, soup):
        """解析电影标题"""
        # 尝试多种选择器
        selectors = [
            'h1[data-qa="score-panel-movie-title"]',
            '[data-qa="score-panel-movie-title"] h1',
            'h1.mop-ratings-wrap__title',
            'h1.title',
            'meta[property="og:title"]',
            'title'
        ]
        
        for selector in selectors:
            if selector == 'meta[property="og:title"]':
                element = soup.select_one(selector)
                if element and element.get('content'):
                    title = element.get('content')
                    # 移除 "- Rotten Tomatoes" 后缀
                    title = re.sub(r'\s*-\s*Rotten Tomatoes.*$', '', title)
                    if title.strip():
                        return title.strip()
            elif selector == 'title':
                element = soup.select_one(selector)
                if element and element.get_text():
                    title = element.get_text()
                    # 移除 "- Rotten Tomatoes" 后缀
                    title = re.sub(r'\s*-\s*Rotten Tomatoes.*$', '', title)
                    if title.strip():
                        return title.strip()
            else:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    return element.get_text(strip=True)
        
        return None
    
    def _parse_year(self, soup):
        """解析上映年份"""
        # 查找年份信息
        year_selectors = [
            '[data-qa="score-panel-movie-title"] + div',
            '.mop-ratings-wrap__text--small',
            'span.year',
            '[data-qa="movie-info-year"]'
        ]
        
        for selector in year_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r'\b(19|20)\d{2}\b', text)
                if match:
                    return int(match.group())
        
        return None
    
    def _parse_ratings(self, soup):
        """解析评分信息"""
        ratings = {
            'tomatometer_score': None,
            'tomatometer_count': None,
            'audience_score': None,
            'audience_count': None,
            'critics_score_state': None,  # fresh, rotten, certified_fresh
            'audience_score_state': None  # spilled, upright
        }
        
        try:
            # 解析Tomatometer评分
            tomatometer_selectors = [
                '[data-qa="tomatometer"] score-board-deprecated score',
                'score-board score[percentage]',
                '.mop-ratings-wrap__percentage'
            ]
            
            for selector in tomatometer_selectors:
                element = soup.select_one(selector)
                if element:
                    # 尝试从属性获取
                    score = element.get('percentage') or element.get('data-percentage')
                    if score:
                        ratings['tomatometer_score'] = int(score.replace('%', ''))
                        break
                    
                    # 尝试从文本获取
                    text = element.get_text(strip=True)
                    match = re.search(r'(\d+)%', text)
                    if match:
                        ratings['tomatometer_score'] = int(match.group(1))
                        break
            
            # 解析观众评分
            audience_selectors = [
                '[data-qa="audience-score"] score-board-deprecated score',
                'score-board[audiencescore] score',
                '.audience-score .mop-ratings-wrap__percentage'
            ]
            
            for selector in audience_selectors:
                element = soup.select_one(selector)
                if element:
                    score = element.get('percentage') or element.get('data-percentage')
                    if score:
                        ratings['audience_score'] = int(score.replace('%', ''))
                        break
                    
                    text = element.get_text(strip=True)
                    match = re.search(r'(\d+)%', text)
                    if match:
                        ratings['audience_score'] = int(match.group(1))
                        break
            
            # 解析评分状态
            state_element = soup.select_one('[data-qa="tomatometer"] score-board-deprecated')
            if state_element:
                state_class = ' '.join(state_element.get('class', []))
                if 'certified' in state_class.lower():
                    ratings['critics_score_state'] = 'certified_fresh'
                elif 'fresh' in state_class.lower():
                    ratings['critics_score_state'] = 'fresh'
                elif 'rotten' in state_class.lower():
                    ratings['critics_score_state'] = 'rotten'
            
        except Exception as e:
            self.logger.warning(f"解析评分失败: {e}")
        
        return ratings
    
    def _parse_critics_consensus(self, soup):
        """解析影评人共识"""
        consensus_selectors = [
            '[data-qa="critics-consensus"] p',
            '.mop-ratings-wrap__text--concensus',
            '.critics-consensus__text'
        ]
        
        for selector in consensus_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # 确保不是空的或太短的文本
                    return text
        
        return None
    
    def _parse_directors(self, soup):
        """解析导演信息"""
        directors = []
        
        # 查找导演信息
        director_selectors = [
            '[data-qa="movie-info-director"] a',
            '.movie-info-director a',
            'a[href*="/celebrity/"]'
        ]
        
        for selector in director_selectors:
            elements = soup.select(selector)
            for element in elements:
                # 验证是否为导演链接
                href = element.get('href', '')
                if '/celebrity/' in href:
                    name = element.get_text(strip=True)
                    if name and name not in directors:
                        directors.append(name)
        
        return directors if directors else None
    
    def _parse_writers(self, soup):
        """解析编剧信息"""
        writers = []
        
        # 查找编剧信息
        writer_selectors = [
            '[data-qa="movie-info-writer"] a',
            '.movie-info-writer a'
        ]
        
        for selector in writer_selectors:
            elements = soup.select(selector)
            for element in elements:
                name = element.get_text(strip=True)
                if name and name not in writers:
                    writers.append(name)
        
        return writers if writers else None
    
    def _parse_actors(self, soup):
        """解析主演信息"""
        actors = []
        
        # 查找演员信息
        actor_selectors = [
            '[data-qa="cast-crew"] .cast-and-crew-item a',
            '.cast-crew-list a[href*="/celebrity/"]',
            '.movie-info-cast a'
        ]
        
        for selector in actor_selectors:
            elements = soup.select(selector)
            for element in elements[:10]:  # 限制前10个主要演员
                name = element.get_text(strip=True)
                if name and name not in actors:
                    actors.append(name)
        
        return actors if actors else None
    
    def _parse_genres(self, soup):
        """解析电影类型"""
        genres = []
        
        # 查找类型信息
        genre_selectors = [
            '[data-qa="movie-info-genre"]',
            '.movie-info-genre',
            'span[data-qa="genre"]'
        ]
        
        for selector in genre_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # 分割多个类型
                if text:
                    genre_list = [g.strip() for g in re.split(r'[,&]', text)]
                    genres.extend([g for g in genre_list if g and g not in genres])
        
        return genres if genres else None
    
    def _parse_mpaa_rating(self, soup):
        """解析MPAA评级"""
        # 查找MPAA评级
        rating_selectors = [
            '[data-qa="movie-info-rating"]',
            '.movie-info-rating',
            'span.mpaa-rating'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating = element.get_text(strip=True)
                # 验证是否为有效的MPAA评级
                valid_ratings = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'NR', 'Unrated']
                for valid_rating in valid_ratings:
                    if valid_rating in rating:
                        return valid_rating
        
        return None
    
    def _parse_runtime(self, soup):
        """解析电影时长"""
        # 查找时长信息
        runtime_selectors = [
            '[data-qa="movie-info-runtime"]',
            '.movie-info-runtime',
            'time'
        ]
        
        for selector in runtime_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # 匹配时长格式：如 "1h 23m", "123 minutes", "123m"
                patterns = [
                    r'(\d+)h\s*(\d+)m',  # 1h 23m
                    r'(\d+)\s*hour[s]?\s*(\d+)\s*minute[s]?',  # 1 hour 23 minutes
                    r'(\d+)\s*minute[s]?',  # 123 minutes
                    r'(\d+)m'  # 123m
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        if len(match.groups()) == 2:
                            # 包含小时和分钟
                            hours = int(match.group(1))
                            minutes = int(match.group(2))
                            return hours * 60 + minutes
                        else:
                            # 只有分钟
                            return int(match.group(1))
        
        return None
    
    def _parse_release_date(self, soup):
        """解析上映日期"""
        # 查找上映日期
        date_selectors = [
            '[data-qa="movie-info-release-date"]',
            '.movie-info-release-date',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # 尝试从datetime属性获取
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr
                
                # 从文本获取
                text = element.get_text(strip=True)
                if text:
                    return text
        
        return None
    
    def _parse_studio(self, soup):
        """解析制片公司"""
        # 查找制片公司信息
        studio_selectors = [
            '[data-qa="movie-info-studio"]',
            '.movie-info-studio',
            'span.studio'
        ]
        
        for selector in studio_selectors:
            element = soup.select_one(selector)
            if element:
                studio = element.get_text(strip=True)
                if studio:
                    return studio
        
        return None
    
    def _parse_synopsis(self, soup):
        """解析电影简介"""
        # 查找简介信息
        synopsis_selectors = [
            '[data-qa="movie-info-synopsis"]',
            '.movie-synopsis',
            '#movieSynopsis',
            'meta[name="description"]'
        ]
        
        for selector in synopsis_selectors:
            if selector == 'meta[name="description"]':
                element = soup.select_one(selector)
                if element and element.get('content'):
                    synopsis = element.get('content')
                    if len(synopsis) > 20:  # 确保不是太短的描述
                        return synopsis
            else:
                element = soup.select_one(selector)
                if element:
                    synopsis = element.get_text(strip=True)
                    if synopsis and len(synopsis) > 20:
                        return synopsis
        
        return None
    
    def _parse_poster_url(self, soup):
        """解析海报图片URL"""
        # 查找海报图片
        poster_selectors = [
            'img[data-qa="movie-poster"]',
            '.movie-poster img',
            'img.posterImage',
            'meta[property="og:image"]'
        ]
        
        for selector in poster_selectors:
            if selector == 'meta[property="og:image"]':
                element = soup.select_one(selector)
                if element and element.get('content'):
                    src = element.get('content')
                    if src and ('rottentomatoes' in src or 'flixster' in src):
                        return src
            else:
                element = soup.select_one(selector)
                if element:
                    src = element.get('src') or element.get('data-src')
                    if src:
                        # 如果是相对URL，转换为绝对URL
                        if src.startswith('/'):
                            src = urljoin(self.config.BASE_URL, src)
                        return src
        
        return None
    
    def _parse_trailer_url(self, soup):
        """解析预告片URL"""
        # 查找预告片链接
        trailer_selectors = [
            'a[href*="/trailers/"]',
            '[data-qa="watch-trailer"] a',
            '.trailer-link'
        ]
        
        for selector in trailer_selectors:
            element = soup.select_one(selector)
            if element:
                href = element.get('href')
                if href:
                    if href.startswith('/'):
                        return urljoin(self.config.BASE_URL, href)
                    return href
        
        return None
    
    def _clean_movie_data(self, movie_data):
        """清理电影数据"""
        # 移除空值
        cleaned_data = {}
        for key, value in movie_data.items():
            if value is not None and value != [] and value != '' and value != {}:
                cleaned_data[key] = value
        
        return cleaned_data
