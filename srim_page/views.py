from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseRedirect
from urllib.parse import urlparse
from django.views.generic import View, ListView, DetailView, TemplateView
from .models import Stock, Intro, About_Page, About_Srim
from django.db.models import Q


# Home page(intro)
def intro_page(request):
    intro_list = Intro.objects.all()

    return render(
        request,
        'srim_page/intro_list.html',
        {
            'intro_list': intro_list,
        }
    )


# About page(about this website)
class About_PageList(ListView):
    model = About_Page


# About page(about srim)
class About_SrimList(ListView):
    model = About_Srim


class StockList(ListView):
    model = Stock
    ordering = 'pk'


class StockDetail(DetailView):
    model = Stock


class StockChartView(TemplateView):
    template_name = 'srim_page/stock_detail.html'
    model = Stock

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["qs"] = Stock.objects.all()
        context["stock"] = Stock

        return context


class StockSearch(StockList):

    def get_queryset(self):
        q = self.kwargs['q']
        stock_list = Stock.objects.filter(
            Q(name__contains=q) | Q(code__contains=q)
        ).order_by('-created_at').distinct()

        return stock_list

    # def get_context_data(self, **kwargs):
    #     context = super(StockSearch, self).get_context_data()
    #     q = self.kwargs['q']
    #     context['search_info'] = f'검색 결과 : {q}'
    #
    #     return context


def login_page(request):

    return render(
        request,
        'srim_page/login.html',
        {

        }
    )


# class StockLike(View):
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return HttpResponseForbidden
#         else:
#             if 'stock_id' in kwargs:
#                 stock_id = kwargs['stock_id']
#                 stock = Stock.objects.get(pk=stock_id)
#                 user = request.user
#                 if user in stock.like.all():
#                     stock.like.remover(user)
#                 else:
#                     stock.like.add(user)
#             referel_url = request.META.get('HTTP_REFERER')
#             path = urlparse(referel_url).path
#             return HttpResponseRedirect(path)


# class StockLikeList(ListView):
#     model = Stock
#     template_name = 'srim_page/stock_list.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             messages.warning(request, '로그인이 필요합니다')
#             return HttpResponseRedirect('/')
#
#         return super(StockLikeList, self).dispatch(request, *args, **kwargs)
#
#     def get_queryset(self):
#         user = self.request.user
#         queryset = user.like_post.all()
#         return queryset

