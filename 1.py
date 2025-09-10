import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 中文文档
documents = [
    "我喜欢皮克斯电影，很有趣",
    "动画电影让人开心",
    "皮克斯的电影适合儿童",
    "开心"
]

# 自定义分词函数
def chinese_tokenizer(text):
    return jieba.lcut(text)  # 精确模式切分

# 构建向量器
tfidf = TfidfVectorizer(tokenizer=chinese_tokenizer, stop_words=None)

# 转成TF-IDF矩阵
tfidf_matrix = tfidf.fit_transform(documents)

# 查看词表
print(tfidf.get_feature_names_out())

# 计算相似度
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
print(cosine_sim)
