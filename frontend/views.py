from django.db.models import Q  
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from .models import Movie, Genre, UserMovieView
from django.utils import timezone
from .recommender_loader import bert_recommender # 导入全局推荐器实例
from .recommender_loader import bert_recommender, personalize_recommender

# Create your views here.
def index(request):
    movie_list = Movie.objects.all()

    context = {
        'movies': movie_list,
        'user': request.user
    }
    return render(request, 'frontend/index.html', context)

def movie_detail(request, movie_id):
    # 根据 movie_id 从数据库中获取电影对象
    movie = get_object_or_404(Movie, id=movie_id)
    
    if request.user.is_authenticated:
        UserMovieView.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'viewed_at': timezone.now()}
        )
    
    # --- 推荐逻辑 ---
    recommended_movies = []
    if bert_recommender:
        # 1. 传ID给推荐器，获取返回的ID列表 (这一步超快)
        recommended_ids = bert_recommender.get_similar_movie_ids(movie_id, num_recommendations=5)
        
        if recommended_ids:
            # 2. 根据ID列表，从数据库中一次性查询出电影对象用于显示
            recommended_movies_qs = Movie.objects.filter(id__in=recommended_ids)
            # 3. 保持推荐的顺序
            rec_movies_dict = {m.id: m for m in recommended_movies_qs}
            recommended_movies = [rec_movies_dict[rid] for rid in recommended_ids if rid in rec_movies_dict]

    # 将电影对象传递到模板
    context = {
        'movie': movie,
        'recommended_movies': recommended_movies, # 把电影对象列表传给模板
    }
    return render(request, 'frontend/movie_detail.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return HttpResponse('<h1>用户名或密码错误！</h1>')
    else:
        return render(request, 'frontend/login.html')
    
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        errors = []  # 用于存储错误信息

        # 验证两次密码是否一致
        if password != password2:
            errors.append('两次密码不一致！')

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            errors.append('用户名已存在！')

        if errors:
            # 如果有错误，将错误信息传递到模板
            return render(request, 'frontend/register.html', {'errors': errors})

        # 创建用户
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # 注册成功后，重定向到登录页面
        return redirect('login')
    else:
        return render(request, 'frontend/register.html')
    
def logout_view(request):
    # --- 后端逻辑占位 ---
    # 你的后端队友未来会在这里编写清除用户登录状态（session）的真实代码。
    # 对于我们前端来说，我们只需要知道这个过程会发生。
    logout(request) 
    # 在重定向前，添加一条成功的消息
    messages.success(request, '您已成功退出登录！')

    # 处理完毕后，将用户重定向回首页
    return redirect('index') # 'index' 是我们给首页URL起的名字

def search_movies(request):
    query = request.GET.get('q')  # 获取搜索框中的查询字符串
    if query:
        # 使用 Q 对象进行模糊查询，支持中文和其他语言
        movie_list = Movie.objects.filter(name__icontains=query)
    else:
        movie_list = Movie.objects.none()  # 如果没有查询，返回空结果集

    context = {
        'movies': movie_list,
        'query': query,  # 将查询字符串传递到模板
    }
    return render(request, 'frontend/search_results.html', context)

def movie_categories(request):
    # 获取筛选条件
    year = request.GET.get('year')  # 从 URL 参数中获取年份
    genre_id = request.GET.get('genre')  # 从 URL 参数中获取类型 ID
    min_rating = request.GET.get('min_rating')  # 从 URL 参数中获取最低评分

    # 查询所有电影
    movies = Movie.objects.all()

    # 根据筛选条件过滤
    if year:
        movies = movies.filter(year=year)
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
    if min_rating:
        movies = movies.filter(rating__gte=min_rating)

    # 获取所有类型和年份，用于筛选菜单
    genres = Genre.objects.all()
    years = Movie.objects.values_list('year', flat=True).distinct().order_by('-year')

    context = {
        'movies': movies,
        'genres': genres,
        'years': years,
        'selected_year': year,
        'selected_genre': int(genre_id) if genre_id else None,
        'selected_min_rating': min_rating,
    }
    return render(request, 'frontend/movie_categories.html', context)


@login_required
def personal_center_view(request):
    # 获取用户最近浏览的20部电影
    # 使用 .distinct('movie') 来确保每个电影只出现一次（最新的那次）
    recent_views_qs = UserMovieView.objects.filter(user=request.user).order_by('movie', '-viewed_at').distinct('movie')
    
    # 由于 distinct() 在某些数据库（如 SQLite）上有限制，我们用 Python 处理
    # 如果您使用 PostgreSQL，上面的方法效率更高。对于 SQLite，我们用下面的方法：
    viewed_movie_ids = UserMovieView.objects.filter(user=request.user).order_by('-viewed_at').values_list('movie_id', flat=True)
    
    # 去重并保持顺序
    unique_movie_ids = list(dict.fromkeys(viewed_movie_ids))[:20]
    
    # 获取电影对象
    recent_movies = Movie.objects.filter(id__in=unique_movie_ids).order_by('-usermovieview__viewed_at')
    
    # 为了保持正确的顺序，我们需要手动排序
    preserved_order_movies = sorted(recent_movies, key=lambda x: unique_movie_ids.index(x.id))

    context = {
        'user': request.user,
        'recent_movies': preserved_order_movies,
    }
    return render(request, 'frontend/personal_center.html', context)

@login_required
def recommendations_view(request):
    personalized_recs = []
    if personalize_recommender:
        # 1. 获取用户的浏览历史
        viewed_movie_ids = UserMovieView.objects.filter(user=request.user).order_by('-viewed_at').values_list('movie_id', flat=True)
        unique_movie_ids = list(dict.fromkeys(viewed_movie_ids))
        
        # 2. 准备用户历史数据 (movie_id: rating)
        user_history = {movie_id: 8.0 for movie_id in unique_movie_ids}

        if user_history:
            # 3. 调用推荐器获取推荐结果
            recs_df = personalize_recommender.recommend(user_history, num_recommendations=20) # 可以多推荐一些
            
            if not recs_df.empty:
                # 4. 从数据库中查询出电影对象用于显示
                rec_ids = recs_df['id'].tolist()
                recs_qs = Movie.objects.filter(id__in=rec_ids)
                recs_dict = {movie.id: movie for movie in recs_qs}
                personalized_recs = [recs_dict[rec_id] for rec_id in rec_ids if rec_id in recs_dict]

    context = {
        'personalized_recs': personalized_recs,
    }
    return render(request, 'frontend/recommendations.html', context)