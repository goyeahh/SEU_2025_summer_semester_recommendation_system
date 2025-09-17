import pandas as pd
import torch
from .models import Movie
from .recommender_bert import MovieRecommenderBERT
from .recommender_personalize import MovieRecommender as PersonalizeRecommender

def initialize_recommender():
    print("正在初始化BERT推荐系统...")
    
    csv_path = "merged_movie_database.csv"  # <-- 直接使用您的CSV文件
    cache_path = "movie_embeddings.pt"      # <-- 直接使用您的.pt文件

    try:
        # 1. 加载您的CSV数据
        movies_df = pd.read_csv(csv_path)
        # 2. 加载您预先计算好的向量
        embeddings = torch.load(cache_path)
        print("成功加载CSV数据和电影向量缓存。")
    except FileNotFoundError as e:
        print(f"错误：无法找到必要的文件 - {e}")
        print("请确保 'merged_movie_database.csv' 和 'movie_embeddings.pt' 文件位于项目根目录。")
        return None

    # 3. 创建推荐器实例 (这个过程只在服务器启动时执行一次)
    recommender = MovieRecommenderBERT(movies_df, embeddings)
    print("BERT推荐系统初始化完成。")
    return recommender

def initialize_personalize_recommender():
    print("正在初始化个性化推荐系统 (TF-IDF)...")
    
    # 1. 从数据库加载所有电影数据
    movies_qs = Movie.objects.prefetch_related('genres').all()
    
    # 2. 将 QuerySet 转换为 Pandas DataFrame
    #    确保列名与 recommender_personalize.py 中使用的完全一致
    movie_list = []
    for movie in movies_qs:
        genres_list = [genre.name for genre in movie.genres.all()]
        movie_list.append({
            'id': movie.id,
            'name': movie.name,
            'genres': ", ".join(genres_list), # 注意这里的列名叫 'genres'
            'year': movie.year,
            'countries': movie.countries,
            'director': movie.director,
            'actors': movie.actors,
            'description': movie.description,
            'star_5': movie.star_5,
            'star_4': movie.star_4,
            'star_3': movie.star_3,
            'star_2': movie.star_2,
            'star_1': movie.star_1,
            'rating': float(movie.rating),
        })
    movies_df = pd.DataFrame(movie_list)

    if movies_df.empty:
        print("数据库中没有电影数据，无法初始化个性化推荐器。")
        return None

    # 3. 创建个性化推荐器实例
    recommender = PersonalizeRecommender(movies_df)
    print("个性化推荐系统初始化完成。")
    return recommender

# 创建两个全局变量，分别持有两个推荐器实例
bert_recommender = initialize_recommender()
personalize_recommender = initialize_personalize_recommender()