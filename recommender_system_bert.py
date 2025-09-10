import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import BertTokenizer, BertModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

import torch

# 矩阵分解
from sklearn.decomposition import TruncatedSVD

# 协同过滤
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import cross_validate, train_test_split
from surprise import KNNBasic
from collections import defaultdict
import os

SAVE_PATH = "bert_embeddings.npy"
INDEX_PATH = "bert_index.npy"  # 保存已经计算过的文本索引

def get_or_update_bert_embeddings(texts, get_bert_embedding):
    """
    texts: 电影内容 (list or Series)
    get_bert_embedding: 你定义的函数
    """
    if os.path.exists(SAVE_PATH) and os.path.exists(INDEX_PATH):
        print("加载已保存的 BERT 向量...")
        bert_matrix = np.load(SAVE_PATH)
        processed_idx = set(np.load(INDEX_PATH).tolist())
    else:
        bert_matrix = np.empty((0, 768))  # 假设 BERT hidden_size = 768
        processed_idx = set()

    new_embeddings = []
    new_indices = []

    for i, text in enumerate(texts):
        if i not in processed_idx:
            # 只算新数据
            emb = get_bert_embedding([text])  # 返回 shape (1,768)
            new_embeddings.append(emb)
            new_indices.append(i)

    if new_embeddings:
        print(f"检测到 {len(new_embeddings)} 条新数据，正在计算 BERT 向量...")
        new_embeddings = np.vstack(new_embeddings)
        bert_matrix = np.vstack([bert_matrix, new_embeddings])
        processed_idx.update(new_indices)

        # 保存更新后的矩阵和索引
        np.save(SAVE_PATH, bert_matrix)
        np.save(INDEX_PATH, np.array(list(processed_idx)))
    else:
        print("没有新数据，无需计算。")

    return bert_matrix

model_path = r"./bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertModel.from_pretrained(model_path)

model.eval()

# 加载数据集
ratings = pd.read_csv('data/ratings.csv')
movies = pd.read_csv('data/movies.csv')
tags = pd.read_csv('data/tags.csv')
links = pd.read_csv('data/links.csv')

num_users = ratings['userId'].nunique()
print(num_users)

print(ratings.head())
print(movies.head())
print(tags.head())
print(links.head())

# 数据预处理
ratings.drop_duplicates(subset=['userId', 'movieId'], keep='last', inplace=True)
ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')
tags['timestamp'] = pd.to_datetime(tags['timestamp'], unit='s')
movies['genres'] = movies['genres'].str.replace('|', ' ')

all_tags = tags.groupby('movieId')['tag'].apply(lambda x: ' '.join(x)).reset_index()
movies = pd.merge(movies, all_tags, on='movieId', how='left')
movies['tag'] = movies['tag'].fillna('')
movies['content'] = movies['tag'] + ' ' + movies['genres'] + ' ' + movies['title']
print(movies.head())

# 将文本转成 BERT 向量
def get_bert_embedding(texts, batch_size=16, max_len=128):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True,
                           max_length=max_len, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        # 平均池化最后一层 hidden states，得到句子向量
        batch_embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        embeddings.append(batch_embeddings)
    return np.vstack(embeddings)

# 生成所有电影的 BERT 向量
print("准备生成/更新 BERT 向量...")
bert_matrix = get_or_update_bert_embeddings(movies["content"], get_bert_embedding)
print("BERT 矩阵形状:", bert_matrix.shape)

# 计算余弦相似度
cosine_sim_bert = cosine_similarity(bert_matrix, bert_matrix)

# 重新建立索引（和你原来一样）
indices = pd.Series(movies.index, index=movies['title']).drop_duplicates()

# 推荐函数（只换了相似度矩阵）
def content_recommendations(title, cosine_sim=cosine_sim_bert, num_recommendations=10):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:num_recommendations+1]
    movie_indices = [i[0] for i in sim_scores]
    return movies['title'].iloc[movie_indices]

# 测试
test_title = "Toy Story (1995)"
print(f"\n测试电影: {test_title}")
print("基于 BERT 的推荐结果:")
print(content_recommendations(test_title, num_recommendations=10))

# 协同过滤推荐
user_movie_matrix = ratings.pivot_table(index='userId', columns='movieId', values='rating')
item_similarity = user_movie_matrix.corr(method='pearson', min_periods=50)

