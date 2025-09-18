from django.apps import AppConfig


class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'

    def ready(self):
        # 这行代码确保了服务器启动时会执行 recommender_loader.py
        from . import recommender_loader