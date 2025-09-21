import pandas as pd
import numpy as np
from collections import defaultdict
import math
import csv
import re


def load_data():
    """加载豆瓣和IMDB数据"""
    # 使用更灵活的方式读取CSV文件，处理字段数量不一致的问题
    try:
        douban_df = pd.read_csv('douban_database_20250913_223944.csv', on_bad_lines='warn', engine='python')
    except:
        # 如果标准方法失败，尝试手动解析
        douban_rows = []
        with open('douban_database_20250913_223944.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # 读取标题行
            for i, row in enumerate(reader):
                if len(row) > len(headers):
                    # 如果字段太多，可能是由于逗号问题，尝试合并多余的字段
                    row = row[:len(headers) - 1] + [','.join(row[len(headers) - 1:])]
                elif len(row) < len(headers):
                    # 如果字段太少，填充空值
                    row = row + [''] * (len(headers) - len(row))
                douban_rows.append(row)
        douban_df = pd.DataFrame(douban_rows, columns=headers)

    try:
        imdb_df = pd.read_csv('imdb_database_20250913_015658.csv', on_bad_lines='warn', engine='python')
    except:
        # 如果标准方法失败，尝试手动解析
        imdb_rows = []
        with open('imdb_database_20250913_015658.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)  # 读取标题行
            for i, row in enumerate(reader):
                if len(row) > len(headers):
                    # 如果字段太多，可能是由于逗号问题，尝试合并多余的字段
                    row = row[:len(headers) - 1] + [','.join(row[len(headers) - 1:])]
                elif len(row) < len(headers):
                    # 如果字段太少，填充空值
                    row = row + [''] * (len(headers) - len(row))
                imdb_rows.append(row)
        imdb_df = pd.DataFrame(imdb_rows, columns=headers)

    return douban_df, imdb_df


def preprocess_data(douban_df, imdb_df):
    """数据预处理"""
    # 确保年份是整数类型
    douban_df['year'] = pd.to_numeric(douban_df['year'], errors='coerce').fillna(0).astype(int)
    imdb_df['year'] = pd.to_numeric(imdb_df['year'], errors='coerce').fillna(0).astype(int)

    # 处理可能的NaN值
    douban_df = douban_df.fillna('')
    imdb_df = imdb_df.fillna('')

    return douban_df, imdb_df


def convert_imdb_ratings(imdb_row):
    """将IMDB的10级评分转换为5级评分"""
    # 确保评分值是数字类型
    rating_10 = float(imdb_row['rating_10']) if imdb_row['rating_10'] != '' and pd.notna(imdb_row['rating_10']) else 0
    rating_9 = float(imdb_row['rating_9']) if imdb_row['rating_9'] != '' and pd.notna(imdb_row['rating_9']) else 0
    rating_8 = float(imdb_row['rating_8']) if imdb_row['rating_8'] != '' and pd.notna(imdb_row['rating_8']) else 0
    rating_7 = float(imdb_row['rating_7']) if imdb_row['rating_7'] != '' and pd.notna(imdb_row['rating_7']) else 0
    rating_6 = float(imdb_row['rating_6']) if imdb_row['rating_6'] != '' and pd.notna(imdb_row['rating_6']) else 0
    rating_5 = float(imdb_row['rating_5']) if imdb_row['rating_5'] != '' and pd.notna(imdb_row['rating_5']) else 0
    rating_4 = float(imdb_row['rating_4']) if imdb_row['rating_4'] != '' and pd.notna(imdb_row['rating_4']) else 0
    rating_3 = float(imdb_row['rating_3']) if imdb_row['rating_3'] != '' and pd.notna(imdb_row['rating_3']) else 0
    rating_2 = float(imdb_row['rating_2']) if imdb_row['rating_2'] != '' and pd.notna(imdb_row['rating_2']) else 0
    rating_1 = float(imdb_row['rating_1']) if imdb_row['rating_1'] != '' and pd.notna(imdb_row['rating_1']) else 0

    return {
        'star_5': rating_10 + rating_9,
        'star_4': rating_8 + rating_7,
        'star_3': rating_6 + rating_5,
        'star_2': rating_4 + rating_3,
        'star_1': rating_2 + rating_1
    }


def get_douban_ratings(douban_row):
    """从豆瓣行获取评分"""
    return {
        'star_5': float(douban_row['star_5']) if douban_row['star_5'] != '' and pd.notna(douban_row['star_5']) else 0,
        'star_4': float(douban_row['star_4']) if douban_row['star_4'] != '' and pd.notna(douban_row['star_4']) else 0,
        'star_3': float(douban_row['star_3']) if douban_row['star_3'] != '' and pd.notna(douban_row['star_3']) else 0,
        'star_2': float(douban_row['star_2']) if douban_row['star_2'] != '' and pd.notna(douban_row['star_2']) else 0,
        'star_1': float(douban_row['star_1']) if douban_row['star_1'] != '' and pd.notna(douban_row['star_1']) else 0
    }


def average_ratings(douban_ratings, imdb_ratings):
    """计算两个平台评分的平均值"""
    return {
        'star_5': (douban_ratings['star_5'] + imdb_ratings['star_5']) / 2,
        'star_4': (douban_ratings['star_4'] + imdb_ratings['star_4']) / 2,
        'star_3': (douban_ratings['star_3'] + imdb_ratings['star_3']) / 2,
        'star_2': (douban_ratings['star_2'] + imdb_ratings['star_2']) / 2,
        'star_1': (douban_ratings['star_1'] + imdb_ratings['star_1']) / 2
    }


def probabilistic_graphical_model(ratings_list):
    """
    使用概率图模型计算处理后的评分
    简化实现：使用加权平均，权重基于评分分布
    """
    if not ratings_list:
        return 0

    # 计算每个评分的可信度权重（基于评分数量）
    weights = [1 + math.log(1 + sum(rating.values())) for rating in ratings_list]
    total_weight = sum(weights)

    # 计算加权平均评分
    weighted_sum = 0
    for i, rating in enumerate(ratings_list):
        # 计算该评分集的平均星级
        total_stars = sum(k * rating[f'star_{k}'] for k in range(1, 6))
        total_votes = sum(rating.values())
        avg_rating = total_stars / total_votes if total_votes > 0 else 0

        weighted_sum += avg_rating * weights[i]

    return weighted_sum / total_weight if total_weight > 0 else 0


def standardize_genres(genres_str):
    """将电影类型标准化为指定的几个主要类型"""
    if not genres_str or pd.isna(genres_str):
        return ""

    # 定义目标类型
    target_genres = ['喜剧', '爱情', '动作', '恐怖', '悬疑', '家庭', '科幻', '青春']

    # 定义类型映射（英文到中文）
    genre_mapping = {
        'comedy': '喜剧',
        'romance': '爱情',
        'action': '动作',
        'horror': '恐怖',
        'mystery': '悬疑',
        'family': '家庭',
        'sci-fi': '科幻',
        'science fiction': '科幻',
        'fantasy': '科幻',  # 将奇幻映射到科幻
        'teen': '青春',
        'youth': '青春',
        'drama': '青春',  # 将剧情映射到青春
        'adventure': '动作',  # 将冒险映射到动作
        'thriller': '悬疑',  # 将惊悚映射到悬疑
        'animation': '家庭',  # 将动画映射到家庭
        'crime': '动作',  # 将犯罪映射到动作
        'war': '动作',  # 将战争映射到动作
    }

    # 将输入的类型字符串转换为小写并分割
    if isinstance(genres_str, str):
        genres_list = [g.strip().lower() for g in genres_str.split(',')]
    else:
        genres_list = []

    # 映射到目标类型
    standardized_genres = set()
    for genre in genres_list:
        # 首先检查是否直接匹配目标类型
        if genre in target_genres:
            standardized_genres.add(genre)
        # 然后检查映射表
        elif genre in genre_mapping:
            standardized_genres.add(genre_mapping[genre])
        # 最后检查中文类型是否包含目标关键词
        else:
            for target in target_genres:
                if target in genre:
                    standardized_genres.add(target)

    # 如果没有匹配到任何类型，保留原始类型（前两个）
    if not standardized_genres and genres_list:
        standardized_genres = set(genres_list[:2])

    return ','.join(sorted(standardized_genres))


def merge_datasets(douban_df, imdb_df):
    """合并两个数据集，仅使用电影名称(name)匹配相同电影"""
    # 创建电影字典，仅以name为键
    movies_dict = {}

    # 首先处理豆瓣数据
    for _, row in douban_df.iterrows():
        key = str(row['name']).strip().lower()  # 使用小写和去除空格进行标准化
        standardized_genres = standardize_genres(row['genres'])
        movies_dict[key] = {
            'source': 'douban',
            'name': row['name'],
            'year': row['year'],
            'countries': row['countries'],
            'directors': row['directors'],
            'actors': row['actors'],
            'duration_minutes': row['duration_minutes'],
            'plot': row['plot'],
            'genres': standardized_genres,
            'ratings': get_douban_ratings(row),
            'processed_rating': float(row['processed_rating']) if row['processed_rating'] != '' and pd.notna(
                row['processed_rating']) else 0,
            'poster_path': row['poster_path']
        }

    # 然后处理IMDB数据，合并重复项
    for _, row in imdb_df.iterrows():
        key = str(row['name']).strip().lower()  # 使用小写和去除空格进行标准化
        imdb_ratings = convert_imdb_ratings(row)
        standardized_genres = standardize_genres(row['genres'])

        if key in movies_dict:
            # 合并两个平台的评分
            douban_ratings = movies_dict[key]['ratings']
            merged_ratings = average_ratings(douban_ratings, imdb_ratings)

            # 更新记录，保留豆瓣的年份和其他信息
            movies_dict[key]['ratings'] = merged_ratings
            movies_dict[key]['source'] = 'both'
            # 如果豆瓣没有类型但IMDB有，使用IMDB的类型
            if not movies_dict[key]['genres'] and standardized_genres:
                movies_dict[key]['genres'] = standardized_genres
        else:
            # 添加新记录
            movies_dict[key] = {
                'source': 'imdb',
                'name': row['name'],
                'year': row['year'],
                'countries': row['countries'],
                'directors': row['directors'],
                'actors': row['actors'],
                'duration_minutes': row['duration_minutes'],
                'plot': row['plot'],
                'genres': standardized_genres,
                'ratings': imdb_ratings,
                'processed_rating': float(row['processed_rating']) if row['processed_rating'] != '' and pd.notna(
                    row['processed_rating']) else 0,
                'poster_path': row['poster_path']
            }

    return movies_dict


def calculate_processed_ratings(movies_dict):
    """使用概率图模型计算处理后的评分"""
    # 收集所有评分数据
    all_ratings = []
    for movie in movies_dict.values():
        all_ratings.append(movie['ratings'])

    # 计算全局处理后的评分
    global_processed_rating = probabilistic_graphical_model(all_ratings)

    # 为每个电影分配处理后的评分
    for key in movies_dict:
        movie = movies_dict[key]
        individual_ratings = [movie['ratings']]
        individual_processed_rating = probabilistic_graphical_model(individual_ratings)

        # 结合全局和个体评分
        movie['processed_rating'] = (global_processed_rating + individual_processed_rating) / 2

    return movies_dict


def create_final_dataframe(movies_dict):
    """创建最终的数据框"""
    rows = []
    for i, (key, movie) in enumerate(movies_dict.items()):
        row = {
            'id': i + 1,
            'name': movie['name'],
            'genres': movie['genres'],
            'year': movie['year'],
            'countries': movie['countries'],
            'directors': movie['directors'],
            'actors': movie['actors'],
            'duration_minutes': movie['duration_minutes'],
            'plot': movie['plot'],
            'star_5': movie['ratings']['star_5'],
            'star_4': movie['ratings']['star_4'],
            'star_3': movie['ratings']['star_3'],
            'star_2': movie['ratings']['star_2'],
            'star_1': movie['ratings']['star_1'],
            'processed_rating': movie['processed_rating'],
            'poster_path': movie['poster_path'],
            'source': movie['source']
        }
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    """主函数"""
    print("开始处理电影数据...")

    # 加载数据
    douban_df, imdb_df = load_data()

    # 数据预处理
    douban_df, imdb_df = preprocess_data(douban_df, imdb_df)

    # 合并数据集
    movies_dict = merge_datasets(douban_df, imdb_df)

    # 计算处理后的评分
    movies_dict = calculate_processed_ratings(movies_dict)

    # 创建最终数据框
    final_df = create_final_dataframe(movies_dict)

    # 保存结果
    final_df.to_csv('merged_movie_database.csv', index=False)
    print("数据合并完成，结果已保存到 merged_movie_database.csv")

    # 显示前几行数据
    print("\n前5行数据预览:")
    print(final_df.head())

    # 显示类型分布统计
    print("\n类型分布统计:")
    all_genres = []
    for genres in final_df['genres']:
        if genres:
            all_genres.extend([g.strip() for g in genres.split(',')])

    from collections import Counter
    genre_counts = Counter(all_genres)
    for genre, count in genre_counts.most_common():
        print(f"{genre}: {count}")

    return final_df


if __name__ == "__main__":
    final_data = main()