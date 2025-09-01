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
        self._cookies_accepted = False
        self._driver_ready = False
        self._setup_session()
    
    def _setup_session(self):
        """设置requests会话（优化版本）"""
        try:
            ua = UserAgent()
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = ua.chrome
            self.session.headers.update(headers)
        except Exception:
            # 如果UserAgent失败，使用默认的
            headers = IMDBConfig.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            self.session.headers.update(headers)
        
        # 启用连接池和Keep-Alive
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=2
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    @retry(stop_max_attempt_number=IMDBConfig.MAX_RETRY_TIMES, wait_fixed=IMDBConfig.RETRY_DELAY)
    def get_page(self, url, use_selenium=None):
        """获取网页内容 - 智能选择请求方式"""
        # 智能判断是否需要使用Selenium
        if use_selenium is None:
            use_selenium = self._should_use_selenium(url)
        
        try:
            if use_selenium:
                return self._get_with_selenium(url)
            else:
                return self._get_with_requests(url)
        except Exception as e:
            self.logger.warning(f"请求失败，正在重试: {url}, 错误: {e}")
            # 如果第一种方式失败，尝试另一种
            if use_selenium:
                try:
                    self.logger.info("Selenium失败，尝试使用requests")
                    return self._get_with_requests(url)
                except Exception as requests_error:
                    self.logger.warning(f"requests也失败: {requests_error}")
            else:
                try:
                    self.logger.info("requests失败，尝试使用Selenium")
                    return self._get_with_selenium(url)
                except Exception as selenium_error:
                    self.logger.warning(f"Selenium也失败: {selenium_error}")
            
            self._random_delay()
            raise e
    
    def _should_use_selenium(self, url):
        """智能判断是否需要使用Selenium"""
        # 对于列表页面，优先使用requests（速度快10倍）
        if any(keyword in url for keyword in ['chart', 'top', 'list', 'search']):
            return False
        # 对于详情页面，只在必要时使用Selenium
        elif '/title/' in url:
            # 先尝试requests，失败再用Selenium
            return False  # 改为优先尝试requests
        # 默认使用requests
        else:
            return False
    
    def _get_with_requests(self, url):
        """使用requests获取页面"""
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response
    
    def _get_with_selenium(self, url):
        """使用Selenium获取页面（优化版本）"""
        if not self.driver:
            self._init_chrome_driver()
        
        self.driver.get(url)
        
        # 智能等待页面加载完成
        self._wait_for_page_load()
        
        # 只在第一次访问时检查cookies
        if not hasattr(self, '_cookies_accepted'):
            self._handle_cookies()
            self._cookies_accepted = True
        
        # 创建伪response对象
        class SeleniumResponse:
            def __init__(self, driver):
                self.content = driver.page_source.encode('utf-8')
                self.text = driver.page_source
                self.status_code = 200
                self.url = driver.current_url
        
        return SeleniumResponse(self.driver)
    
    def _wait_for_page_load(self):
        """智能等待页面加载 - 优化版本"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        try:
            # 快速检查页面状态
            WebDriverWait(self.driver, 5).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 非常短的等待时间
            time.sleep(0.5)
        except Exception:
            # 如果智能等待失败，使用最小等待时间
            time.sleep(1)
    
    def _handle_cookies(self):
        """处理Cookie同意弹窗"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # 等待并点击同意按钮
            accept_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='accept-button']"))
            )
            accept_button.click()
            time.sleep(1)
            self.logger.info("已接受IMDB cookies")
        except Exception:
            # 如果没有找到同意按钮或已经同意过，继续
            pass
    
    def _init_chrome_driver(self):
        """初始化Chrome浏览器驱动（优化版本）"""
        if self._driver_ready:
            return
            
        try:
            chrome_options = Options()
            
            # 添加配置选项
            for option in IMDBConfig.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 禁用自动化检测
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 使用webdriver-manager自动管理驱动
            service = Service(ChromeDriverManager().install())
            service.start_error_message = "Chrome driver failed to start"
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 优化超时设置 - 更激进的设置
            self.driver.set_page_load_timeout(10)  # 进一步减少超时
            self.driver.implicitly_wait(2)         # 进一步减少等待
            
            # 执行脚本隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 快速预热浏览器 - 跳过复杂的预热
            # self._warmup_browser()  # 暂时禁用预热以提升速度
            
            self._driver_ready = True
            self.logger.info("IMDB Chrome驱动快速初始化成功")
            
        except Exception as e:
            self.logger.error(f"IMDB Chrome驱动初始化失败: {e}")
            self.logger.info("尝试使用requests作为备用方案")
            self.driver = None
            self._driver_ready = False
            raise e
    
    def _warmup_browser(self):
        """预热浏览器，处理初始化设置"""
        try:
            self.driver.get(f"{IMDBConfig.BASE_URL}")
            time.sleep(1)
            self._handle_cookies()
            self.logger.info("浏览器预热完成")
        except Exception as e:
            self.logger.warning(f"浏览器预热失败，但将继续: {e}")
    
    def _random_delay(self):
        """随机延时"""
        delay = random.uniform(IMDBConfig.DELAY_MIN, IMDBConfig.DELAY_MAX)
        time.sleep(delay)
    
    def close(self):
        """关闭连接 - 修复版本"""
        if self.driver:
            try:
                # 优雅关闭浏览器
                self.driver.delete_all_cookies()  # 清理cookies
                self.driver.quit()
                self.driver = None  # 重要：清空引用
                self.logger.info("Chrome驱动已正常关闭")
            except Exception as e:
                # 强制关闭
                try:
                    if hasattr(self.driver, 'service') and self.driver.service:
                        self.driver.service.stop()
                    self.driver = None
                    self.logger.warning(f"Chrome驱动强制关闭: {e}")
                except:
                    self.logger.error(f"Chrome驱动关闭失败: {e}")
        
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                self.logger.warning(f"关闭session时出错: {e}")
        
        self._driver_ready = False
    
    def __del__(self):
        """析构函数"""
        self.close()
