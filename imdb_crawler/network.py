#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB网络请求模块
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

from .config import IMDBConfig


class IMDBNetworkManager:
    """IMDB网络请求管理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._setup_session()
    
    def _setup_session(self):
        """设置requests会话"""
        try:
            ua = UserAgent()
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = ua.chrome
            self.session.headers.update(headers)
        except Exception:
            # 如果UserAgent失败，使用默认的
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            self.session.headers.update(headers)
    
    @retry(stop_max_attempt_number=IMDBConfig.MAX_RETRY_TIMES, wait_fixed=IMDBConfig.RETRY_DELAY)
    def get_page(self, url, use_selenium=True):
        """获取网页内容 - IMDB通常需要JavaScript渲染"""
        try:
            if use_selenium:
                return self._get_with_selenium(url)
            else:
                return self._get_with_requests(url)
        except Exception as e:
            self.logger.warning(f"请求失败，正在重试: {url}, 错误: {e}")
            # 如果Selenium失败，尝试requests作为备用
            if use_selenium:
                try:
                    self.logger.info("Selenium失败，尝试使用requests")
                    return self._get_with_requests(url)
                except Exception as requests_error:
                    self.logger.warning(f"requests也失败: {requests_error}")
            
            self._random_delay()
            raise e
    
    def _get_with_requests(self, url):
        """使用requests获取页面"""
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response
    
    def _get_with_selenium(self, url):
        """使用Selenium获取页面（IMDB主要使用这种方式）"""
        if not self.driver:
            self._init_chrome_driver()
        
        self.driver.get(url)
        
        # 等待页面加载完成
        time.sleep(3)
        
        # 检查是否需要接受cookies
        try:
            accept_button = self.driver.find_elements("css selector", "[data-testid='accept-button']")
            if accept_button:
                accept_button[0].click()
                time.sleep(2)
        except Exception:
            pass
        
        # 创建伪response对象
        class SeleniumResponse:
            def __init__(self, driver):
                self.content = driver.page_source.encode('utf-8')
                self.text = driver.page_source
                self.status_code = 200
                self.url = driver.current_url
        
        return SeleniumResponse(self.driver)
    
    def _init_chrome_driver(self):
        """初始化Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 添加配置选项
            for option in IMDBConfig.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 禁用自动化检测
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 添加更多稳定性配置
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            
            # 使用webdriver-manager自动管理驱动
            service = Service(ChromeDriverManager().install())
            
            # 设置更长的超时时间
            service.start_error_message = "Chrome driver failed to start"
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # 执行脚本隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("IMDB Chrome驱动初始化成功")
            
        except Exception as e:
            self.logger.error(f"IMDB Chrome驱动初始化失败: {e}")
            # 如果Chrome驱动失败，尝试降级到requests
            self.logger.info("尝试使用requests作为备用方案")
            self.driver = None
            raise e
    
    def _random_delay(self):
        """随机延时"""
        delay = random.uniform(IMDBConfig.DELAY_MIN, IMDBConfig.DELAY_MAX)
        time.sleep(delay)
    
    def close(self):
        """关闭连接"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome驱动已关闭")
            except Exception as e:
                self.logger.warning(f"关闭Chrome驱动时出错: {e}")
        
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                self.logger.warning(f"关闭session时出错: {e}")
    
    def __del__(self):
        """析构函数"""
        self.close()
