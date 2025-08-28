#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
烂番茄网络请求模块
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
from .config import RTConfig


class RTNetwork:
    """烂番茄网络请求处理类"""
    
    def __init__(self, config=None):
        """
        初始化网络请求处理器
        
        Args:
            config: 配置对象，默认使用RTConfig
        """
        self.config = config or RTConfig()
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
            'Referer': 'https://www.rottentomatoes.com/',
            'Origin': 'https://www.rottentomatoes.com'
        })
    
    def get_page(self, url, use_selenium=True, wait_element=None, timeout=15):
        """
        获取网页内容（烂番茄需要JavaScript渲染，使用Selenium）
        
        Args:
            url: 目标URL
            use_selenium: 是否使用Selenium（推荐为True）
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
            except WebDriverException as e:
                self.logger.warning(f"WebDriver异常 (第 {attempt + 1} 次): {e}")
                # WebDriver连接问题，尝试重启
                self._restart_driver()
                if attempt < self.config.RETRY_TIMES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次请求失败: {url}, 错误: {e}")
                if attempt < self.config.RETRY_TIMES - 1:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                else:
                    self.logger.error(f"请求失败，已重试 {self.config.RETRY_TIMES} 次: {url}")
                    return None
    
    def _restart_driver(self):
        """重启WebDriver"""
        try:
            self.logger.info("尝试重启WebDriver...")
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            # 等待一段时间再重启
            time.sleep(3)
            self._init_driver()
            
        except Exception as e:
            self.logger.error(f"重启WebDriver失败: {e}")
            self.driver = None
    
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
        
        response = self.session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.text
    
    def _get_page_selenium(self, url, wait_element=None, timeout=15):
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
        
        # 等待页面加载完成 - 优化等待策略
        if wait_element:
            try:
                wait = WebDriverWait(self.driver, min(timeout, 10))  # 限制最大等待时间
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_element)))
            except TimeoutException:
                self.logger.warning(f"等待元素超时: {wait_element}")
        else:
            # 快速检查常见元素
            common_selectors = [
                '[data-qa="discovery-media-list"]',  # 电影列表
                'tile-link',                         # 电影链接
                '.movie_info',                       # 电影信息
                '[data-qa="score-panel"]'           # 评分面板
            ]
            
            for selector in common_selectors:
                try:
                    wait = WebDriverWait(self.driver, 3)  # 减少单个元素等待时间
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
        
        # 快速滚动页面以加载动态内容
        self._fast_scroll()
        
        # 减少额外等待时间
        time.sleep(1)
        
        return self.driver.page_source
    
    def _init_driver(self):
        """初始化Chrome WebDriver"""
        try:
            chrome_options = Options()
            for option in self.config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # 针对烂番茄的特殊配置
            prefs = {
                "profile.managed_default_content_settings.images": 2,  # 禁用图片加载
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.media_stream_mic": 2,
                "profile.default_content_setting_values.media_stream_camera": 2,
                "profile.default_content_setting_values.geolocation": 2,
                "profile.default_content_setting_values.desktop_notification": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 添加更多反检测措施
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            service = Service(ChromeDriverManager().install())
            
            # 添加服务参数
            service.creation_flags = 0x08000000  # CREATE_NO_WINDOW flag
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置页面加载超时 - 减少等待时间
            self.driver.set_page_load_timeout(15)  # 从30秒减少到15秒
            self.driver.implicitly_wait(5)          # 从10秒减少到5秒
            
            # 执行脚本隐藏webdriver属性
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            self.logger.info("Chrome WebDriver 初始化成功")
            
        except Exception as e:
            self.logger.error(f"Chrome WebDriver 初始化失败: {e}")
            raise
    
    def _fast_scroll(self):
        """快速滚动页面，适用于大多数情况"""
        if not self.driver:
            return
        
        try:
            # 快速滚动到页面底部，然后回到顶部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)  # 简短等待
            
            # 滚动到页面中间
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.5)
            
            # 回到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.3)
                
        except Exception as e:
            self.logger.warning(f"快速滚动失败: {e}")
    
    def _progressive_scroll(self):
        """渐进式滚动页面，模拟真实用户浏览"""
        if not self.driver:
            return
        
        try:
            # 获取页面高度
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 快速分段滚动 - 优化性能
            scroll_pause_time = random.uniform(0.5, 1)  # 减少等待时间
            scroll_steps = 3  # 减少滚动步骤
            
            for i in range(scroll_steps):
                # 计算滚动位置
                scroll_position = (last_height * (i + 1)) // scroll_steps
                
                # 滚动到指定位置
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                
                # 等待内容加载
                time.sleep(scroll_pause_time)
                
                # 检查是否有新内容加载
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height
            
            # 滚动到页面顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)  # 减少等待时间
                
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
                'Referer': 'https://www.rottentomatoes.com/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            })
            
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"成功下载图片: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"图片下载失败 {url}: {e}")
            return False
    
    def handle_cloudflare_challenge(self):
        """处理Cloudflare挑战页面"""
        if not self.driver:
            return False
        
        try:
            # 检查是否遇到Cloudflare挑战
            page_source = self.driver.page_source.lower()
            
            if 'cloudflare' in page_source or 'checking your browser' in page_source:
                self.logger.info("检测到Cloudflare挑战，等待处理...")
                
                # 等待挑战完成（最多30秒）
                for _ in range(30):
                    time.sleep(1)
                    current_source = self.driver.page_source.lower()
                    
                    if 'cloudflare' not in current_source and 'checking your browser' not in current_source:
                        self.logger.info("Cloudflare挑战已通过")
                        return True
                
                self.logger.warning("Cloudflare挑战处理超时")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理Cloudflare挑战时出错: {e}")
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
