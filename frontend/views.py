from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

# Create your views here.
def index(request):
    # 模拟从数据库中获取到的电影数据
    # 真实项目中，这里会是你的后端同学写的数据库查询代码
    movie_list = [
        {'id': 1, 'title': '沙丘', 'year': 2021, 'poster': 'https://via.placeholder.com/150x220.png?text=沙丘海报'},
        {'id': 2, 'title': '流浪地球', 'year': 2019, 'poster': 'https://via.placeholder.com/150x220.png?text=流浪地球海报'},
        {'id': 3, 'title': '星际穿越', 'year': 2014, 'poster': 'https://via.placeholder.com/150x220.png?text=星际穿越海报'},
        {'id': 4, 'title': '盗梦空间', 'year': 2010, 'poster': 'https://via.placeholder.com/150x220.png?text=盗梦空间海报'},
        {'id': 5, 'title': '瞬息全宇宙', 'year': 2022, 'poster': 'https://via.placeholder.com/150x220.png?text=瞬息全宇宙海报'},
    ]

    context = {
        'movies': movie_list,
        'user': {'username': '超级影迷', 'is_authenticated': True} # 模拟已登录
    }
    return render(request, 'frontend/index.html', context)

def movie_detail(request, movie_id):
    # 我们把假的数据库升级一下，让它能包含更多信息
    fake_movie_db = {
        1: {'title': '沙丘', 'genres': ['科幻', '冒险']},
        2: {'title': '流浪地球', 'genres': ['科幻', '灾难']},
        3: {'title': '星际穿越', 'genres': ['科幻', '剧情', '冒险']}
    }

    # 查找电影，如果找不到，就给一个默认值
    movie_info = fake_movie_db.get(movie_id, {'title': '未知电影', 'genres': []})

    context = {
        'movie_title': movie_info['title'],
        'movie_genres': movie_info['genres'], # 把类型列表也传给模板
        'movie_id': movie_id
    }
    return render(request, 'frontend/movie_detail.html', context)

def login_view(request):
    if request.method == 'POST':
        # 如果是POST请求，说明用户点击了“登录”按钮
        # request.POST 是一个类似字典的对象，可以获取表单数据
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 在这里，你的后端同学未来会编写验证用户名和密码的逻辑
        # 我们现在只是简单地把收到的信息返回给用户，以作验证
        return HttpResponse(f'<h1>登录成功！</h1><p>用户名: {username}</p><p>密码: {password}</p>')
    else:
        # 如果是GET请求，说明用户是第一次访问这个页面，就显示登录表单
        return render(request, 'frontend/login.html')
    
def register_view(request):
    if request.method == 'POST':
        # 接收用户提交的数据
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # --- 后端逻辑占位 ---
        # 在这里，后端同学未来会检查用户名是否已存在、两次密码是否一致、邮箱格式是否正确，
        # 然后将新用户信息存入数据库。
        # 我们现在只返回一个成功的提示，来验证前端数据已成功发送。
        return HttpResponse(f'<h1>注册成功！</h1><p>欢迎你，{username}！</p><p>你的邮箱是: {email}</p>')
    else:
        # 如果是GET请求，就显示注册表单
        return render(request, 'frontend/register.html')
    
# ▼▼▼ 我们来创建（或检查）这个退出登录的视图函数 ▼▼▼
def logout_view(request):
    # --- 后端逻辑占位 ---
    # 你的后端队友未来会在这里编写清除用户登录状态（session）的真实代码。
    # 对于我们前端来说，我们只需要知道这个过程会发生。

    # 在重定向前，添加一条成功的消息
    messages.success(request, '您已成功退出登录！')

    # 处理完毕后，将用户重定向回首页
    return redirect('index') # 'index' 是我们给首页URL起的名字

def categories_view(request):
    # 模拟的电影类型数据
    genre_list = ['科幻', '动作', '喜剧', '爱情', '悬疑', '动画', '恐怖', '犯罪', '战争', '冒险', '武侠', '奇幻']
    # 模拟的年份数据
    year_list = ['全部', 2024, 2023, 2022, 2021, 2020, 2019, 2018, '更早']

    # 从URL的查询参数中获取用户当前选择的类型和年份，如果没有选，默认为'全部'
    selected_genre = request.GET.get('genre', '全部')
    selected_year = request.GET.get('year', '全部')

    context = {
        'genres': genre_list,
        'years': year_list,
        'selected_genre': selected_genre,
        'selected_year': selected_year,
    }
    return render(request, 'frontend/categories.html', context)