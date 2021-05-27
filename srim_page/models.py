from django.db import models
from django.utils.timezone import now


class Stock(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=15)
    sector = models.CharField(max_length=100)
    current_price = models.CharField(max_length=100)
    srim_price = models.CharField(max_length=100)
    srim10_price = models.CharField(max_length=100)
    srim20_price = models.CharField(max_length=100)
    roe = models.CharField(max_length=20, null=True)
    gap = models.CharField(max_length=20, null=True)
    risky = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f'[{self.pk}]{self.name}'
