import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class MovieRecommender:
    def __init__(self, movies_df):
        self.movies = movies_df.copy()
        self.tfidf = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self._prepare_data()
        self._compute_similarity()

    def _prepare_data(self):
        # 清洗数据，字段名与 Movie 模型保持一致
        for col in ['genres', 'countries', 'director', 'actors']:
            self.movies[col] = self.movies[col].fillna('').astype(str)
        self.movies['description'] = self.movies['description'].fillna('')
        self.movies['feature_text'] = self.movies.apply(self._create_feature_string, axis=1)

    def _create_feature_string(self, row):
        features = []
        if row['genres'] and row['genres'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['genres']))
        if row['countries'] and row['countries'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['countries']))
        if row['director'] and row['director'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['director']))
        if row['actors'] and row['actors'] != 'nan':
            actors = str(row['actors']).split(',')[:3] # 假设演员以逗号分隔
            features.extend(actors)
        if row['description'] and row['description'] != 'nan':
            features.append(row['description'][:200])
        return ' '.join(features)

    def _compute_similarity(self):
        print("计算电影内容相似度矩阵 (TF-IDF)...")
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.tfidf.fit_transform(self.movies['feature_text'])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        print(f"TF-IDF相似度矩阵形状: {self.cosine_sim.shape}")

    def _calculate_quality_score(self):
        # 使用模型中的 star_* 字段
        star_cols = ['star_5', 'star_4', 'star_3', 'star_2', 'star_1']
        for col in star_cols:
            if col not in self.movies.columns:
                self.movies[col] = 0 # 如果数据不完整，填充0
        
        total_ratings = self.movies[star_cols].sum(axis=1)
        total_ratings[total_ratings == 0] = 1 # 避免除以0
        
        high_rating_ratio = (self.movies['star_5'] + self.movies['star_4']) / total_ratings
        # 使用模型的 rating 字段 (0-10分制)，归一化到 0-1
        base_score = self.movies['rating'].fillna(5.0).astype(float) / 10.0
        
        quality_scores = base_score * (0.7 + 0.3 * high_rating_ratio)
        
        # 归一化
        if quality_scores.max() > quality_scores.min():
            quality_scores = (quality_scores - quality_scores.min()) / (quality_scores.max() - quality_scores.min())
        return quality_scores.to_numpy()

    def recommend(self, user_history, num_recommendations=10, content_weight=0.7, quality_weight=0.3):
        if not user_history:
            return pd.DataFrame()

        # 构建用户画像向量
        user_profile = np.zeros(self.tfidf_matrix.shape[1])
        valid_history_count = 0
        for movie_id, user_rating in user_history.items():
            movie_mask = self.movies['id'] == movie_id
            if movie_mask.any():
                idx = self.movies.index[movie_mask].tolist()[0]
                # 评分越高，权重越大 (将10分制转为5分制)
                rating_weight = (user_rating / 10.0) * 5.0
                user_profile += self.tfidf_matrix[idx] * rating_weight
                valid_history_count += 1
        
        if valid_history_count > 0:
            user_profile = user_profile / valid_history_count

        # --- 解决 TypeError 的关键修改 ---
        # 将 user_profile 转换为一个二维 numpy array
        # user_profile.reshape(1, -1) 将一维数组 [a, b, c] 转换为二维数组 [[a, b, c]]
        user_profile_2d = np.asarray(user_profile).reshape(1, -1)

        # 计算内容相似度得分
        content_scores = cosine_similarity(user_profile_2d, self.tfidf_matrix).flatten()
        
        # 计算质量得分
        quality_scores = self._calculate_quality_score()
        
        # 综合得分
        composite_scores = content_scores * content_weight + quality_scores * quality_weight
        
        # 生成推荐
        watched_ids = set(user_history.keys())
        self.movies['recommend_score'] = composite_scores
        
        recommendations = self.movies[~self.movies['id'].isin(watched_ids)]
        recommendations = recommendations.sort_values('recommend_score', ascending=False).head(num_recommendations)
        
        return recommendations