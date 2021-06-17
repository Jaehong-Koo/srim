from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect
from urllib.parse import urlparse
from django.views.generic import View, ListView, DetailView, TemplateView
from .models import Stock, Intro, About_Page, About_Srim, User
from django.db.models import Q
import json
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy, reverse


class StockLikeList(ListView):
    model = Stock
    template_name = 'srim_page/stock_list.html'

    def dispatch(self, request, *args, **kwargs):
        return super(StockLikeList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        queryset = user.like_stock.all()
        return queryset


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
