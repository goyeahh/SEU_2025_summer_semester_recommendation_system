from django.urls import path
from . import views # 从当前目录导入views.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 这行代码定义了一条URL规则
    # 当访问应用的根路径('')时, 调用views.py中的index函数
    path('', views.index, name='index'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie-detail'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_movies, name='search-movies'),  # 搜索功能的路由
    path('categories/', views.movie_categories, name='movie-categories'),  # 影片分类页面
    path('personal-center/', views.personal_center_view, name='personal_center'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
