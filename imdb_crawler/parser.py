#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB页面解析模块
负责解析IMDB网页内容，提取电影信息
"""

import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging


class IMDBPageParser:
    """IMDB页面解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.imdb.com"
    
    def parse_movie_list(self, response, url_type='chart'):
        """
        解析电影列表页面，获取电影详情页链接
        
        Args:
            response: HTTP响应对象
            url_type: URL类型 ('chart', 'search', 'top250')
            
        Returns:
            list: 电影详情页链接列表
        """
        movie_links = []
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if url_type == 'chart' or 'chart' in response.url:
                # 处理榜单页面
                movie_links.extend(self._parse_chart_page(soup))
            
            elif url_type == 'search' or 'search' in response.url:
                # 处理搜索结果页面
                movie_links.extend(self._parse_search_page(soup))
            
            elif 'top' in response.url:
                # 处理Top250等页面
                movie_links.extend(self._parse_top_page(soup))
            
            else:
                # 默认尝试多种解析方式
                movie_links.extend(self._parse_generic_page(soup))
            
            # 去重并转换为完整URL
            unique_links = list(set(movie_links))
            full_links = [urljoin(self.base_url, link) for link in unique_links if link]
            
            self.logger.info(f"从页面解析到 {len(full_links)} 个电影链接")
            return full_links
            
        except Exception as e:
            self.logger.error(f"解析电影列表页面失败: {e}")
            return []
    
    def _parse_chart_page(self, soup):
        """解析榜单页面"""
        links = []
        
        # 尝试多种选择器
        selectors = [
            '.ipc-title-link-wrapper',
            '.titleColumn a',
            '.cli-title a',
            'h3.ipc-title a',
            'a[class*="title"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/title/tt' in href:
                    # 清理链接，只保留到电影ID部分
                    match = re.search(r'/title/(tt\d+)/', href)
                    if match:
                        links.append(f"/title/{match.group(1)}/")
        
        return links
    
    def _parse_search_page(self, soup):
        """解析搜索结果页面"""
        links = []
        
        # 搜索页面的选择器
        selectors = [
            '.ipc-title-link-wrapper',
            '.result_text a',
            'h3.ipc-title a',
            '.lister-item-header a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/title/tt' in href:
                    match = re.search(r'/title/(tt\d+)/', href)
                    if match:
                        links.append(f"/title/{match.group(1)}/")
        
        return links
    
    def _parse_top_page(self, soup):
        """解析Top页面"""
        links = []
        
        # Top页面选择器
        selectors = [
            '.cli-title a',
            '.titleColumn a',
            '.ipc-title-link-wrapper'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/title/tt' in href:
                    match = re.search(r'/title/(tt\d+)/', href)
                    if match:
                        links.append(f"/title/{match.group(1)}/")
        
        return links
    
    def _parse_generic_page(self, soup):
        """通用页面解析"""
        links = []
        
        # 查找所有包含电影ID的链接
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and '/title/tt' in href:
                match = re.search(r'/title/(tt\d+)/', href)
                if match:
                    links.append(f"/title/{match.group(1)}/")
        
        return links
    
    def parse_movie_detail(self, response, movie_url):
        """
        解析电影详情页面
        
        Args:
            response: HTTP响应对象
            movie_url: 电影详情页URL
            
        Returns:
            dict: 电影信息字典
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取电影ID
            movie_id = self._extract_movie_id(movie_url)
            
            # 提取电影信息
            movie_info = {
                'platform': 'IMDB',
                'imdb_id': movie_id,
                'url': movie_url,
                'title': self._extract_title(soup),
                'original_title': self._extract_original_title(soup),
                'year': self._extract_year(soup),
                'rating': self._extract_rating(soup),
                'rating_count': self._extract_rating_count(soup),
                'genres': self._extract_genres(soup),
                'duration': self._extract_duration(soup),
                'directors': self._extract_directors(soup),
                'actors': self._extract_actors(soup),
                'plot': self._extract_plot(soup),
                'poster_url': self._extract_poster(soup),
                'countries': self._extract_countries(soup),
                'languages': self._extract_languages(soup),
                'release_date': self._extract_release_date(soup),
                'budget': self._extract_budget(soup),
                'box_office': self._extract_box_office(soup),
                'awards': self._extract_awards(soup)
            }
            
            # 调试日志
            self.logger.info(f"解析结果: ID={movie_id}, 标题='{movie_info['title']}', 评分={movie_info['rating']}")
            
            return movie_info
            
        except Exception as e:
            self.logger.error(f"解析电影详情失败 {movie_url}: {e}")
            return None
    
    def _extract_movie_id(self, url):
        """提取电影ID"""
        match = re.search(r'/title/(tt\d+)/', url)
        return match.group(1) if match else ''
    
    def _extract_title(self, soup):
        """提取电影标题 - 更新版本"""
        selectors = [
            # 新版IMDB结构
            'h1[data-testid="hero-title-block__title"]',
            'span.hero__primary-text',
            '.sc-afe43def-1.fDTGTb',
            # 旧版结构
            'h1.sc-b73cd867-0',
            'h1[class*="title"]',
            '.title_wrapper h1',
            # 通用匹配
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 1:  # 确保不是空白或单字符
                    return title
        
        # 如果都失败，尝试从页面标题提取
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text()
            # 移除" - IMDb"后缀
            title = title_text.replace(' - IMDb', '').strip()
            if title:
                return title
        
        return ''
    
    def _extract_original_title(self, soup):
        """提取原始标题"""
        # 尝试从页面中提取原始标题
        original_title = soup.select_one('[data-testid="hero-title-block__original-title"]')
        if original_title:
            text = original_title.get_text(strip=True)
            # 移除"Original title: "前缀
            return text.replace('Original title: ', '')
        return ''
    
    def _extract_year(self, soup):
        """提取上映年份"""
        selectors = [
            'a[href*="year"]',
            '.sc-8c396aa2-2 a',
            '[data-testid="hero-title-block__metadata"] a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                year_match = re.search(r'\b(19|20)\d{2}\b', text)
                if year_match:
                    return int(year_match.group())
        
        return None
    
    def _extract_rating(self, soup):
        """提取评分 - 增强版本"""
        selectors = [
            # 新版IMDB结构
            'span[class*="AggregateRatingButton__RatingScore"]',
            '.hero-rating-bar__aggregate-rating__score span',
            '[data-testid="hero-rating-bar__aggregate-rating__score"] span',
            # 其他可能的选择器
            '.sc-7ab21ed2-1',
            '.ratingValue span',
            'span.ipc-rating-star--rating',
            # JSON-LD 数据提取
            'script[type="application/ld+json"]'
        ]
        
        # 首先尝试常规选择器
        for selector in selectors[:-1]:  # 排除script标签
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    # 合理的评分范围检查
                    if 0 <= rating <= 10:
                        return rating
        
        # 尝试从JSON-LD数据提取
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'aggregateRating' in data:
                    rating = data['aggregateRating'].get('ratingValue')
                    if rating:
                        return float(rating)
            except:
                continue
        
        return None
    
    def _extract_rating_count(self, soup):
        """提取评分人数"""
        selectors = [
            '[data-testid="hero-rating-bar__aggregate-rating__score"] + div',
            '.sc-7ab21ed2-3'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # 提取数字，可能包含K、M等单位
                count_match = re.search(r'([\d,]+(?:\.\d+)?)\s*([KMB]?)', text)
                if count_match:
                    number = float(count_match.group(1).replace(',', ''))
                    unit = count_match.group(2)
                    if unit == 'K':
                        number *= 1000
                    elif unit == 'M':
                        number *= 1000000
                    elif unit == 'B':
                        number *= 1000000000
                    return int(number)
        
        return None
    
    def _extract_genres(self, soup):
        """提取电影类型"""
        genres = []
        
        selectors = [
            '[data-testid="genres"] a',
            '.sc-16ede01-3 a',
            '[class*="genre"] a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                genre = element.get_text(strip=True)
                if genre and genre not in genres:
                    genres.append(genre)
        
        return genres
    
    def _extract_duration(self, soup):
        """提取电影时长"""
        selectors = [
            '[data-testid="title-techspec_runtime"]',
            '.sc-16ede01-0 li',
            '.runtime'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 'min' in text or 'hour' in text:
                    # 提取分钟数
                    time_match = re.search(r'(\d+)\s*(?:hour|hr)?s?\s*(\d+)?\s*min', text)
                    if time_match:
                        hours = int(time_match.group(1) or 0)
                        minutes = int(time_match.group(2) or 0)
                        if 'hour' in text or 'hr' in text:
                            return hours * 60 + minutes
                        else:
                            return hours
                    
                    # 只有分钟的情况
                    min_match = re.search(r'(\d+)\s*min', text)
                    if min_match:
                        return int(min_match.group(1))
        
        return None
    
    def _extract_directors(self, soup):
        """提取导演"""
        directors = []
        
        selectors = [
            '[data-testid="title-pc-principal-credit"]:has-text("Director") a',
            '.credit_summary_item:has-text("Director") a'
        ]
        
        # 查找导演部分
        director_sections = soup.find_all(['div', 'li'], string=re.compile(r'Director|Directed'))
        for section in director_sections:
            parent = section.find_parent()
            if parent:
                links = parent.find_all('a')
                for link in links:
                    name = link.get_text(strip=True)
                    if name and name not in directors:
                        directors.append(name)
        
        return directors
    
    def _extract_actors(self, soup):
        """提取主要演员"""
        actors = []
        
        # 查找演员列表
        cast_sections = soup.select('[data-testid="title-cast"] a, .cast_list a')
        for link in cast_sections[:10]:  # 限制前10个主要演员
            name = link.get_text(strip=True)
            if name and name not in actors and not any(x in name.lower() for x in ['more', 'see', 'full']):
                actors.append(name)
        
        return actors
    
    def _extract_plot(self, soup):
        """提取剧情简介"""
        selectors = [
            '[data-testid="plot-xl"]',
            '[data-testid="plot-l"]',
            '.summary_text',
            '[data-testid="storyline-plot-summary"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ''
    
    def _extract_poster(self, soup):
        """提取海报图片URL"""
        selectors = [
            '[data-testid="hero-media__poster"] img',
            '.poster img',
            '.ipc-image'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src')
                if src:
                    return src
        
        return ''
    
    def _extract_countries(self, soup):
        """提取制片国家"""
        countries = []
        
        # 查找国家信息
        country_sections = soup.find_all(['span', 'div'], string=re.compile(r'Country|Countries'))
        for section in country_sections:
            parent = section.find_parent()
            if parent:
                links = parent.find_all('a')
                for link in links:
                    country = link.get_text(strip=True)
                    if country and country not in countries:
                        countries.append(country)
        
        return countries
    
    def _extract_languages(self, soup):
        """提取语言"""
        languages = []
        
        # 查找语言信息
        lang_sections = soup.find_all(['span', 'div'], string=re.compile(r'Language|Languages'))
        for section in lang_sections:
            parent = section.find_parent()
            if parent:
                links = parent.find_all('a')
                for link in links:
                    language = link.get_text(strip=True)
                    if language and language not in languages:
                        languages.append(language)
        
        return languages
    
    def _extract_release_date(self, soup):
        """提取上映日期"""
        selectors = [
            '[data-testid="title-details-releasedate"]',
            '.release_date'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return ''
    
    def _extract_budget(self, soup):
        """提取预算"""
        budget_sections = soup.find_all(['span', 'div'], string=re.compile(r'Budget'))
        for section in budget_sections:
            parent = section.find_parent()
            if parent:
                text = parent.get_text()
                budget_match = re.search(r'\$?([\d,]+)', text)
                if budget_match:
                    return budget_match.group(1)
        
        return ''
    
    def _extract_box_office(self, soup):
        """提取票房"""
        box_office_sections = soup.find_all(['span', 'div'], string=re.compile(r'Box office|Gross'))
        for section in box_office_sections:
            parent = section.find_parent()
            if parent:
                text = parent.get_text()
                box_office_match = re.search(r'\$?([\d,]+)', text)
                if box_office_match:
                    return box_office_match.group(1)
        
        return ''
    
    def _extract_awards(self, soup):
        """提取获奖信息"""
        awards = []
        
        awards_sections = soup.find_all(['span', 'div'], string=re.compile(r'Award|Oscar|Emmy|Golden Globe'))
        for section in awards_sections:
            awards.append(section.get_text(strip=True))
        
        return awards[:5]  # 限制前5个奖项
