from django.urls import path
from . import views # 从当前目录导入views.py

urlpatterns = [
    # 这行代码定义了一条URL规则
    # 当访问应用的根路径('')时, 调用views.py中的index函数
    path('', views.index, name='index'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie-detail'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('categories/', views.categories_view, name='movie-categories'),
]