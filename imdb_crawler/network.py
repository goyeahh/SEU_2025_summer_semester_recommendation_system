#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB网络请求模块
处理所有HTTP请求和浏览器自动化操作
"""

import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from .config import IMDBConfig


class IMDBNetwork:
    """IMDB网络请求处理类"""
    
    def __init__(self, config=None):
        """
        初始化网络请求处理器
        
        Args:
            config: 配置对象，默认使用IMDBConfig
        """
        self.config = config or IMDBConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.DEFAULT_HEADERS)
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
        # 添加随机User-Agent轮换
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        ]
        
        # 设置请求会话
        self.session.headers.update({
            'Referer': 'https://www.imdb.com/',
            'Origin': 'https://www.imdb.com'
        })
    
    def get_page(self, url, use_selenium=False, wait_element=None, timeout=10):
        """
        获取网页内容
        
        Args:
            url: 目标URL
            use_selenium: 是否使用Selenium
            wait_element: 等待的元素选择器
            timeout: 超时时间
            
        Returns:
            str: 网页HTML内容，失败返回None
        """
        for attempt in range(self.config.RETRY_TIMES):
            try:
                if use_selenium:
                    return self._get_page_selenium(url, wait_element, timeout)
                else:
                    return self._get_page_requests(url)
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次请求失败: {url}, 错误: {e}")
                if attempt < self.config.RETRY_TIMES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                else:
                    self.logger.error(f"请求失败，已重试 {self.config.RETRY_TIMES} 次: {url}")
                    return None
    
    def _get_page_requests(self, url):
        """
        使用requests获取网页
        
        Args:
            url: 目标URL
            
        Returns:
            str: 网页HTML内容
        """
        # 随机选择User-Agent
        import random
        user_agent = random.choice(self._user_agents)
        headers = {'User-Agent': user_agent}
        
        # 随机延时
        delay = random.uniform(self.config.DELAY_MIN, self.config.DELAY_MAX)
        time.sleep(delay)
        
        response = self.session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.text
    
    def _get_page_selenium(self, url, wait_element=None, timeout=10):
        """
        使用Selenium获取网页
        
        Args:
            url: 目标URL
            wait_element: 等待的元素选择器
            timeout: 超时时间
            
        Returns:
            str: 网页HTML内容
        """
        if not self.driver:
            self._init_driver()
        
        self.driver.get(url)
        
        # 等待特定元素加载
        if wait_element:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_element)))
        
        # 随机滚动页面，模拟真实用户行为
        self._random_scroll()
        
        return self.driver.page_source
    
    def _init_driver(self):
        """初始化Chrome WebDriver"""
        try:
            chrome_options = Options()
            for option in self.config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 禁用图片加载以提高速度
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.info("Chrome WebDriver 初始化成功")
            
        except Exception as e:
            self.logger.error(f"Chrome WebDriver 初始化失败: {e}")
            raise
    
    def _random_scroll(self):
        """随机滚动页面"""
        if not self.driver:
            return
        
        try:
            # 获取页面高度
            height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 随机滚动几次
            for _ in range(random.randint(1, 3)):
                scroll_position = random.randint(0, height)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(random.uniform(0.5, 1.5))
                
        except Exception as e:
            self.logger.warning(f"页面滚动失败: {e}")
    
    def download_image(self, url, filepath):
        """
        下载图片
        
        Args:
            url: 图片URL
            filepath: 保存路径
            
        Returns:
            bool: 是否成功下载
        """
        try:
            # 设置图片下载的请求头
            headers = self.config.DEFAULT_HEADERS.copy()
            headers.update({
                'Referer': 'https://www.imdb.com/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            })
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"成功下载图片: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"图片下载失败 {url}: {e}")
            return False
    
    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver 已关闭")
            except Exception as e:
                self.logger.error(f"关闭 WebDriver 失败: {e}")
            finally:
                self.driver = None
    
    def __del__(self):
        """析构函数，确保WebDriver被正确关闭"""
        self.close_driver()
