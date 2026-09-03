from django.urls import path
from . import views

urlpatterns = [
    path('', views.DeviceListCreateView.as_view(), name='device-list-create'),
    path('<uuid:pk>/', views.DeviceDetailView.as_view(), name='device-detail'),
]
