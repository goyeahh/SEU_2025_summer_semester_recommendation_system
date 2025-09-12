#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IMDB网络请求模块 - 反爬虫优化版本
负责处理HTTP请求和浏览器操作
"""

import requests
import time
import random
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from retrying import retry

from .config import IMDBConfig

# 抑制WebDriver Manager和TensorFlow日志
if IMDBConfig.LOG_CONFIG.get('level') == 'INFO':
    logging.getLogger('WDM').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    os.environ['WDM_LOG'] = '0'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class IMDBNetworkManager:
    """IMDB网络请求管理器 - 反爬虫增强版"""
    
    def __init__(self):
        self.session = requests.Session()
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._cookies_accepted = False
        self._driver_ready = False
        self._setup_session()
    
    def _setup_session(self):
        """设置requests会话（反爬虫优化版本）"""
        try:
            # 设置动态User-Agent池
            self._user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = random.choice(self._user_agents)
            headers['Referer'] = 'https://www.imdb.com/'
            headers['Accept-Language'] = 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
            headers['Accept-Encoding'] = 'gzip, deflate, br'
            headers['DNT'] = '1'
            headers['Upgrade-Insecure-Requests'] = '1'
            
            self.session.headers.update(headers)
        except Exception:
            # 如果设置失败，使用基础配置
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            self.session.headers.update(headers)
        
        # 启用连接池和Keep-Alive
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _rotate_user_agent(self):
        """轮换User-Agent以避免检测"""
        if hasattr(self, '_user_agents'):
            new_ua = random.choice(self._user_agents)
            self.session.headers['User-Agent'] = new_ua
            self.logger.debug(f"轮换IMDB User-Agent: {new_ua[:50]}...")
    
    def _is_blocked_response(self, response):
        """检测是否被反爬虫拦截"""
        if not response:
            return True
        
        # 检查状态码
        if response.status_code in [403, 429, 503]:
            return True
        
        # 检查页面内容
        content = response.text.lower() if hasattr(response, 'text') else str(response).lower()
        blocked_keywords = [
            'access denied', 'blocked', 'rate limit', 
            'too many requests', 'captcha', 'robot'
        ]
        
        return any(keyword in content for keyword in blocked_keywords)
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_page(self, url, use_selenium=None):
        """获取网页内容 - IMDB强制使用Selenium"""
        # IMDB对requests拦截严格，完全使用Selenium
        try:
            return self._get_with_selenium(url)
        except Exception as e:
            self.logger.warning(f"IMDB请求失败: {url}, 错误: {e}")
            raise e
    
    def _should_use_selenium(self, url):
        """IMDB强制使用Selenium，requests总是被拦截"""
        # IMDB对requests的拦截非常严格，直接使用Selenium
        return True
    
    def _get_with_requests(self, url):
        """使用requests获取页面 - 增强反爬虫"""
        # 轮换User-Agent
        self._rotate_user_agent()
        
        # 添加更多随机性的请求头
        headers = self.session.headers.copy()
        extra_headers = {
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-US,en;q=0.8,zh-CN;q=0.7,zh;q=0.6',
                'en-GB,en;q=0.9,en-US;q=0.8'
            ]),
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
        headers.update(extra_headers)
        
        # 添加随机延时
        self._random_delay()
        
        try:
            response = self.session.get(
                url, 
                headers=headers,
                timeout=IMDBConfig.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            
            # 检查是否被拦截
            if self._is_blocked_response(response):
                self.logger.warning(f"IMDB requests被拦截: {url}")
                return None
            
            response.raise_for_status()
            self.logger.debug(f"IMDB requests成功: {url}")
            return response.text
            
        except Exception as e:
            self.logger.warning(f"IMDB requests请求失败: {url}, 错误: {e}")
            return None
        
    def _get_with_selenium(self, url):
        """使用Selenium获取页面"""
        try:
            # 初始化driver
            if not self._driver_ready:
                self._init_chrome_driver()
            
            self.driver.get(url)
            self._random_delay()
            
            # 等待页面加载
            time.sleep(random.uniform(2, 4))
            
            # 处理Cookie同意（如果需要）
            if not self._cookies_accepted:
                self._handle_cookie_consent()
            
            # 获取页面源码
            page_source = self.driver.page_source
            self.logger.debug(f"IMDB Selenium成功: {url}")
            
            return page_source
            
        except Exception as e:
            self.logger.warning(f"IMDB Selenium请求失败: {url}, 错误: {e}")
            return None
    
    def _init_chrome_driver(self):
        """初始化Chrome驱动 - 反爬虫优化版本"""
        try:
            chrome_options = Options()
            
            # 使用配置中的Chrome选项
            for option in IMDBConfig.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 隐藏自动化特征和抑制输出
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("detach", True)
            
            # 创建驱动（抑制日志）
            service = Service(ChromeDriverManager().install())
            service.log_path = os.devnull  # 抑制ChromeDriver日志
            
            # 添加抑制DevTools输出的参数
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--remote-debugging-port=0')  # 禁用DevTools监听
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行反检测脚本
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self._driver_ready = True
            self.logger.info("✓ IMDB Chrome驱动初始化成功")
            
        except Exception as e:
            self.logger.error(f"IMDB Chrome驱动初始化失败: {e}")
            raise
    
    def _handle_cookie_consent(self):
        """处理Cookie同意弹窗"""
        try:
            # IMDB可能的Cookie同意按钮
            accept_selectors = [
                "button[data-testid='accept-button']",
                "button[class*='accept']",
                ".accept-cookies",
                "#accept-cookies"
            ]
            
            for selector in accept_selectors:
                try:
                    element = self.driver.find_element("css selector", selector)
                    if element.is_displayed():
                        element.click()
                        self.logger.info("IMDB Cookie同意已处理")
                        self._cookies_accepted = True
                        time.sleep(1)
                        return
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"IMDB处理Cookie同意失败（可忽略）: {e}")
        
        self._cookies_accepted = True  # 标记为已处理，避免重复尝试
    
    def _random_delay(self):
        """添加随机延时"""
        delay = random.uniform(1, 3)
        time.sleep(delay)
    
    def close(self):
        """关闭所有连接"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self._driver_ready = False
                self.logger.info("IMDB Chrome驱动已关闭")
        except Exception as e:
            self.logger.warning(f"关闭IMDB Chrome驱动失败: {e}")
        
        try:
            self.session.close()
            self.logger.info("IMDB requests会话已关闭")
        except Exception as e:
            self.logger.warning(f"关闭IMDB requests会话失败: {e}")
    
    def __del__(self):
        """析构函数"""
        self.close()
