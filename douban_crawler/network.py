#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络请求模块
负责处理HTTP请求和浏览器操作
"""

import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from retrying import retry
import logging

from .config import Config


class NetworkManager:
    """网络请求管理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._setup_session()
    
    def _setup_session(self):
        """设置requests会话"""
        ua = UserAgent()
        headers = Config.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = ua.chrome
        self.session.headers.update(headers)
    
    @retry(stop_max_attempt_number=Config.MAX_RETRY_TIMES, wait_fixed=Config.RETRY_DELAY)
    def get_page(self, url, use_selenium=False):
        """获取网页内容"""
        try:
            if use_selenium:
                return self._get_with_selenium(url)
            else:
                return self._get_with_requests(url)
        except Exception as e:
            self.logger.warning(f"请求失败，正在重试: {url}, 错误: {e}")
            self._random_delay()
            raise e
    
    def _get_with_requests(self, url):
        """使用requests获取页面"""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response
    
    def _get_with_selenium(self, url):
        """使用Selenium获取页面（用于JavaScript渲染的页面）"""
        if not self.driver:
            self._init_chrome_driver()
        
        self.driver.get(url)
        time.sleep(2)  # 等待页面加载
        
        # 创建伪response对象
        class SeleniumResponse:
            def __init__(self, driver):
                self.content = driver.page_source.encode('utf-8')
                self.text = driver.page_source
                self.status_code = 200
        
        return SeleniumResponse(self.driver)
    
    def _init_chrome_driver(self):
        """初始化Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 添加配置选项
            for option in Config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 设置User-Agent
            chrome_options.add_argument(f'--user-agent={self.session.headers["User-Agent"]}')
            
            # 使用webdriver-manager自动管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.info("Chrome驱动初始化成功")
            
        except Exception as e:
            self.logger.error(f"Chrome驱动初始化失败: {e}")
            raise e
    
    def _random_delay(self):
        """随机延时"""
        delay = random.uniform(Config.DELAY_MIN, Config.DELAY_MAX)
        time.sleep(delay)
    
    def close(self):
        """关闭网络连接"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
