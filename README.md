# 大数据真值推荐系统 - 爬虫模块使用指南

## 项目概述

本项目是大数据真值推荐系统的爬虫模块，专门用于从豆瓣和 IMDB 两个权威电影网站爬取电影数据，为后续的推荐算法和真值算法提供可靠的数据基础。

## 功能特性

### 支持平台

- **豆瓣电影**: 获取中文电影信息、评分、评论等
- **IMDB**: 获取国际电影信息、评分、详细信息等

### 主要功能

1. **多平台数据爬取**: 同时支持豆瓣和 IMDB 数据获取
2. **分类爬取**: 支持按电影分类进行定向爬取
3. **数据清洗**: 自动清洗和标准化爬取数据
4. **多格式输出**: 支持 JSON、CSV 格式数据保存
5. **反爬虫机制**: 内置延时、随机用户代理等反爬虫措施
6. **错误恢复**: 具备重试机制和错误处理能力

## 环境要求

### Python 版本

- Python 3.8+

### 依赖包

```bash
pip install -r requirements.txt
```

### 浏览器要求

- 需要安装 Chrome 浏览器
- 自动下载和管理 ChromeDriver

## 快速开始

### 1. 安装依赖

```bash
# 确保在虚拟环境Recommendation_System中
pip install -r requirements.txt
```

### 2. 测试连接

```bash
python main.py --test-connection
```

### 3. 查看支持的分类

```bash
python main.py --list-categories
```

### 4. 开始爬取

#### 爬取所有平台（推荐）

```bash
# 爬取所有平台，每个平台100部电影
"D:\Anaconda_envs\envs\Recommendation_System\python.exe" main.py --platform all --max-movies 100

# 指定分类爬取
python main.py --platform all --categories hot top250 --max-movies 50
```

#### 只爬取豆瓣

```bash
# 爬取豆瓣热门和Top250
python main.py --platform douban --categories hot top250 --max-movies 100
```

#### 只爬取 IMDB

```bash
# 爬取IMDB Top250和热门
python main.py --platform imdb --categories top250 popular --max-movies 100
```

## 支持的电影分类

### 豆瓣电影分类

- `hot`: 豆瓣电影热门榜
- `top250`: 豆瓣电影 Top250
- `new_movies`: 新片榜
- `weekly_best`: 一周口碑榜
- `north_america`: 北美票房榜
- `classic`: 经典电影
- `comedy`: 喜剧片
- `action`: 动作片
- `romance`: 爱情片
- `sci_fi`: 科幻片

### IMDB 分类

- `top250`: IMDB Top 250
- `popular`: 最受欢迎电影
- `upcoming`: 即将上映
- `in_theaters`: 正在上映
- `most_popular_movies`: 最受欢迎电影（更多页面）
- `top_rated_movies`: 评分最高电影
- `lowest_rated_movies`: 评分最低电影

## 输出数据格式

### 数据字段说明

#### 豆瓣电影数据字段

```json
{
  "platform": "豆瓣",
  "douban_id": "电影ID",
  "url": "电影页面URL",
  "title": "电影标题",
  "original_title": "原始标题",
  "year": "上映年份",
  "rating": "评分",
  "rating_count": "评分人数",
  "genres": ["类型列表"],
  "directors": ["导演列表"],
  "actors": ["主演列表"],
  "duration": "时长(分钟)",
  "countries": ["制片国家"],
  "languages": ["语言"],
  "plot": "剧情简介",
  "poster_url": "海报链接",
  "crawl_time": "爬取时间"
}
```

#### IMDB 电影数据字段

```json
{
  "platform": "IMDB",
  "imdb_id": "IMDB ID",
  "url": "电影页面URL",
  "title": "电影标题",
  "original_title": "原始标题",
  "year": "上映年份",
  "rating": "评分",
  "rating_count": "评分人数",
  "genres": ["类型列表"],
  "directors": ["导演列表"],
  "actors": ["主演列表"],
  "duration": "时长(分钟)",
  "countries": ["制片国家"],
  "languages": ["语言"],
  "plot": "剧情简介",
  "poster_url": "海报链接",
  "release_date": "上映日期",
  "budget": "预算",
  "box_office": "票房",
  "awards": ["获奖信息"],
  "crawl_time": "爬取时间"
}
```

## 高级用法

### 1. 数据合并

```bash
# 合并豆瓣和IMDB数据文件
python main.py --merge-data data/douban_movies_20250829_143022.json data/imdb_movies_20250829_144015.json
```

### 2. 自定义输出目录

```bash
python main.py --platform all --output-dir custom_data --max-movies 50
```

### 3. 程序化使用

```python
from run_multi_platform_crawler import MultiPlatformCrawler

# 创建爬虫实例
crawler = MultiPlatformCrawler(output_dir="my_data")

# 测试连接
connections = crawler.test_all_connections()
print(connections)

# 爬取数据
results = crawler.crawl_all_platforms(
    max_movies_per_platform=50,
    douban_categories=['hot', 'top250'],
    imdb_categories=['top250', 'popular']
)

print(f"总共爬取了 {results['summary']['total_movies']} 部电影")
```

## 配置说明

### 豆瓣爬虫配置

- 最小延时: 2 秒
- 最大延时: 5 秒
- 最大重试次数: 3 次
- 默认最大电影数: 200 部

### IMDB 爬虫配置

- 最小延时: 2 秒
- 最大延时: 5 秒
- 最大重试次数: 3 次
- 默认最大电影数: 200 部
- 使用 Selenium 进行 JavaScript 渲染

## 故障排除

### 常见问题

1. **连接失败**

   - 检查网络连接
   - 确认是否需要代理
   - 验证 Chrome 浏览器安装

2. **ChromeDriver 问题**

   - 程序会自动下载和管理 ChromeDriver
   - 如果失败，请手动更新 Chrome 浏览器

3. **数据获取不完整**

   - 适当增加延时时间
   - 减少并发请求
   - 检查网站是否更新了结构

4. **权限问题**
   - 确保有数据目录的写入权限
   - 检查日志文件写入权限

### 日志文件

- 豆瓣爬虫日志: `douban_crawler.log`
- IMDB 爬虫日志: `imdb_crawler.log`
- 多平台爬虫日志: `multi_platform_crawler.log`

## 数据质量保证

### 数据验证

- 自动验证必要字段完整性
- 评分范围检查
- 年份合理性验证
- URL 格式验证

### 数据清洗

- 去除 HTML 标签
- 标准化空白字符
- 类型字段标准化
- 重复数据检测

### 统计信息

每次爬取都会生成统计报告，包含：

- 爬取成功率
- 数据完整性分析
- 平台分布统计
- 年份和类型分布

## 注意事项

1. **合规使用**: 请遵守网站 robots.txt 和使用条款
2. **频率控制**: 内置延时机制，请勿过度频繁访问
3. **数据使用**: 爬取的数据仅用于学术研究和推荐系统开发
4. **版权声明**: 电影信息版权归原网站所有

## 更新日志

### v1.0.0 (2025-08-29)

- 初始版本发布
- 支持豆瓣和 IMDB 双平台爬取
- 完整的数据清洗和验证功能
- 多格式数据输出
- 命令行和程序化接口

## 技术支持

如有问题请检查：

1. 日志文件中的错误信息
2. 网络连接状态
3. 依赖包版本兼容性

## 贡献指南

欢迎提交问题和改进建议，请确保：

1. 详细描述问题或需求
2. 提供相关日志信息
3. 测试环境信息
