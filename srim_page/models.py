from django.db import models
from django.utils.timezone import now


class Stock(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=15)
    sector = models.CharField(max_length=100)
    current_price = models.IntegerField()

    srim_price = models.IntegerField()
    srim10_price = models.IntegerField()
    srim20_price = models.IntegerField()

    roe_average = models.CharField(max_length=20, null=True)
    roe_2020 = models.CharField(max_length=20, null=True)
    roe_2019 = models.CharField(max_length=20, null=True)
    roe_2018 = models.CharField(max_length=20, null=True)
    bbb_rate = models.CharField(max_length=20, null=True)

    gap = models.CharField(max_length=20, null=True)

    risky = models.CharField(max_length=20)
    risky_revenue = models.CharField(max_length=20, null=True)
    risky_profit = models.CharField(max_length=20, null=True)
    risky_ebitda = models.CharField(max_length=20, null=True)
    risky_capital = models.CharField(max_length=20, null=True)

    created_at = models.DateTimeField(default=now)


    def __str__(self):
        return f'[{self.pk}]{self.name}'

    def get_absolute_url(self):
        return '/{}/'.format(self.pk)




