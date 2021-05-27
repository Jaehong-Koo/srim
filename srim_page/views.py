from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Stock


class StockList(ListView):
    model = Stock
    ordering = 'pk'


class StockDetail(DetailView):
    model = Stock
