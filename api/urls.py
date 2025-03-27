from account.viewset import UserViewSet, SettingViewSet
from project.viewset import ProjectViewSet, PageViewSet

from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'user', UserViewSet)
router.register(r'setting', SettingViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'page', PageViewSet)


urlpatterns = [
    path('account/', include('account.urls')),
    path('', include(router.urls)),
]