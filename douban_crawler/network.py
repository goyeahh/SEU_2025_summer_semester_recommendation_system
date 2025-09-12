#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络请求模块 - 豆瓣纯Selenium版（参考IMDB配置）
负责处理HTTP请求和浏览器操作，优化反爬虫策略
"""

import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from retrying import retry
import logging

from .config import Config

# 抑制WebDriver Manager日志
logging.getLogger('WDM').setLevel(logging.WARNING)
os.environ['WDM_LOG'] = '0'


class NetworkManager:
    """网络请求管理器 - 豆瓣反爬虫增强版"""
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._cookies_accepted = False
        self._driver_ready = False
        
        # 用户代理池 - 参考IMDB
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_page(self, url, use_selenium=None):
        """获取网页内容 - 豆瓣强制使用Selenium（参考IMDB）"""
        # 豆瓣对requests拦截严格，完全使用Selenium
        try:
            return self._get_with_selenium(url)
        except Exception as e:
            self.logger.warning(f"豆瓣请求失败: {url}, 错误: {e}")
            raise e
    
    def _smart_delay(self):
        """智能延时控制 - 纯Selenium模式"""
        current_time = time.time()
        self._request_count += 1
        
        # 基础延时 - 纯Selenium模式使用更长延时
        base_delay = random.uniform(Config.DELAY_MIN, Config.DELAY_MAX)
        
        # 根据请求频率调整延时
        if self._request_count > 20:
            base_delay *= 1.5  # 高频访问时增加延时
        elif self._request_count > 40:
            base_delay *= 2.5  # 超高频访问时大幅增加延时
        
        # 确保与上次请求间隔足够
        if self._last_request_time > 0:
            time_since_last = current_time - self._last_request_time
            if time_since_last < base_delay:
                additional_delay = base_delay - time_since_last
                time.sleep(additional_delay)
        
        self._last_request_time = time.time()
        self.logger.info(f"延时 {base_delay:.1f} 秒 (第 {self._request_count} 次请求)")
    
    def _get_with_selenium(self, url):
        """使用Selenium获取页面（参考IMDB配置）"""
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
            self.logger.debug(f"豆瓣Selenium成功: {url}")
            
            # 创建伪response对象（兼容解析器）
            class SeleniumResponse:
                def __init__(self, page_source, url):
                    self.content = page_source.encode('utf-8')
                    self.text = page_source
                    self.status_code = 200
                    self.url = url
                    
                def json(self):
                    return {}
            
            return SeleniumResponse(page_source, url)
            
        except Exception as e:
            self.logger.warning(f"豆瓣Selenium请求失败: {url}, 错误: {e}")
            return None
    
    def _init_chrome_driver(self):
        """初始化Chrome驱动 - 完全参考IMDB配置"""
        try:
            chrome_options = Options()
            
            # 使用豆瓣配置中的Chrome选项（参考IMDB）
            for option in Config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 隐藏自动化特征和抑制输出（参考IMDB）
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("detach", True)
            
            # 创建驱动（抑制日志）- 参考IMDB
            service = Service(ChromeDriverManager().install())
            service.log_path = os.devnull  # 抑制ChromeDriver日志
            
            # 添加抑制DevTools输出的参数（参考IMDB）
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--remote-debugging-port=0')  # 禁用DevTools监听
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行反检测脚本（参考IMDB）
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self._driver_ready = True
            self.logger.info("✓ 豆瓣Chrome驱动初始化成功（IMDB配置）")
            
        except Exception as e:
            self.logger.error(f"豆瓣Chrome驱动初始化失败: {e}")
            raise
            
        except Exception as e:
            self.logger.error(f"豆瓣Chrome驱动初始化失败: {e}")
            self.driver = None
            self._driver_ready = False
            raise Exception(f"Selenium驱动初始化失败，无法继续: {e}")
    
    def _handle_cookie_consent(self):
        """处理Cookie同意弹窗（参考IMDB）"""
        try:
            # 豆瓣可能的Cookie同意按钮
            accept_selectors = [
                "button[class*='accept']",
                ".accept-cookies",
                "#accept-cookies",
                "button[data-testid='accept-button']"
            ]
            
            for selector in accept_selectors:
                try:
                    element = self.driver.find_element("css selector", selector)
                    if element.is_displayed():
                        element.click()
                        self.logger.info("豆瓣Cookie同意已处理")
                        self._cookies_accepted = True
                        time.sleep(1)
                        return
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"豆瓣处理Cookie同意失败（可忽略）: {e}")
        
        self._cookies_accepted = True  # 标记为已处理，避免重复尝试
    
    def _random_delay(self):
        """添加随机延时（参考IMDB）"""
        delay = random.uniform(Config.DELAY_MIN, Config.DELAY_MAX)
        time.sleep(delay)
    
    def close(self):
        """关闭所有连接（参考IMDB）"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self._driver_ready = False
                self.logger.info("豆瓣Chrome驱动已关闭")
        except Exception as e:
            self.logger.warning(f"关闭豆瓣Chrome驱动失败: {e}")
    
    def __del__(self):
        """析构函数（参考IMDB）"""
        self.close()
    
    def _rotate_user_agent(self):
        """轮换User-Agent - 增强版"""
        try:
            new_ua = random.choice(self._user_agents)
            self.session.headers.update({'User-Agent': new_ua})
            
            # 如果使用Selenium，也更新浏览器的User-Agent
            if self.driver and self._driver_ready:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": new_ua})
                
            self.logger.debug(f"轮换豆瓣User-Agent: {new_ua[:50]}...")
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
