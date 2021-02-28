from django.urls import path
from . import views

app_name = 'seekforadvice'

urlpatterns = [
    path('', views.SoA_List.as_view(), name='top'),
    path('detail/<int:pk>', views.SoA_details.as_view(), name='detail'),
]