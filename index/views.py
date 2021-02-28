from django.views import generic
from relationship.models import Intimate

class TopPage(generic.TemplateView):
    template_name = 'index/top_page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        # ユーザー情報
        ctx['login'] = self.request.user
        """ 親しい友達リスト """
        if self.request.user:
            request_user = self.request.user
            intimate_qs1 = Intimate.objects.filter(sender=request_user, request=True, approval=True)
            intimate_qs2 = Intimate.objects.filter(receiver=request_user, request=True, approval=True)
            intimate_dic = {}
            for user in intimate_qs1:
                intimate_dic[(str(user.receiver.account_name))] = user.date
            for user in intimate_qs2:
                intimate_dic[str(user.sender.account_name)] = user.date
            # 繋がった日付でソート
            intimate_dic_sorted = sorted(intimate_dic.items(), key=lambda x: x[1])
            # account_nameとdateを辞書で渡す
            ctx['intimate_dic_sorted'] = intimate_dic_sorted
        else:
            pass
        return ctx