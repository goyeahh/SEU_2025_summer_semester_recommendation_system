# 豆瓣电影爬虫系统使用指南

## 📋 项目概述

这是一个为**大数据真值推荐系统**项目开发的模块化豆瓣电影爬虫系统。该系统负责从豆瓣官网采集电影数据，为后续的推荐算法和真值算法提供数据支持。

## 🏗️ 项目结构

```
recommendation_system/
├── douban_crawler/          # 爬虫模块包
│   ├── __init__.py         # 包初始化文件
│   ├── config.py           # 配置管理模块
│   ├── crawler.py          # 主爬虫类
│   ├── network.py          # 网络请求模块
│   ├── parser.py           # 页面解析模块
│   └── data_processor.py   # 数据处理模块
├── run_crawler.py          # 主程序入口
├── requirements.txt        # 依赖包列表
└── README.md              # 本文件
```

## 🚀 快速开始

### 1. 环境准备

确保您已经激活了虚拟环境 `Recommendation_System`：

```bash
# Windows
conda activate Recommendation_System

# 或使用venv
# source Recommendation_System/Scripts/activate  (Windows)
# source Recommendation_System/bin/activate      (Linux/Mac)
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python run_crawler.py
```

## 📖 使用方法

### 简单使用（推荐新手）

运行 `run_crawler.py` 后选择"简单爬取"模式，系统将自动爬取 50 部热门电影数据。

### 批量爬取

选择"批量爬取"模式，系统将依次爬取：

- 热门电影 (80 部)
- 新片推荐 (30 部)
- 经典电影 (40 部)

### 编程接口使用

```python
from douban_crawler import DoubanMovieCrawler

# 创建爬虫实例
with DoubanMovieCrawler() as crawler:
    # 爬取数据
    raw_data, cleaned_data, saved_files = crawler.crawl_movies(
        categories=['hot', 'new_movies'],  # 爬取分类
        max_movies=100,                    # 最大数量
        max_pages=10                       # 最大页数
    )

    print(f"获得 {len(cleaned_data)} 部电影数据")
```

## 📊 输出数据格式

### 数据文件

爬虫会生成以下格式的数据文件：

1. **JSON 格式** (`cleaned_movies_YYYYMMDD_HHMMSS.json`)
2. **Excel 格式** (`cleaned_movies_YYYYMMDD_HHMMSS.xlsx`)
3. **CSV 格式** (`cleaned_movies_YYYYMMDD_HHMMSS.csv`)
4. **神经网络特征** (`neural_features_YYYYMMDD_HHMMSS.npy`)
5. **特征信息** (`feature_info_YYYYMMDD_HHMMSS.json`)

### 数据字段说明

每部电影包含以下主要字段：

```json
{
  "douban_id": "电影豆瓣ID",
  "title": "电影标题",
  "year": "上映年份",
  "rating": "豆瓣评分",
  "rating_count": "评分人数",
  "directors": ["导演列表"],
  "actors": ["主演列表"],
  "genres": ["类型列表"],
  "countries": ["制片国家"],
  "runtime_minutes": "时长(分钟)",
  "summary": "剧情简介",
  "tags": ["标签列表"],
  "star_5": "5星评分百分比",
  "star_4": "4星评分百分比",
  "star_3": "3星评分百分比",
  "star_2": "2星评分百分比",
  "star_1": "1星评分百分比"
}
```

## 🤖 为神经网络准备的特征

系统自动为推荐算法生成以下特征：

### 数值特征

- `rating_normalized`: 归一化评分 (0-1)
- `rating_count_log`: 评分人数对数
- `runtime_normalized`: 归一化时长
- `rating_variance`: 评分方差（评分分歧度）

### 类别特征

- 电影类型 one-hot 编码
- 地区特征 (中国片、美国片、欧洲片)
- 年代特征 (近期片、经典片)

### 评分分布特征

- 5 星到 1 星的评分分布比例

## 🔧 配置选项

可以通过修改 `douban_crawler/config.py` 来调整爬虫参数：

```python
class Config:
    MAX_MOVIES = 100        # 最大爬取数量
    DELAY_MIN = 1          # 最小延时(秒)
    DELAY_MAX = 3          # 最大延时(秒)
    OUTPUT_DIR = "data"    # 输出目录
    # ... 更多配置选项
```

## 👥 团队协作

### 数据交接接口

为方便与其他模块协作，建议使用以下标准接口：

```python
# 推荐算法团队使用
import numpy as np
import json

# 加载神经网络特征
features = np.load('data/neural_features_YYYYMMDD_HHMMSS.npy')

# 加载特征信息
with open('data/feature_info_YYYYMMDD_HHMMSS.json', 'r') as f:
    feature_info = json.load(f)

print(f"特征维度: {feature_info['feature_dim']}")
print(f"样本数量: {feature_info['sample_count']}")
```

### Git 协作建议

```bash
# 只提交代码，不提交数据文件
git add *.py *.md *.txt
git add douban_crawler/

# 数据文件添加到 .gitignore
echo "data/" >> .gitignore
echo "*.log" >> .gitignore
```

## ⚠️ 注意事项

1. **遵守 robots.txt**: 本爬虫设置了合理的延时，请勿修改为过于频繁的请求
2. **数据使用**: 爬取的数据仅供学习和研究使用，请遵守豆瓣的使用条款
3. **网络环境**: 建议在稳定的网络环境下运行，避免频繁的网络中断
4. **Chrome 浏览器**: 系统会自动下载 ChromeDriver，请确保 Chrome 浏览器已安装

## 🐛 常见问题

### Q: 爬虫运行很慢怎么办？

A: 这是正常现象，为了遵守网站规则，设置了 1-3 秒的随机延时。可以在配置中适当调整，但不建议设置过小。

### Q: 出现"Chrome 驱动初始化失败"怎么办？

A: 请确保已安装 Chrome 浏览器，系统会自动下载对应的 ChromeDriver。

### Q: 数据质量如何保证？

A: 系统包含完整的数据清洗模块，会自动过滤无效数据并进行标准化处理。

### Q: 如何与推荐算法模块对接？

A: 使用生成的 `.npy` 特征文件和 `feature_info.json` 文件，包含了为神经网络优化的特征向量。

## 📞 技术支持

如有问题，请联系爬虫模块负责人或在项目群中讨论。

---

**版本**: v1.0.0  
**更新日期**: 2025-08-27  
**适用项目**: 大数据真值推荐系统
