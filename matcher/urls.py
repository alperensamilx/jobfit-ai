from django.urls import path

from . import views

app_name = 'matcher'

urlpatterns = [
    path('', views.analyze_view, name='analyze'),
    path('result/<int:pk>/', views.result_view, name='result'),
    path('history/', views.history_view, name='history'),
]
