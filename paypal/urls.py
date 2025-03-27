from . import views
from django.urls import path
from rest_framework_simplejwt import views as jwt_views


urlpatterns = [
    path('subscribe/basic/', views.subscribe_to_basic_plan),
    path('subscribe/basic/success/', views.subscribe_to_basic_plan_on_success),
    path('subscribe/basic/error/', views.subscribe_to_basic_plan_on_error),
]