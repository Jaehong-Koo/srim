from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Stock, Intro, About_Page, About_Srim
from django.db.models import Q


def intro_page(request):
    intro_list = Intro.objects.all()

    return render(
        request,
        'srim_page/intro_list.html',
        {
            'intro_list': intro_list,
        }
    )


def search_page(request):
    stock = Stock.objects.all()

    return render(
        request,
        'srim_page/stock_detail.html',
        {
            'stock': stock,
        }
    )


class About_PageList(ListView):
    model = About_Page


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


