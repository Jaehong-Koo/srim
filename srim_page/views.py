from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Stock, Intro, About, Category


def intro_page(request):
    intro_list = Intro.objects.all()

    return render(
        request,
        'srim_page/intro_list.html',
        {
            'intro_list': intro_list,
        }
    )


def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        about_list = About.objects.filter(category=None).order_by('-created_at')

    else:
        category = Category.objects.get(slug=slug)
        about_list = About.objects.filter(category=category).order_by('-created_at')

    return render(
        request,
        'srim_page/about_list.html',
        {
            'about_list': about_list,
            'categories': Category.objects.all(),
            'no_category_about_count': About.objects.filter(category=None).count(),
            'category': category,
        }
    )


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


