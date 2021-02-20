from django.urls import path
from . import views


app_name = 'article'

urlpatterns = [
        path('', views.Index.as_view(), name='index'),
        path('<int:pk>/', views.Detail.as_view(), name='detail'),
        path('add_form/', views.AddForm.as_view(), name='add_form'),
]