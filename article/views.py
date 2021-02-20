from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import generic
from django.urls import reverse_lazy

from .models import Article
from .forms import ArticleForm


class OnlyYouMixin(UserPassesTestMixin):
    """スーパーユーザーだけユーザーページアクセスを許可する"""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.pk == user.is_superuser


class Index(generic.ListView):
    """ 記事一覧の表示 """
    template_name = 'article/index.html'
    model = Article
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['article'] = Article.objects.order_by('-id')
        return ctx


class Detail(generic.DetailView):
    """ 投稿内容の表示 """
    template_name = 'article/detail.html'
    model = Article
    context_object_name = 'objects'


class AddForm(generic.CreateView):
    template_name = 'article/form.html'
    form_class = ArticleForm
    success_url = reverse_lazy('article:index')