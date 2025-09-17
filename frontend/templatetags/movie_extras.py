from django import template
from django.utils.html import format_html
import math

register = template.Library()

@register.filter(name='rating_to_stars', is_safe=True)
def generate_stars(rating):
    """
    将 0-10 的评分转换为 5 颗星的 HTML 显示。
    例如: 8.5 -> ★★★★☆
    """
    if rating is None:
        return "暂无评分"
    
    # 将 10分制 转为 5星制
    stars_rating = float(rating) 
    
    full_stars = int(stars_rating)
    half_star = 1 if (stars_rating - full_stars) >= 0.3 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars_html = ''
    stars_html += '<i class="bi bi-star-fill"></i>' * full_stars
    if half_star:
        stars_html += '<i class="bi bi-star-half"></i>'
    stars_html += '<i class="bi bi-star"></i>' * empty_stars
    
    return format_html(f'评分： <span class="rating-stars">{stars_html}</span> ({rating})')