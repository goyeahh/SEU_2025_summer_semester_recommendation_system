#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB网页解析模块
负责解析IMDB网页内容，提取电影信息
"""

import re
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .config import IMDBConfig


class IMDBParser:
    """IMDB网页解析器"""
    
    def __init__(self, config=None):
        """
        初始化解析器
        
        Args:
            config: 配置对象，默认使用IMDBConfig
        """
        self.config = config or IMDBConfig()
        self.logger = logging.getLogger(__name__)
    
    def parse_movie_list(self, html, category='popular'):
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
            
            if category == 'top250':
                # Top 250页面的解析
                movie_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
                for link in movie_links:
                    href = link.get('href')
                    if href and '/title/' in href:
                        full_url = urljoin(self.config.BASE_URL, href.split('?')[0])
                        if full_url not in movie_urls:
                            movie_urls.append(full_url)
                            
            elif category in ['popular', 'now_playing']:
                # 流行和正在上映页面的解析
                movie_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
                for link in movie_links:
                    href = link.get('href')
                    if href and '/title/' in href:
                        full_url = urljoin(self.config.BASE_URL, href.split('?')[0])
                        if full_url not in movie_urls:
                            movie_urls.append(full_url)
            
            elif 'search/title' in self.config.CATEGORY_URLS.get(category, ''):
                # 搜索结果页面的解析
                movie_containers = soup.find_all('h3', class_='ipc-title')
                for container in movie_containers:
                    link = container.find('a', href=re.compile(r'/title/tt\d+/'))
                    if link:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.config.BASE_URL, href.split('?')[0])
                            if full_url not in movie_urls:
                                movie_urls.append(full_url)
            
            # 去重并限制数量
            unique_urls = list(dict.fromkeys(movie_urls))
            self.logger.info(f"从IMDB列表页面解析到 {len(unique_urls)} 个电影链接")
            
            return unique_urls
            
        except Exception as e:
            self.logger.error(f"解析IMDB电影列表失败: {e}")
            return []
    
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
            
            # 提取IMDB ID
            imdb_id = self._extract_imdb_id(url)
            
            # 基本信息
            movie_data = {
                'imdb_id': imdb_id,
                'url': url,
                'title': self._parse_title(soup),
                'original_title': self._parse_original_title(soup),
                'year': self._parse_year(soup),
                'rating': self._parse_rating(soup),
                'rating_count': self._parse_rating_count(soup),
                'metascore': self._parse_metascore(soup),
                'directors': self._parse_directors(soup),
                'writers': self._parse_writers(soup),
                'actors': self._parse_actors(soup),
                'genres': self._parse_genres(soup),
                'countries': self._parse_countries(soup),
                'languages': self._parse_languages(soup),
                'release_date': self._parse_release_date(soup),
                'runtime_minutes': self._parse_runtime(soup),
                'budget': self._parse_budget(soup),
                'box_office': self._parse_box_office(soup),
                'summary': self._parse_summary(soup),
                'poster_url': self._parse_poster_url(soup),
                'trailer_url': self._parse_trailer_url(soup)
            }
            
            # 添加技术信息
            movie_data.update(self._parse_technical_specs(soup))
            
            # 清理数据
            movie_data = self._clean_movie_data(movie_data)
            
            self.logger.info(f"成功解析IMDB电影: {movie_data.get('title', 'Unknown')}")
            return movie_data
            
        except Exception as e:
            self.logger.error(f"解析IMDB电影详情失败 {url}: {e}")
            return None
    
    def _extract_imdb_id(self, url):
        """从URL中提取IMDB ID"""
        match = re.search(r'/title/(tt\d+)/', url)
        return match.group(1) if match else None
    
    def _parse_title(self, soup):
        """解析电影标题"""
        # 尝试多种选择器
        selectors = [
            'h1[data-testid="hero__pageTitle"] span.hero__primary-text',
            'h1.sc-afe43def-0',
            'h1[data-testid="hero-title-block__title"]',
            'h1.titleBar-title',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return None
    
    def _parse_original_title(self, soup):
        """解析原始标题"""
        # 查找原始标题信息
        original_title_element = soup.find('div', {'data-testid': 'hero-title-block__original-title'})
        if original_title_element:
            text = original_title_element.get_text(strip=True)
            if 'Original title:' in text:
                return text.replace('Original title:', '').strip()
        
        return None
    
    def _parse_year(self, soup):
        """解析上映年份"""
        # 尝试多种方式获取年份
        year_selectors = [
            'a[href*="releaseinfo"]',
            'span.sc-afe43def-4',
            'h1 span'
        ]
        
        for selector in year_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r'\b(19|20)\d{2}\b', text)
                if match:
                    return int(match.group())
        
        return None
    
    def _parse_rating(self, soup):
        """解析IMDB评分"""
        # 查找评分信息
        rating_selectors = [
            'span.sc-bde20123-1',
            'span[data-testid="rating-button__aggregate-rating__score"]',
            'span.AggregateRatingButton__RatingScore-sc-1ll29m0-1'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                try:
                    return float(text)
                except ValueError:
                    continue
        
        return None
    
    def _parse_rating_count(self, soup):
        """解析评分人数"""
        # 查找评分人数
        count_selectors = [
            'div[data-testid="rating-button__aggregate-rating__score"] div:nth-child(3)',
            'span.AggregateRatingButton__TotalRatingAmount-sc-1ll29m0-3'
        ]
        
        for selector in count_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # 提取数字，处理K、M等单位
                match = re.search(r'([\d,.]+)([KM]?)', text.replace(',', ''))
                if match:
                    number = float(match.group(1))
                    unit = match.group(2).upper()
                    if unit == 'K':
                        return int(number * 1000)
                    elif unit == 'M':
                        return int(number * 1000000)
                    else:
                        return int(number)
        
        return None
    
    def _parse_metascore(self, soup):
        """解析Metascore评分"""
        metascore_element = soup.find('span', class_='score-meta')
        if metascore_element:
            try:
                return int(metascore_element.get_text(strip=True))
            except ValueError:
                pass
        return None
    
    def _parse_directors(self, soup):
        """解析导演信息"""
        directors = []
        
        # 查找导演信息
        director_sections = soup.find_all('li', {'data-testid': 'title-pc-principal-credit'})
        for section in director_sections:
            label = section.find('span', class_='ipc-metadata-list-item__label')
            if label and 'Director' in label.get_text():
                links = section.find_all('a', class_='ipc-metadata-list-item__list-content-item')
                directors.extend([link.get_text(strip=True) for link in links])
                break
        
        return directors if directors else None
    
    def _parse_writers(self, soup):
        """解析编剧信息"""
        writers = []
        
        # 查找编剧信息
        writer_sections = soup.find_all('li', {'data-testid': 'title-pc-principal-credit'})
        for section in writer_sections:
            label = section.find('span', class_='ipc-metadata-list-item__label')
            if label and 'Writer' in label.get_text():
                links = section.find_all('a', class_='ipc-metadata-list-item__list-content-item')
                writers.extend([link.get_text(strip=True) for link in links])
                break
        
        return writers if writers else None
    
    def _parse_actors(self, soup):
        """解析主演信息"""
        actors = []
        
        # 查找演员信息
        cast_section = soup.find('section', {'data-testid': 'title-cast'})
        if cast_section:
            actor_links = cast_section.find_all('a', {'data-testid': 'title-cast-item__actor'})
            actors = [link.get_text(strip=True) for link in actor_links[:10]]  # 限制前10个主要演员
        
        return actors if actors else None
    
    def _parse_genres(self, soup):
        """解析电影类型"""
        genres = []
        
        # 查找类型信息
        genre_elements = soup.find_all('a', href=re.compile(r'genres='))
        for element in genre_elements:
            genre = element.get_text(strip=True)
            if genre and genre not in genres:
                genres.append(genre)
        
        return genres if genres else None
    
    def _parse_countries(self, soup):
        """解析制片国家"""
        countries = []
        
        # 查找国家信息
        country_elements = soup.find_all('a', href=re.compile(r'country_of_origin='))
        countries = [elem.get_text(strip=True) for elem in country_elements]
        
        return countries if countries else None
    
    def _parse_languages(self, soup):
        """解析语言信息"""
        languages = []
        
        # 查找语言信息
        language_elements = soup.find_all('a', href=re.compile(r'primary_language='))
        languages = [elem.get_text(strip=True) for elem in language_elements]
        
        return languages if languages else None
    
    def _parse_release_date(self, soup):
        """解析上映日期"""
        # 查找上映日期
        date_elements = soup.find_all('a', href=re.compile(r'releaseinfo'))
        for element in date_elements:
            text = element.get_text(strip=True)
            # 尝试匹配日期格式
            date_match = re.search(r'\b\d{1,2}\s+\w+\s+(19|20)\d{2}\b', text)
            if date_match:
                return date_match.group()
        
        return None
    
    def _parse_runtime(self, soup):
        """解析电影时长"""
        # 查找时长信息
        runtime_selectors = [
            'time',
            'li[data-testid="title-techspec_runtime"]',
            'span:contains("min")'
        ]
        
        for selector in runtime_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                match = re.search(r'(\d+)\s*min', text)
                if match:
                    return int(match.group(1))
        
        return None
    
    def _parse_budget(self, soup):
        """解析制作预算"""
        # 查找预算信息
        budget_elements = soup.find_all('li', {'data-testid': 'title-boxoffice-budget'})
        for element in budget_elements:
            text = element.get_text(strip=True)
            match = re.search(r'\$[\d,]+', text.replace(',', ''))
            if match:
                return match.group().replace('$', '').replace(',', '')
        
        return None
    
    def _parse_box_office(self, soup):
        """解析票房信息"""
        # 查找票房信息
        box_office_elements = soup.find_all('li', {'data-testid': 'title-boxoffice-cumulativeworldwidegross'})
        for element in box_office_elements:
            text = element.get_text(strip=True)
            match = re.search(r'\$[\d,]+', text)
            if match:
                return match.group().replace('$', '').replace(',', '')
        
        return None
    
    def _parse_summary(self, soup):
        """解析电影简介"""
        # 查找简介信息
        summary_selectors = [
            'span[data-testid="plot-x1_text"]',
            'span[data-testid="plot-xl_text"]',
            'span.plot_summary',
            'div.summary_text'
        ]
        
        for selector in summary_selectors:
            element = soup.select_one(selector)
            if element:
                summary = element.get_text(strip=True)
                if summary and len(summary) > 10:  # 确保不是空的或太短的文本
                    return summary
        
        return None
    
    def _parse_poster_url(self, soup):
        """解析海报图片URL"""
        # 查找海报图片
        poster_selectors = [
            'div[data-testid="hero-media__poster"] img',
            'img.ipc-image',
            'img[data-testid="hero-media__poster"]'
        ]
        
        for selector in poster_selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src')
                if src and 'amazon' in src:
                    # 获取更高质量的图片
                    return src.replace('_UX67_CR0,0,67,98_', '_SX300_').replace('_V1_UX67_CR0,0,67,98_AL_', '_V1_SX300_AL_')
        
        return None
    
    def _parse_trailer_url(self, soup):
        """解析预告片URL"""
        # 查找预告片链接
        trailer_links = soup.find_all('a', href=re.compile(r'video/vi\d+'))
        if trailer_links:
            href = trailer_links[0].get('href')
            return urljoin(self.config.BASE_URL, href)
        
        return None
    
    def _parse_technical_specs(self, soup):
        """解析技术规格信息"""
        specs = {
            'aspect_ratio': None,
            'sound_mix': None,
            'color': None
        }
        
        # 查找技术规格
        tech_specs = soup.find_all('li', class_='ipc-metadata-list-item')
        for spec in tech_specs:
            label_elem = spec.find('span', class_='ipc-metadata-list-item__label')
            if label_elem:
                label = label_elem.get_text(strip=True).lower()
                value_elem = spec.find('div', class_='ipc-metadata-list-item__content-container')
                if value_elem:
                    value = value_elem.get_text(strip=True)
                    
                    if 'aspect ratio' in label:
                        specs['aspect_ratio'] = value
                    elif 'sound mix' in label:
                        specs['sound_mix'] = value
                    elif 'color' in label:
                        specs['color'] = value
        
        return specs
    
    def _clean_movie_data(self, movie_data):
        """清理电影数据"""
        # 移除空值
        cleaned_data = {}
        for key, value in movie_data.items():
            if value is not None and value != [] and value != '':
                cleaned_data[key] = value
        
        return cleaned_data
