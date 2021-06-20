from django.contrib import admin
from .models import Stock, Intro, About_Page, About_Srim
from django_summernote.admin import SummernoteModelAdmin


# Summernote 에디터 사용
class IntroAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'


class About_PageAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'


class About_SrimAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'


admin.site.register(Stock)
admin.site.register(Intro, IntroAdmin)
admin.site.register(About_Page, About_PageAdmin)
admin.site.register(About_Srim, About_SrimAdmin)


