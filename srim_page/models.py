from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.conf import settings


# 소개 페이지 모델
class Intro(models.Model):
    title = models.CharField(max_length=28)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'[{self.pk}]{self.title}'


# 홈페이지 이용안내 각 글 모델
class About_Page(models.Model):
    title = models.CharField(max_length=28)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'[{self.pk}]{self.title}'


# 계산 방법 및 안내 각 글 모델
class About_Srim(models.Model):
    title = models.CharField(max_length=28)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'[{self.pk}]{self.title}'


# Stock 모델
class Stock(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=15)
    sector = models.CharField(max_length=100)
    current_price = models.IntegerField()

    srim_price = models.IntegerField()
    srim10_price = models.IntegerField()
    srim20_price = models.IntegerField()

    roe_average = models.FloatField(max_length=20, null=True)
    roe_2021 = models.FloatField(max_length=20, null=True)
    roe_2020 = models.FloatField(max_length=20, null=True)
    roe_2019 = models.FloatField(max_length=20, null=True)
    roe_2018 = models.FloatField(max_length=20, null=True)
    bbb_rate = models.FloatField(max_length=20, null=True)

    gap = models.FloatField(max_length=20, null=True)

    risky = models.CharField(max_length=20)
    risky_revenue = models.CharField(max_length=20, null=True)
    risky_profit = models.CharField(max_length=20, null=True)
    risky_ebitda = models.CharField(max_length=20, null=True)
    risky_capital = models.CharField(max_length=20, null=True)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    # 좋아요 기능 추가, related_name = like_stock
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    like_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='like_stock')


    def __str__(self):
        return f'[{self.pk}]{self.name}'

    # 각 Stock의 url 지정
    def get_absolute_url(self):
        return '/srim/{}/'.format(self.pk)




