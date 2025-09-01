#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网页解析器模块
负责解析豆瓣电影页面内容
"""

import re
from bs4 import BeautifulSoup
import logging


class PageParser:
    """网页内容解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_movie_list(self, response, url_type='chart'):
        """解析电影列表页面 - 增强版"""
        try:
            soup = BeautifulSoup(response.content, 'lxml')
            movie_links = []
            
            # 先检查页面是否有内容
            page_title = soup.find('title')
            if not page_title:
                self.logger.warning("页面没有title标签，可能是空页面或被反爬虫拦截")
                return []
            
            # 检查是否被重定向到验证页面
            if "验证" in page_title.get_text() or "安全验证" in page_title.get_text():
                self.logger.warning("页面被重定向到验证页面，触发了反爬虫机制")
                return []
            
            # 多种解析策略
            if url_type == 'chart':
                # 策略1: 标准榜单页面解析
                movie_elements = soup.find_all('div', class_='pl2')
                if not movie_elements:
                    # 策略2: 尝试其他可能的class名称
                    movie_elements = soup.find_all('div', class_='item')
                    if not movie_elements:
                        # 策略3: 查找所有包含电影链接的元素
                        movie_elements = soup.find_all('a', href=lambda x: x and '/subject/' in x)
                        for element in movie_elements:
                            if element.get('href'):
                                movie_links.append(element['href'])
                    else:
                        for element in movie_elements:
                            link = element.find('a', href=lambda x: x and '/subject/' in x)
                            if link and link.get('href'):
                                movie_links.append(link['href'])
                else:
                    for element in movie_elements:
                        link = element.find('a')
                        if link and link.get('href'):
                            movie_links.append(link['href'])
            
            elif url_type == 'typerank':
                # 分类排行页面解析 - 多策略
                movie_elements = soup.find_all('div', class_='pl2')
                if not movie_elements:
                    # 备用策略：查找所有电影链接
                    all_links = soup.find_all('a', href=lambda x: x and '/subject/' in x)
                    for link in all_links:
                        href = link.get('href')
                        if href and '/subject/' in href:
                            movie_links.append(href)
                else:
                    for element in movie_elements:
                        link = element.find('a')
                        if link and link.get('href'):
                            movie_links.append(link['href'])
            
            # 去重和清理
            movie_links = list(set(movie_links))
            
            # 调试信息
            if len(movie_links) == 0:
                self.logger.warning(f"页面解析结果为空，页面标题: {page_title.get_text()[:100] if page_title else 'None'}")
                # 保存页面内容用于调试
                debug_content = soup.get_text()[:500]
                self.logger.debug(f"页面内容片段: {debug_content}")
            
            self.logger.info(f"从列表页面解析到 {len(movie_links)} 个电影链接")
            return movie_links
            
        except Exception as e:
            self.logger.error(f"解析电影列表失败: {e}")
            return []
    
    def parse_movie_detail(self, response, movie_url):
        """解析电影详情页面"""
        try:
            soup = BeautifulSoup(response.content, 'lxml')
            
            movie_info = {
                'url': movie_url,
                'douban_id': self._extract_douban_id(movie_url)
            }
            
            # 基本信息解析
            movie_info.update(self._parse_basic_info(soup))
            
            # 评分信息解析
            movie_info.update(self._parse_rating_info(soup))
            
            # 演职人员信息解析
            movie_info.update(self._parse_cast_info(soup))
            
            # 电影详细信息解析
            movie_info.update(self._parse_movie_details(soup))
            
            # 封面图片解析
            movie_info.update(self._parse_poster(soup))
            
            # 简介解析
            movie_info.update(self._parse_summary(soup))
            
            # 标签解析
            movie_info.update(self._parse_tags(soup))
            
            self.logger.info(f"成功解析电影: {movie_info.get('title', 'Unknown')}")
            return movie_info
            
        except Exception as e:
            self.logger.error(f"解析电影详情失败: {movie_url}, 错误: {e}")
            return None
    
    def _extract_douban_id(self, url):
        """提取豆瓣ID"""
        match = re.search(r'/subject/(\d+)', url)
        return match.group(1) if match else None
    
    def _parse_basic_info(self, soup):
        """解析基本信息 - 增强版"""
        info = {}
        
        # 电影标题 - 尝试多种方法
        title_element = soup.find('span', property='v:itemreviewed')
        if not title_element:
            # 备用方法1：查找h1标签
            title_element = soup.find('h1')
            if title_element:
                # 如果h1包含year信息，需要清理
                title_text = title_element.get_text(strip=True)
                # 移除年份信息
                title_text = re.sub(r'\s*\(\d{4}\).*$', '', title_text)
                info['title'] = title_text
            else:
                # 备用方法2：从页面title提取
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text(strip=True)
                    # 清理标题，移除"(豆瓣)"等后缀
                    title_text = re.sub(r'\s*\(豆瓣\).*$', '', title_text)
                    title_text = re.sub(r'\s*\(\d{4}\).*$', '', title_text)
                    info['title'] = title_text
                else:
                    # 备用方法3：尝试其他可能的选择器
                    title_element = soup.find('div', id='content').find('h1') if soup.find('div', id='content') else None
                    info['title'] = title_element.get_text(strip=True) if title_element else 'Unknown'
        else:
            info['title'] = title_element.get_text(strip=True)
        
        # 确保标题不为空
        if not info.get('title'):
            info['title'] = 'Unknown Movie'
        
        # 年份 - 优化提取方法
        year_element = soup.find('span', class_='year')
        if year_element:
            year_text = year_element.get_text(strip=True)
            year_match = re.search(r'\((\d{4})\)', year_text)
            info['year'] = int(year_match.group(1)) if year_match else None
        else:
            # 备用方法：从页面标题或其他位置提取
            page_title = soup.find('title')
            if page_title:
                year_match = re.search(r'\((\d{4})\)', page_title.get_text())
                info['year'] = int(year_match.group(1)) if year_match else None
            else:
                info['year'] = None
        
        # 原名
        aka_elements = soup.find_all('span', string=re.compile(r'又名:|原名:'))
        original_titles = []
        for element in aka_elements:
            next_text = element.find_next_sibling(string=True)
            if next_text:
                original_titles.append(next_text.strip())
        
        info['original_title'] = ' / '.join(original_titles) if original_titles else ''
        
        return info
    
    def _parse_rating_info(self, soup):
        """解析评分信息"""
        info = {}
        
        # 平均评分
        rating_element = soup.find('strong', property='v:average')
        if rating_element and rating_element.text.strip():
            try:
                info['rating'] = float(rating_element.text.strip())
            except (ValueError, TypeError):
                info['rating'] = None
        else:
            info['rating'] = None
        
        # 评分人数
        rating_people = soup.find('a', class_='rating_people')
        if rating_people:
            rating_text = rating_people.text.strip()
            rating_count = re.search(r'(\d+)', rating_text)
            info['rating_count'] = int(rating_count.group(1)) if rating_count else None
        else:
            info['rating_count'] = None
        
        # 评分分布
        rating_per = soup.find_all('span', class_='rating_per')
        if len(rating_per) >= 5:
            for i, star_level in enumerate(['star_5', 'star_4', 'star_3', 'star_2', 'star_1']):
                try:
                    percent_text = rating_per[i].text.strip()
                    percent_match = re.search(r'(\d+\.?\d*)%', percent_text)
                    info[star_level] = float(percent_match.group(1)) if percent_match else 0.0
                except (ValueError, TypeError, IndexError):
                    info[star_level] = 0.0
        else:
            # 如果没有评分分布数据，设置默认值
            for star_level in ['star_5', 'star_4', 'star_3', 'star_2', 'star_1']:
                info[star_level] = 0.0
        
        return info
    
    def _parse_cast_info(self, soup):
        """解析演职人员信息"""
        info = {}
        
        # 导演
        directors = []
        director_elements = soup.find_all('a', rel='v:directedBy')
        for director in director_elements:
            directors.append(director.text.strip())
        info['directors'] = directors
        
        # 主演
        actors = []
        actor_elements = soup.find_all('a', rel='v:starring')
        for actor in actor_elements[:8]:  # 只取前8个主演
            actors.append(actor.text.strip())
        info['actors'] = actors
        
        return info
    
    def _parse_movie_details(self, soup):
        """解析电影详细信息"""
        info = {}
        
        # 类型
        genres = []
        genre_elements = soup.find_all('span', property='v:genre')
        for genre in genre_elements:
            genres.append(genre.text.strip())
        info['genres'] = genres
        
        # 上映时间
        release_dates = []
        release_elements = soup.find_all('span', property='v:initialReleaseDate')
        for release in release_elements:
            release_dates.append(release.text.strip())
        info['release_dates'] = release_dates
        
        # 片长
        runtime_element = soup.find('span', property='v:runtime')
        if runtime_element:
            runtime_text = runtime_element.text.strip()
            runtime_match = re.search(r'(\d+)', runtime_text)
            info['runtime_minutes'] = int(runtime_match.group(1)) if runtime_match else None
        
        # 从信息区域提取更多信息
        info_element = soup.find('div', id='info')
        if info_element:
            info_text = info_element.get_text()
            
            # 制片国家/地区
            country_match = re.search(r'制片国家/地区:\s*([^\n]+)', info_text)
            info['countries'] = [c.strip() for c in country_match.group(1).split('/')] if country_match else []
            
            # 语言
            language_match = re.search(r'语言:\s*([^\n]+)', info_text)
            info['languages'] = [l.strip() for l in language_match.group(1).split('/')] if language_match else []
            
            # IMDb链接
            imdb_match = re.search(r'IMDb:\s*([^\n]+)', info_text)
            info['imdb_id'] = imdb_match.group(1).strip() if imdb_match else None
        
        return info
    
    def _parse_summary(self, soup):
        """解析电影简介"""
        info = {}
        
        # 尝试多种方式获取简介
        summary_element = soup.find('span', property='v:summary')
        if summary_element:
            info['summary'] = summary_element.text.strip()
        else:
            # 尝试其他方式
            summary_div = soup.find('div', class_='related-info')
            if summary_div:
                summary_span = summary_div.find('span', class_='all hidden')
                if summary_span:
                    info['summary'] = summary_span.text.strip()
                else:
                    # 如果没有展开的简介，获取简短版本
                    short_summary = summary_div.find('span', class_='short')
                    if short_summary:
                        info['summary'] = short_summary.text.strip()
        
        return info
    
    def _parse_poster(self, soup):
        """解析电影封面图片"""
        info = {}
        
        try:
            # 尝试多种方式获取封面图片URL
            poster_img = soup.find('a', class_='nbgnbg')
            if poster_img:
                img_tag = poster_img.find('img')
                if img_tag and img_tag.get('src'):
                    info['poster_url'] = img_tag['src']
            
            # 备用方法1：查找电影海报区域
            if not info.get('poster_url'):
                poster_div = soup.find('div', id='mainpic')
                if poster_div:
                    img_tag = poster_div.find('img')
                    if img_tag and img_tag.get('src'):
                        info['poster_url'] = img_tag['src']
            
            # 备用方法2：查找任何电影相关图片
            if not info.get('poster_url'):
                img_tags = soup.find_all('img', alt=True)
                for img in img_tags:
                    if img.get('src') and ('doubanio.com' in img['src'] or 'movie' in img.get('alt', '').lower()):
                        info['poster_url'] = img['src']
                        break
                        
        except Exception as e:
            self.logger.warning(f"获取电影封面失败: {e}")
            info['poster_url'] = None
        
        return info
    
    def _parse_tags(self, soup):
        """解析电影标签"""
        info = {}
        
        tags = []
        try:
            tag_elements = soup.find_all('a', class_='tag')
            for tag in tag_elements[:15]:  # 最多获取15个标签
                tag_text = tag.text.strip()
                if tag_text and tag_text not in tags:  # 去重
                    tags.append(tag_text)
        except Exception as e:
            self.logger.warning(f"获取电影标签失败: {e}")
        
        info['tags'] = tags
        return info
