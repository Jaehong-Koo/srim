from django.contrib import admin
from .models import Stock, Intro, About, Category


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Stock)
admin.site.register(Intro)
admin.site.register(About)
admin.site.register(Category, CategoryAdmin)

