from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views import generic

from .models import Seek, Advice
from .forms import AddAdvice

User = get_user_model()


class SoA_List(generic.ListView):
    template_name = 'seekforadvice/soa_list.html'
    context_object_name = 'objects_list'
    model = Seek

    def get_queryset(self):
        queryset = Seek.objects.order_by('-date_posted')
        return  queryset


class SoA_details(generic.DetailView):
    template_name = 'seekforadvice/soa_detail.html'
    context_object_name = 'objects'
    model = Seek

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        """ 紐づいたアドバイスを表示 """
        seek = self.kwargs.get('pk')
        ctx['advices'] = Advice.objects.filter(post_connected=seek)
        """ アドバイスを追加 """
        ctx['form'] = AddAdvice()
        return ctx

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            if 'add' in self.request.POST:
                form = AddAdvice(self.request.POST)
                if form.is_valid():
                    add_advice = Advice()
                    add_advice.author = User.objects.get(pk=self.request.user.pk)
                    add_advice.content = self.request.POST.get('content')
                    add_advice.post_connected = Seek.objects.get(pk=self.kwargs.get('pk'))
                    add_advice.save()
                else:
                    return redirect('seekforadvice:top')
            return self.get(self, *args, **kwargs)