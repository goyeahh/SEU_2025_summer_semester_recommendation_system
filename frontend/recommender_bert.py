import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity

class MovieRecommenderBERT:
    # __init__ 现在接收一个 DataFrame 和一个 embeddings 张量
    def __init__(self, movies_df, embeddings):
        self.movies = movies_df
        self.embeddings = embeddings

    # 这个函数就是您想要的“传ID，返回ID列表”的核心
    def get_similar_movie_ids(self, movie_id, num_recommendations=5):
        # 使用 'id' 列进行匹配
        movie_row = self.movies[self.movies["id"] == movie_id]
        if movie_row.empty:
            return []

        # 使用 .index 获取行号
        try:
            idx = self.movies.index[self.movies['id'] == movie_id].tolist()[0]
        except IndexError:
            return []
            
        query_emb = self.embeddings[idx].unsqueeze(0)
        sims = cosine_similarity(query_emb, self.embeddings)[0]
        
        # 排除自身，然后取Top-N
        sims[idx] = -1 
        top_indices = sims.argsort()[::-1][:num_recommendations]
        
        # 返回推荐电影的 ID 列表
        recommended_ids = self.movies.iloc[top_indices]['id'].tolist()
        return recommended_ids