from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    id = models.AutoField(primary_key=True)  # 电影 ID
    name = models.CharField(max_length=255)  # 电影名称
    genres = models.ManyToManyField('Genre', related_name='movies')  # 类型（多对多关系）
    year = models.IntegerField()  # 上映年份
    countries = models.CharField(max_length=255)  # 制作国家（用逗号分隔）
    director = models.CharField(max_length=255)  # 导演
    actors = models.TextField()  # 主演（用逗号分隔的字符串）
    duration_minutes = models.IntegerField()  # 时长（分钟）
    description = models.TextField(blank=True, null=True)  # 剧情简介
    star_5 = models.IntegerField(default=0)  # 5星评分人数
    star_4 = models.IntegerField(default=0)  # 4星评分人数
    star_3 = models.IntegerField(default=0)  # 3星评分人数
    star_2 = models.IntegerField(default=0)  # 2星评分人数
    star_1 = models.IntegerField(default=0)  # 1星评分人数
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)  # 评分（0.0-10.0）
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)  # 本地存储图片

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)  # 类型名称（如动作、科幻）

    def __str__(self):
        return self.name
    
class UserMovieView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']  # 默认按浏览时间降序排序

    def __str__(self):
        return f'{self.user.username} viewed {self.movie.name} at {self.viewed_at}'