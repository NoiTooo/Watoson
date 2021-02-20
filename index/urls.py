from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views


app_name = 'index'

urlpatterns = [
        path('', views.TopPage.as_view(), name='top'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)