from django.views import generic


class TopPage(generic.TemplateView):
    template_name = 'index/top_page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['login'] = self.request.user
        return ctx