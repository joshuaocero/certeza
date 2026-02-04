from django.contrib import admin
from .models import Questionnaire, Question, SelectOption, Responses, QuestionnaireLog, Prospect


# class SelectOptionInline(admin.TabularInline):
#     model = SelectOption
#     extra = 1
#     fields = ('text', 'value', 'order')
#     show_change_link = True

class SelectOptionAdmin(admin.ModelAdmin):
    filter_horizontal = ('questions',)

admin.site.site_header = "Certeza Admin"
admin.site.site_title = "Certeza Admin Portal"
admin.site.index_title = "Welcome to Certeza Admin Portal"

admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(SelectOption)
admin.site.register(Responses)
admin.site.register(Prospect)