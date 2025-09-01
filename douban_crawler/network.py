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
    def get_page(self, url, use_selenium=False, force_selenium=False):
        """获取网页内容 - 智能策略"""
        try:
            # 智能选择请求方式
            if force_selenium or self._should_use_selenium(url):
                return self._get_with_selenium(url)
            else:
                response = self._get_with_requests(url)
                
                # 检查响应是否被反爬虫拦截
                if self._is_blocked_response(response):
                    self.logger.warning(f"检测到反爬虫拦截，切换到Selenium: {url}")
                    return self._get_with_selenium(url)
                
                return response
        except Exception as e:
            self.logger.warning(f"请求失败，正在重试: {url}, 错误: {e}")
            self._random_delay()
            raise e
    
    def _should_use_selenium(self, url):
        """判断是否应该使用Selenium"""
        # 对于某些特定页面或高页数使用Selenium
        if 'typerank' in url and ('start=75' in url or 'start=100' in url):
            return True
        if 'chart' in url and any(x in url for x in ['start=200', 'start=225']):
            return True
        return False
    
    def _is_blocked_response(self, response):
        """检查响应是否被反爬虫拦截"""
        # 检查状态码
        if response.status_code in [403, 429, 503]:
            return True
        
        # 检查内容长度
        if len(response.content) < 1000:  # 页面内容太短可能是被拦截
            return True
        
        # 检查页面内容
        content_text = response.text.lower()
        blocked_keywords = ['验证', '安全验证', 'captcha', 'blocked', '拒绝访问', '访问被限制']
        if any(keyword in content_text for keyword in blocked_keywords):
            return True
        
        return False
    
    def _get_with_requests(self, url):
        """使用requests获取页面"""
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response
    
    def _get_with_selenium(self, url):
        """使用Selenium获取页面（用于JavaScript渲染的页面）"""
        if not self.driver:
            self._init_chrome_driver()
        
        if not self.driver:
            # 如果驱动初始化失败，回退到requests
            self.logger.warning("Chrome驱动不可用，回退到requests")
            return self._get_with_requests(url)
        
        try:
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            
            # 创建伪response对象
            class SeleniumResponse:
                def __init__(self, driver):
                    self.content = driver.page_source.encode('utf-8')
                    self.text = driver.page_source
                    self.status_code = 200
            
            return SeleniumResponse(self.driver)
        
        except Exception as e:
            self.logger.warning(f"Selenium获取页面失败: {e}")
            # 尝试用requests作为备用
            return self._get_with_requests(url)
    
    def _init_chrome_driver(self):
        """初始化Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            
            # 添加配置选项
            for option in Config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 设置User-Agent
            chrome_options.add_argument(f'--user-agent={self.session.headers["User-Agent"]}')
            
            # 添加更多稳定性配置
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 使用webdriver-manager自动管理驱动
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置超时
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info("Chrome驱动初始化成功")
            
        except Exception as e:
            self.logger.error(f"Chrome驱动初始化失败: {e}")
            self.logger.info("将使用requests作为备用方案")
            self.driver = None
            # 不抛出异常，允许继续使用requests
    
    def _random_delay(self):
        """随机延时"""
        delay = random.uniform(Config.DELAY_MIN, Config.DELAY_MAX)
        time.sleep(delay)
    
    def _rotate_user_agent(self):
        """轮换User-Agent"""
        try:
            ua = UserAgent()
            new_ua = ua.chrome
            self.session.headers.update({'User-Agent': new_ua})
            if self.driver:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": new_ua})
        except Exception as e:
            self.logger.warning(f"轮换User-Agent失败: {e}")
    
    def get_with_retry_and_rotation(self, url, max_attempts=3):
        """带用户代理轮换的重试请求"""
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    self._rotate_user_agent()
                    self._random_delay()
                
                return self.get_page(url)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                self.logger.warning(f"请求失败，正在轮换UA重试 ({attempt+1}/{max_attempts}): {e}")
        
        return None
    
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
