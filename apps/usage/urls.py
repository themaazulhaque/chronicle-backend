from django.urls import path
from . import views

urlpatterns = [
    path('', views.AppListView.as_view(), name='app-list'),
    path('<uuid:pk>/', views.AppDetailView.as_view(), name='app-detail'),
    path('<uuid:pk>/history/', views.AppHistoryView.as_view(), name='app-history'),
]
