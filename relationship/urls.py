from django.urls import path
from . import views

app_name = 'relationship'

urlpatterns = [
    path('', views.PostList.as_view(), name='home'),
    path('post-details/<int:pk>', views.PostDetail.as_view(), name='post_detail'),
    path('follow/', views.FollowList.as_view(), name='follow'),
    path('follower/', views.FollowerList.as_view(), name='follower'),
    path('new/', views.PostCreate.as_view(), name="post_create"),
    path('update/<int:pk>', views.PostUpdate.as_view(), name='post_update'),
    path('userprofile/<int:pk>', views.UserProfile.as_view(), name='user_profile'),
]