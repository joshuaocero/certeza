from django.urls import path
from . import views

app_name = 'prospect'

urlpatterns = [
    path('form/<int:questionnaire_id>/', views.prospect_form, name='prospect_form'),
    path('form/submit/<int:questionnaire_id>/', views.prospect_form_submit, name='prospect_form_submit'),
    path('form/prospect/<str:prospect_form_id>/join', views.prospect_join, name='prospect_join'),
    path('form/prospect/<str:prospect_form_id>/no-join', views.prospect_no_join, name='prospect_no_join'),
    path('form/prospect/<str:prospect_form_id>/self-study', views.prospect_join_self_study, name='prospect_join_self_study'),
    path('form/prospect/<str:prospect_form_id>/final-success', views.prospect_final_success, name='prospect_final_success'),
]