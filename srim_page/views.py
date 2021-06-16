from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from urllib.parse import urlparse
from django.views.generic import View, ListView, DetailView, TemplateView
from .models import Stock, Intro, About_Page, About_Srim, User
from django.db.models import Q
import json
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy, reverse


def like(request, pk):
    stock = get_object_or_404(Stock, id=pk)

    if request.user in stock.like_users.all():
        stock.like_users.remove(request.user)
    else:
        stock.like_users.add(request.user)

    return redirect('stock:detail', pk=pk)




def login_page(request):

    return render(
        request,
        'srim_page/login.html',
        {

        }
    )


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

    # def get_context_data(self, *args, **kwargs):
    #     context = super(StockDetail, self).get_context_data()
    #     stuff = get_object_or_404(Stock, id=self.kwargs['pk'])
    #     total_likes = stuff.total_likes()
    #     context["total_likes"] = total_likes
    #     return context


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

