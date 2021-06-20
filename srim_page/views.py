from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from .models import Stock, Intro, About_Page, About_Srim
from django.db.models import Q
from django.contrib.auth.decorators import login_required


# Stock Like List View for User
class StockLikeList(ListView):
    model = Stock
    template_name = 'srim_page/stock_list.html'

    # dispatch 사용
    def dispatch(self, request, *args, **kwargs):
        return super(StockLikeList, self).dispatch(request, *args, **kwargs)

    # 각 request user = user 지정
    def get_queryset(self):
        user = self.request.user
        # like_stock 메소드에 해당하는 모든 리스트 return
        queryset = user.like_stock.all()
        return queryset


# Like Function, need login
@login_required(login_url='/login/')
def like(request, pk):
    stock = get_object_or_404(Stock, id=pk)

    # unlike할 때 -> remove
    if request.user in stock.like_users.all():
        stock.like_users.remove(request.user)

    # like할 때 -> add
    else:
        stock.like_users.add(request.user)

    return redirect('stock:detail', pk=pk)


# Login Page view
def login_page(request):

    return render(
        request,
        'srim_page/login.html',
        {

        }
    )


# Intro page view
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


# Stock List page
class StockList(ListView):
    model = Stock
    ordering = 'pk'


# Stock Detail page
class StockDetail(DetailView):
    model = Stock


# Stock ChartView page
class StockChartView(TemplateView):
    template_name = 'srim_page/stock_detail.html'
    model = Stock

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["qs"] = Stock.objects.all()
        context["stock"] = Stock

        return context


# Stock Search page
class StockSearch(StockList):

    def get_queryset(self):
        q = self.kwargs['q']
        stock_list = Stock.objects.filter(
            Q(name__contains=q) | Q(code__contains=q)
        ).order_by('-created_at').distinct()

        return stock_list
