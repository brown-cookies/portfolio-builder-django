from . import views
from django.urls import path
from rest_framework_simplejwt import views as jwt_views


urlpatterns = [
    path('user', views.user_info)
]


auth_patterns = [
    path('auth/access/', jwt_views.TokenObtainPairView.as_view()),
    path('auth/blacklist/', jwt_views.TokenBlacklistView.as_view()),
    path('auth/create/', views.create_user),
    path('auth/refresh/', jwt_views.TokenRefreshView.as_view()),
    path('auth/validate/', views.validate_token),
    path('auth/verify/', jwt_views.TokenVerifyView.as_view()),
]


# Embed auth patterns

urlpatterns += auth_patterns