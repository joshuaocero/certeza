from django.urls import path
from . import views

app_name = 'organisation'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('prospects/', views.prospects, name='prospects'),
    path('disciplers/', views.disciplers, name='disciplers'),
    path('survey-responses/', views.survey_responses, name='survey_responses'),
    path('api/assign-prospect/', views.assign_prospect, name='assign_prospect'),
    path('api/assign-prospect-to-discipler/', views.assign_prospect_to_discipler, name='assign_prospect_to_discipler'),
]