import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import re


class MovieRecommender:
    def __init__(self, movies_df):
        """
        初始化推荐系统
        movies_df: 包含电影数据的DataFrame
        """
        self.movies = movies_df.copy()
        self.tfidf = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self._prepare_data()
        self._compute_similarity()

    def _prepare_data(self):
        """数据预处理"""
        # 清洗数据
        for col in ['genres', 'countries', 'directors', 'actors']:
            self.movies[col] = self.movies[col].fillna('').astype(str)

        self.movies['plot'] = self.movies['plot'].fillna('')

        # 创建特征文本
        self.movies['feature_text'] = self.movies.apply(self._create_feature_string, axis=1)

    def _create_feature_string(self, row):
        """创建特征组合字符串"""
        features = []

        # 处理类型
        if row['genres'] and row['genres'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['genres']))

        # 处理国家
        if row['countries'] and row['countries'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['countries']))

        # 处理导演
        if row['directors'] and row['directors'] != 'nan':
            features.append(re.sub(r'[^\w\s]', ' ', row['directors']))

        # 处理演员（取前3个）
        if row['actors'] and row['actors'] != 'nan':
            actors = row['actors'].split('|')[:3]
            features.extend(actors)

        # 处理剧情简介
        if row['plot'] and row['plot'] != 'nan':
            features.append(row['plot'][:200])  # 取前200字符

        return ' '.join(features)

    def _compute_similarity(self):
        """计算内容相似度矩阵"""
        print("计算电影内容相似度矩阵...")
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            min_df=2,
            max_df=0.8
        )
        self.tfidf_matrix = self.tfidf.fit_transform(self.movies['feature_text'])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        print(f"相似度矩阵形状: {self.cosine_sim.shape}")

    def _calculate_quality_score(self, preference_weight=0.5):
        """计算电影质量得分"""
        quality_scores = []

        for _, movie in self.movies.iterrows():
            # 提取评分分布（转换为小数）
            star5 = movie.get('star_5', 0) / 100
            star4 = movie.get('star_4', 0) / 100
            star3 = movie.get('star_3', 0) / 100
            star2 = movie.get('star_2', 0) / 100
            star1 = movie.get('star_1', 0) / 100

            # 计算高评分占比和低评分占比
            high_rating_ratio = star5 + star4  # 4-5星占比
            low_rating_ratio = star2 + star1  # 1-2星占比

            # 评分一致性（高分段占比高且低分段占比低）
            consistency_score = high_rating_ratio * (1 - low_rating_ratio)

            # 评分可信度（基于分布形状）
            credibility = min(1.0, high_rating_ratio * 1.5)  # 高评分占比越高越可信

            # 基础质量得分（使用processed_rating）
            base_score = movie.get('processed_rating', 3.0) / 5.0  # 归一化到0-1

            # 最终质量得分（考虑一致性和可信度）
            quality_score = base_score * (0.6 + 0.4 * consistency_score) * (0.7 + 0.3 * credibility)

            # 根据用户偏好调整
            quality_score = quality_score * (0.8 + 0.2 * preference_weight)

            quality_scores.append(quality_score)

        # 归一化到0-1范围
        quality_scores = np.array(quality_scores)
        if quality_scores.max() > quality_scores.min():
            quality_scores = (quality_scores - quality_scores.min()) / (quality_scores.max() - quality_scores.min())

        return quality_scores

    def _analyze_user_preference(self, user_history):
        """分析用户评分偏好"""
        if not user_history:
            return 0.5, 3.0  # 默认值

        user_ratings = list(user_history.values())
        avg_rating = np.mean(user_ratings)

        # 计算偏好强度（用户平均评分越高，偏好强度越大）
        preference_strength = min(1.0, avg_rating / 4.0)  # 4分以上认为有强偏好

        return preference_strength, avg_rating

    def recommend(self, user_history, num_recommendations=10, content_weight=0.7, quality_weight=0.3):
        """
        生成个性化推荐

        Args:
            user_history: 用户历史 {movie_id: rating}
            num_recommendations: 推荐数量
            content_weight: 内容相似度权重
            quality_weight: 质量得分权重

        Returns:
            推荐电影DataFrame
        """
        # 分析用户偏好
        preference_strength, avg_rating = self._analyze_user_preference(user_history)
        print(f"用户平均评分: {avg_rating:.2f}, 偏好强度: {preference_strength:.2f}")

        # 计算内容相似度得分
        content_scores = np.zeros(len(self.movies))
        valid_history_count = 0

        for movie_id, user_rating in user_history.items():
            movie_mask = self.movies['id'] == movie_id
            if movie_mask.any():
                idx = self.movies[movie_mask].index[0]
                # 用户评分越高，该电影的权重越大
                rating_weight = (user_rating / 5.0) * preference_strength
                content_scores += self.cosine_sim[idx] * rating_weight
                valid_history_count += 1

        if valid_history_count > 0:
            content_scores = content_scores / valid_history_count

        # 计算质量得分
        quality_scores = self._calculate_quality_score(preference_strength)

        # 综合得分
        composite_scores = content_scores * content_weight + quality_scores * quality_weight

        # 生成推荐结果
        recommendations = self._generate_recommendations(composite_scores, user_history, num_recommendations)

        return recommendations

    def _generate_recommendations(self, scores, user_history, num_recommendations):
        """生成推荐列表"""
        watched_ids = set(user_history.keys())
        movie_scores = []

        for idx, score in enumerate(scores):
            movie_id = self.movies.iloc[idx]['id']
            if movie_id not in watched_ids:
                movie_data = self.movies.iloc[idx].copy()
                movie_data['recommend_score'] = score
                movie_scores.append((score, movie_data))

        # 按推荐得分排序
        movie_scores.sort(key=lambda x: x[0], reverse=True)

        recommendations = []
        for score, movie_data in movie_scores[:num_recommendations]:
            recommendations.append(movie_data)

        result_df = pd.DataFrame(recommendations)

        # 选择重要的列返回
        important_cols = ['id', 'name', 'genres', 'year', 'countries', 'directors',
                          'processed_rating', 'recommend_score']
        available_cols = [col for col in important_cols if col in result_df.columns]

        return result_df[available_cols].sort_values('recommend_score', ascending=False)

    def get_movie_info(self, movie_id):
        """获取电影详细信息"""
        movie = self.movies[self.movies['id'] == movie_id]
        if not movie.empty:
            return movie.iloc[0]
        return None


