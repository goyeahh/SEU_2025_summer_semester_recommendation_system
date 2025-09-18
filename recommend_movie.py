import pandas as pd
import torch
import os
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity


# 拼接文本函数
def combine_text(row):
    name = row['name']
    genre = row['genres'] if pd.notnull(row['genres']) else "未知类型"
    director = row['directors'] if pd.notnull(row['directors']) else "未知导演"
    plot = row['plot'] if pd.notnull(row['plot']) else "暂无简介"
    return f"《{name}》是一部{genre}电影，由{director}执导，{plot}"


class MovieRecommenderBERT:
    def __init__(self, movies_df, cache_path="movie_embeddings.pt"):
        self.movies = movies_df.copy()
        self.movies["combined_text"] = self.movies.apply(combine_text, axis=1)

        # 加载多语言 BERT
        model_name = "bert-base-multilingual-cased"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.bert_model = AutoModel.from_pretrained(model_name)

        self.cache_path = cache_path

        # 预先编码或加载缓存
        if os.path.exists(cache_path):
            print("加载缓存的电影向量...")
            self.embeddings = torch.load(cache_path)
        else:
            print("首次运行，正在编码电影文本，请稍候...")
            self.embeddings = self._encode_all_movies()
            torch.save(self.embeddings, cache_path)
            print(f"编码完成，已缓存到 {cache_path}")

    def _encode_text(self, text):
        """对单段文本编码，返回 [1, hidden_size]"""
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, padding=True, max_length=128
        )
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1)  # 平均池化
        return emb

    def _encode_all_movies(self):
        """对所有电影文本做批量编码"""
        embeddings = []
        for txt in self.movies["combined_text"]:
            emb = self._encode_text(txt)
            embeddings.append(emb)
        return torch.cat(embeddings, dim=0)  # [num_movies, hidden_size]

    def get_similar_movies(self, movie_id, num_recommendations=5):
        """基于BERT文本相似度的电影推荐"""
        movie_row = self.movies[self.movies["id"] == movie_id]
        if movie_row.empty:
            print("未找到该电影")
            return pd.DataFrame()

        idx = movie_row.index[0]
        query_emb = self.embeddings[idx].unsqueeze(0)  # [1, hidden_size]

        # 计算余弦相似度
        sims = cosine_similarity(query_emb, self.embeddings)[0]

        # 取Top-N
        top_indices = sims.argsort()[::-1][1:num_recommendations + 1]  # 排除自身
        recommendations = self.movies.iloc[top_indices].copy()
        recommendations["similarity_score"] = sims[top_indices]

        return recommendations[["id", "name", "genres", "directors", "similarity_score"]]


# ===================== 使用示例 =====================
if __name__ == "__main__":
    # 假设你已经有 DataFrame，格式如题
    movies_df = pd.read_csv("merged_movie_database.csv")  # 替换成你的数据路径

    recommender = MovieRecommenderBERT(movies_df, cache_path="movie_embeddings.pt")

    movie_id = 34
    recs = recommender.get_similar_movies(movie_id, num_recommendations=10)
    # print("相似电影推荐：")
    # print(recs)
    id_list = recs["id"].tolist()
    print(id_list)