def item_based_recommendations(user_id, num_recommendations=5):
    user_ratings = user_movie_matrix.loc[user_id].dropna()
    similar_items = pd.Series()
    for movie_id, rating in user_ratings.items():
        sims = item_similarity[movie_id].dropna()
        sims = sims.map(lambda x: x * rating)
        similar_items = pd.concat([similar_items, sims])
    similar_items = similar_items.groupby(similar_items.index).sum()
    similar_items = similar_items.sort_values(ascending=False)
    similar_items = similar_items.drop(user_ratings.index, errors='ignore')
    return movies.set_index('movieId').loc[similar_items.index[:num_recommendations]]['title']


print("用户-电影矩阵形状:", user_movie_matrix.shape)
print("项目相似度矩阵形状:", item_similarity.shape if item_similarity is not None else "未计算")

# 测试基于项目的推荐
test_user = ratings['userId'].iloc[0]
print(f"\n测试用户ID: {test_user}")
item_recs = item_based_recommendations(test_user, 3)
print("基于项目的推荐结果:")
print(item_recs)



# 基于模型的协同过滤
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)
trainset, testset = train_test_split(data, test_size=0.25, random_state=42)
svd = SVD()
svd.fit(trainset)
predictions = svd.test(testset)
print(len(predictions))
rmse = accuracy.rmse(predictions)

def svd_recommendations(user_id, num_recommendations=5):
    user_rated_movies = ratings[ratings['userId'] == user_id]['movieId'].tolist()
    all_movies = movies['movieId'].tolist()
    unrated_movies = [movie for movie in all_movies if movie not in user_rated_movies]
    predictions = [svd.predict(user_id, movie_id) for movie_id in unrated_movies]
    predictions.sort(key=lambda x: x.est, reverse=True)
    recommended_movie_ids = [int(pred.iid) for pred in predictions[:num_recommendations]]
    return movies.set_index('movieId').loc[recommended_movie_ids]['title']


print(f"预测数量: {len(predictions)}")
print(f"RMSE: {rmse}")

# 测试SVD推荐
svd_recs = svd_recommendations(test_user, 3)
print("SVD推荐结果:")
print(svd_recs)

# 混合模型推荐
def hybrid_recommendations(user_id, title, num_recommendations=10):
    content_recs = content_recommendations(title, num_recommendations=50)
    content_recs = movies[movies['title'].isin(content_recs)]
    item_recs = item_based_recommendations(user_id, num_recommendations=50)
    item_recs = movies[movies['title'].isin(item_recs)]
    svd_recs = svd_recommendations(user_id, num_recommendations=50)
    svd_recs = movies[movies['title'].isin(svd_recs)]
    hybrid_recs = pd.merge(content_recs, item_recs, on='title')

    print(hybrid_recs)

    user_rated_movies = ratings[ratings['userId'] == user_id]['movieId'].tolist()
    hybrid_recs = hybrid_recs[~hybrid_recs['movieId_x'].isin(user_rated_movies)]
    return hybrid_recs['title'].head(num_recommendations)

# 模型评估
def precision_recall_at_k(predictions, k=10, threshold=3.5):
    user_est_true = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))
    precisions = dict()
    recalls = dict()
    for uid, user_ratings in user_est_true.items():
        user_ratings.sort(key=lambda x: x[0], reverse=True)
        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings)
        n_rec_k = sum((est >= threshold) for (est, _) in user_ratings[:k])
        n_rel_and_rec_k = sum(((true_r >= threshold) and (est >= threshold))
                              for (est, true_r) in user_ratings[:k])
        precisions[uid] = n_rel_and_rec_k / n_rec_k if n_rec_k != 0 else 0
        recalls[uid] = n_rel_and_rec_k / n_rel if n_rel != 0 else 0
    precision = sum(precisions.values()) / len(precisions)
    recall = sum(recalls.values()) / len(recalls)
    return precision, recall


print("\n=== 混合推荐完整测试 ===")
test_user_id = 1
test_movie_title = "Toy Story (1995)"

print(f"测试用户: {test_user_id}")
print(f"测试电影: {test_movie_title}")
hybrid_results = hybrid_recommendations(test_user_id, test_movie_title, num_recommendations=5)
print("\n混合推荐结果:")
for i, movie in enumerate(hybrid_results, 1):
    print(f"{i}. {movie}")







precision, recall = precision_recall_at_k(predictions, k=10, threshold=4.0)
print(f'Precision@10: {precision:.4f}')
print(f'Recall@10: {recall:.4f}')

# 结果展示
user_id = 1
title = 'Toy Story (1995)'
print(f'为用户 {user_id} 推荐的电影：')
print(hybrid_recommendations(user_id, title))

# 可视化
plt.figure(figsize=(8,6))
sns.histplot(ratings['rating'], bins=10, kde=True)
plt.title('Rating Distribution')
plt.xlabel('Rating')
plt.ylabel('Count')
plt.show()