# 使用示例
def main():
    # 假设movies_df是您的数据
    movies_df = pd.read_csv('merged_movie_database.csv')

    # 初始化推荐系统
    recommender = MovieRecommender(movies_df)

    # 用户历史评分（movie_id: rating）这里传入用户的历史观看电影id和对应打分
    user_history = {
        35: 4.5,
        36: 4.6,
        37: 4.8
    }

    # 生成推荐
    print("生成个性化推荐...")
    recommendations = recommender.recommend(user_history, num_recommendations=10)

    # 返回推荐电影的 id 列表
    recommended_ids = recommendations['id'].tolist()
    print(recommended_ids)
    """
    print("\n推荐结果:")
    print("=" * 80)
    for idx, row in recommendations.iterrows():
        print(f"{idx + 1}. {row['name']} ({row['year']})")
        print(f"   类型: {row['genres']}")
        print(f"   导演: {row['directors']}")
        print(f"   评分: {row['processed_rating']:.1f} | 推荐得分: {row['recommend_score']:.3f}")
        print(f"   国家: {row['countries']}")
        print("-" * 80)

    # 查看用户看过的电影
    print("\n用户观看历史:")
    for movie_id, rating in user_history.items():
        movie_info = recommender.get_movie_info(movie_id)
        if movie_info is not None:
            print(f"《{movie_info['name']}》 - 用户评分: {rating} | 平均评分: {movie_info['processed_rating']:.1f}")
    """


if __name__ == "__main__":
    main()