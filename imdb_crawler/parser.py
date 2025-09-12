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
    
    def __init__(self, network_manager=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.imdb.com"
        self.network_manager = network_manager
        
        # 从配置中获取输出控制设置
        from .config import IMDBConfig
        self.show_parsing_details = getattr(config or IMDBConfig, 'SHOW_PARSING_SUCCESS', True)
    
    def parse_movie_list(self, response, url_type='chart'):
        """
        解析电影列表页面，获取电影详情页链接 - 增强反爬虫检测
        
        Args:
            response: HTTP响应对象或HTML字符串
            url_type: URL类型 ('chart', 'search', 'top250')
            
        Returns:
            list: 电影详情页链接列表
        """
        movie_links = []
        
        try:
            # 处理不同类型的响应
            if hasattr(response, 'text'):
                html_content = response.text
                response_url = getattr(response, 'url', '')
            elif isinstance(response, str):
                html_content = response
                response_url = ''
            else:
                self.logger.error("无效的响应对象类型")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 检查页面是否被反爬虫拦截
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if any(keyword in title_text for keyword in ['blocked', 'forbidden', 'access denied', 'error']):
                    self.logger.warning("IMDB页面被反爬虫拦截")
                    return []
            
            # 检查页面内容长度
            if len(html_content) < 1000:
                self.logger.warning("IMDB页面内容过短，可能被拦截")
                return []
            
            if url_type == 'chart' or 'chart' in response_url:
                # 处理榜单页面
                movie_links.extend(self._parse_chart_page(soup))
            
            elif url_type == 'search' or 'search' in response_url:
                # 处理搜索结果页面
                movie_links.extend(self._parse_search_page(soup))
            
            elif 'top' in response_url:
                # 处理Top250等页面
                movie_links.extend(self._parse_top_page(soup))
            
            else:
                # 默认尝试多种解析方式
                movie_links.extend(self._parse_generic_page(soup))
            
            # 去重并转换为完整URL
            unique_links = list(set(movie_links))
            full_links = [urljoin(self.base_url, link) for link in unique_links if link]
            
            # 调试信息
            if len(full_links) == 0:
                self.logger.warning(f"IMDB页面解析结果为空，页面标题: {page_title.get_text()[:100] if page_title else 'None'}")
                debug_content = soup.get_text()[:500]
                self.logger.debug(f"页面内容片段: {debug_content}")
            
            self.logger.info(f"从IMDB页面解析到 {len(full_links)} 个电影链接")
            return full_links
            
        except Exception as e:
            self.logger.error(f"解析IMDB电影列表页面失败: {e}")
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
            response: HTTP响应对象或HTML字符串
            movie_url: 电影详情页URL
            
        Returns:
            dict: 电影信息字典
        """
        try:
            # 处理不同类型的响应
            if hasattr(response, 'text'):
                html_content = response.text
            elif isinstance(response, str):
                html_content = response
            else:
                self.logger.error(f"无效的响应对象类型: {type(response)}")
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取电影信息 - 仅保留数据库需要的字段
            movie_info = {
                'title': self._extract_title(soup),
                'year': self._extract_year(soup),
                'rating': self._extract_rating(soup),
                'genres': self._extract_genres(soup),
                'duration': self._extract_duration(soup),
                'directors': self._extract_directors(soup),
                'actors': self._extract_actors(soup),
                'plot': self._extract_plot(soup),
                'poster_url': self._extract_poster(soup),
                'countries': self._extract_countries(soup),
                'rating_distribution': self._extract_rating_distribution_from_url(movie_url)
            }
            
            # 调试日志
            self.logger.info(f"解析结果: 标题='{movie_info['title']}', 评分={movie_info['rating']}")
            
            return movie_info
            
        except Exception as e:
            self.logger.error(f"解析电影详情失败 {movie_url}: {e}")
            return None
    
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

    def _extract_year(self, soup):
        """提取上映年份 - 优化版本"""
        # 1. 尝试从hero标题块的元数据提取
        metadata_links = soup.select('[data-testid="hero-title-block__metadata"] a')
        for link in metadata_links:
            href = link.get('href', '')
            if '/year/' in href:
                year_match = re.search(r'/year/(\d{4})/', href)
                if year_match:
                    return int(year_match.group(1))
        
        # 2. 尝试从页面文本中提取年份
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # 匹配1900-2099年
        ]
        
        # 在标题区域查找
        title_section = soup.select_one('[data-testid="hero-title-block__metadata"]')
        if title_section:
            text = title_section.get_text()
            for pattern in year_patterns:
                match = re.search(pattern, text)
                if match:
                    year = int(match.group())
                    if 1880 <= year <= 2030:  # 合理的电影年份范围
                        return year
        
        # 3. 从页面标题提取
        page_title = soup.find('title')
        if page_title:
            title_text = page_title.get_text()
            year_match = re.search(r'\((\d{4})\)', title_text)
            if year_match:
                return int(year_match.group(1))
        
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

    def _extract_genres(self, soup):
        """提取电影类型 - 优化版本"""
        genres = []
        
        # 1. 首先尝试从genres测试ID提取
        genre_elements = soup.select('[data-testid="genres"] a, [data-testid="genres"] span')
        for element in genre_elements:
            genre = element.get_text(strip=True)
            if genre and genre not in genres:
                genres.append(genre)
        
        # 2. 如果没找到，尝试其他选择器
        if not genres:
            selectors = [
                '.ipc-chip-list__scroller a',
                '.sc-16ede01-3 a',
                '[class*="genre"] a',
                'a[href*="/search/title/?genres="]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    genre = element.get_text(strip=True)
                    # 过滤掉明显不是类型的文本
                    if (genre and genre not in genres and 
                        len(genre) < 20 and  # 类型名通常较短
                        not any(word in genre.lower() for word in ['see', 'more', 'all', 'imdb'])):
                        genres.append(genre)
        
        # 3. 最后尝试从JSON-LD数据提取
        if not genres:
            json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'genre' in data:
                        genre_data = data['genre']
                        if isinstance(genre_data, list):
                            genres.extend(genre_data)
                        elif isinstance(genre_data, str):
                            genres.append(genre_data)
                except:
                    continue
        
        return genres[:10]  # 限制最多10个类型
    
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
        """提取导演 - 优化版本"""
        directors = []
        
        # 1. 尝试从principal credits提取导演
        credits_sections = soup.select('[data-testid="title-pc-principal-credit"]')
        for section in credits_sections:
            # 查找包含"Director"的部分
            section_text = section.get_text()
            if 'Director' in section_text:
                # 提取该部分的所有链接
                links = section.select('a')
                for link in links:
                    name = link.get_text(strip=True)
                    if (name and name not in directors and 
                        not any(word in name.lower() for word in ['director', 'more', 'see', 'full'])):
                        directors.append(name)
        
        # 2. 如果没找到，尝试其他方法
        if not directors:
            # 查找包含"Director"文本的区域
            for element in soup.find_all(text=re.compile(r'Director', re.I)):
                parent = element.parent
                if parent:
                    # 在父元素及其兄弟元素中查找链接
                    for sibling in parent.find_next_siblings():
                        links = sibling.find_all('a') if sibling else []
                        for link in links:
                            name = link.get_text(strip=True)
                            if (name and name not in directors and 
                                not any(word in name.lower() for word in ['director', 'more', 'see'])):
                                directors.append(name)
                                break
                    if directors:
                        break
        
        # 3. 尝试从JSON-LD数据提取
        if not directors:
            json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'director' in data:
                        director_data = data['director']
                        if isinstance(director_data, list):
                            for director in director_data:
                                if isinstance(director, dict) and 'name' in director:
                                    directors.append(director['name'])
                                elif isinstance(director, str):
                                    directors.append(director)
                        elif isinstance(director_data, dict) and 'name' in director_data:
                            directors.append(director_data['name'])
                except:
                    continue
        
        return directors[:5]  # 限制最多5个导演
    
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

    def _extract_rating_distribution_from_url(self, movie_url):
        """从IMDB ratings页面提取评分分布数据"""
        try:
            # 构建ratings页面URL
            movie_id_match = re.search(r'/title/(tt\d+)/', movie_url)
            if not movie_id_match:
                self.logger.warning(f"无法从URL中提取电影ID: {movie_url}")
                return {}
            
            movie_id = movie_id_match.group(1)
            ratings_url = f"https://www.imdb.com/title/{movie_id}/ratings/"
            
            if self.network_manager:
                # 获取ratings页面 - 精简日志
                response = self.network_manager.get_page(ratings_url)
                if response:
                    soup = BeautifulSoup(response, 'html.parser')
                    distribution = self._parse_rating_distribution(soup)
                    if distribution:
                        # 只在详细模式下显示成功信息
                        if getattr(self, 'show_parsing_details', True):
                            self.logger.info(f"✓ 评分分布解析成功: {len(distribution)} 个等级")
                        return distribution
                    else:
                        self.logger.warning(f"未能解析到评分分布数据: {ratings_url}")
                else:
                    self.logger.warning(f"无法访问ratings页面: {ratings_url}")
            else:
                self.logger.warning("网络管理器未初始化，无法获取ratings页面")
            
            return {}
            
        except Exception as e:
            self.logger.error(f"获取评分分布数据失败 {movie_url}: {e}")
            return {}

    def _parse_rating_distribution(self, soup):
        """解析ratings页面的评分分布数据"""
        distribution = {}
        
        try:
            self.logger.debug("开始解析IMDB ratings页面的评分分布数据")
            
            # 获取页面文本
            page_text = soup.get_text()
            
            # 根据IMDB ratings页面的实际结构进行解析
            # 关键发现：评分数字1-10被连续显示为"1234567891"，然后紧跟着百分比数据
            # 格式: "1234567891038.3% (591K)31.6% (488K)17.8% (274K)..."
            # 实际含义: 10分:38.3%, 9分:31.6%, 8分:17.8%...
            
            self.logger.debug(f"页面文本长度: {len(page_text)}")
            
            # 方法1: 查找连续评分序列后的百分比数据
            # 查找模式: "1234567891" + 百分比数据序列
            sequence_pattern = r'1234567891(\d+\.?\d*)%\s*\([^)]+\)(.*?)(?:Unweighted mean|More from)'
            sequence_match = re.search(sequence_pattern, page_text, re.DOTALL)
            
            if sequence_match:
                self.logger.debug("找到连续评分序列，开始解析")
                
                # 第一个百分比数据（10分）
                first_percentage = float(sequence_match.group(1))
                distribution["10"] = first_percentage
                self.logger.debug(f"评分 10 分: {first_percentage}%")
                
                # 解析后续的百分比数据（9分到1分）
                remaining_text = sequence_match.group(2)
                
                # 查找所有后续的百分比数据
                percent_pattern = r'(\d+\.?\d*)%\s*\([^)]+\)'
                percent_matches = re.findall(percent_pattern, remaining_text)
                
                # 按顺序分配给9,8,7,6,5,4,3,2,1分
                for i, percent_str in enumerate(percent_matches[:9]):  # 只取前9个（9分到1分）
                    try:
                        percentage = float(percent_str)
                        rating_score = str(9 - i)  # 9, 8, 7, 6, 5, 4, 3, 2, 1
                        distribution[rating_score] = percentage
                        self.logger.debug(f"评分 {rating_score} 分: {percentage}%")
                    except ValueError:
                        continue
            
            # 方法2: 如果方法1失败，尝试查找所有K格式数据并按IMDB标准顺序分配
            if len(distribution) < 8:
                self.logger.debug("连续序列解析不足，尝试标准K格式解析")
                
                # 查找所有K/M格式的百分比数据
                k_pattern = r'(\d+\.?\d*)%\s*\([^)]*[KM]\)'
                k_matches = re.findall(k_pattern, page_text)
                
                # 过滤合理的百分比（排除异常值）
                valid_percentages = []
                for match in k_matches:
                    try:
                        pct = float(match)
                        # 第一个可能是异常值（包含连续数字），跳过超大值
                        if pct > 1000:
                            # 提取正确的百分比部分
                            # 例如从"1234567891038.3"中提取"38.3"
                            if len(str(int(pct))) > 3:
                                pct_str = str(pct)
                                if '.' in pct_str:
                                    # 查找小数点，取小数点前的最后几位和小数部分
                                    decimal_pos = pct_str.find('.')
                                    if decimal_pos > 2:
                                        corrected_pct = float(pct_str[decimal_pos-2:])
                                        if 0.1 <= corrected_pct <= 60:
                                            valid_percentages.append(corrected_pct)
                                            continue
                        elif 0.1 <= pct <= 60:
                            valid_percentages.append(pct)
                    except ValueError:
                        continue
                
                self.logger.debug(f"K格式解析找到 {len(valid_percentages)} 个有效百分比: {valid_percentages}")
                
                # 如果找到足够的数据，按IMDB标准顺序分配（10到1）
                if len(valid_percentages) >= 10:
                    distribution.clear()  # 清空之前的部分数据
                    
                    for i, percentage in enumerate(valid_percentages[:10]):
                        rating_score = str(10 - i)  # 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
                        distribution[rating_score] = percentage
                        self.logger.debug(f"标准顺序 - 评分 {rating_score} 分: {percentage}%")
            
            # 方法3: 最后的精确匹配备用方案
            if len(distribution) < 5:
                self.logger.debug("使用精确匹配备用方案")
                
                # 查找更宽泛的百分比数据
                all_percent_pattern = r'(\d+\.?\d*)%\s*\([^)]+\)'
                all_matches = re.findall(all_percent_pattern, page_text)
                
                # 过滤并处理数据
                backup_percentages = []
                for match in all_matches:
                    try:
                        pct = float(match)
                        if pct > 1000:
                            # 处理连续数字情况
                            pct_str = str(pct)
                            if '.' in pct_str:
                                decimal_pos = pct_str.find('.')
                                if decimal_pos > 2:
                                    corrected_pct = float(pct_str[decimal_pos-2:])
                                    if 0.1 <= corrected_pct <= 60:
                                        backup_percentages.append(corrected_pct)
                                        continue
                        elif 0.1 <= pct <= 60:
                            backup_percentages.append(pct)
                    except ValueError:
                        continue
                
                self.logger.debug(f"备用方案找到 {len(backup_percentages)} 个百分比: {backup_percentages}")
                
                if len(backup_percentages) >= 10:
                    distribution.clear()
                    for i, percentage in enumerate(backup_percentages[:10]):
                        rating_score = str(10 - i)
                        distribution[rating_score] = percentage
                        self.logger.debug(f"备用分配 - 评分 {rating_score} 分: {percentage}%")
            
            # 验证获取到的数据
            if distribution:
                total_percentage = sum(distribution.values())
                
                # 精简日志输出 - 只显示核心信息
                if getattr(self, 'show_parsing_details', True):
                    self.logger.info(f"✓ 评分分布: {len(distribution)}等级 (总计{total_percentage:.1f}%)")
                    
                    # 详细分布信息 - 在调试模式下才显示
                    if self.logger.isEnabledFor(logging.DEBUG):
                        for rating in sorted(distribution.keys(), key=int, reverse=True):
                            self.logger.debug(f"  {rating}分: {distribution[rating]}%")
                
                # 如果总百分比明显不合理，记录警告但保留数据
                if total_percentage > 120 or total_percentage < 80:
                    self.logger.warning(f"评分分布数据可能不完整，总百分比为{total_percentage:.1f}%")
                    
            else:
                self.logger.warning("未能在ratings页面中找到评分分布数据")
                # 保存页面内容的关键部分用于调试
                key_content = page_text[:2000] if len(page_text) > 2000 else page_text
                if any(char in key_content for char in ['%', '1', '2', '3', '4', '5']):
                    self.logger.debug(f"页面关键内容: {key_content}")
            
        except Exception as e:
            self.logger.error(f"解析评分分布时出错: {e}")
        
        return distribution

    def _extract_rating_distribution(self, soup):
        """提取评分分布 (1-10分的百分比)"""
        distribution = {}
        
        # 尝试从rating histogram或breakdown获取分布数据
        # IMDB的评分分布通常在专门的评分页面或通过API获取
        # 这里先返回空字典，在实际应用中可能需要额外的请求
        
        # 查找可能的评分分布数据
        rating_elements = soup.select('[class*="rating"], [class*="histogram"], [data-testid*="rating"]')
        for element in rating_elements:
            text = element.get_text()
            # 尝试匹配百分比数据
            percent_matches = re.findall(r'(\d+).*?(\d+\.?\d*)%', text)
            for match in percent_matches:
                try:
                    rating_score = int(match[0])
                    percentage = float(match[1])
                    if 1 <= rating_score <= 10:
                        distribution[str(rating_score)] = percentage
                except:
                    continue
        
        # 如果没有找到分布数据，返回空字典
        return distribution
