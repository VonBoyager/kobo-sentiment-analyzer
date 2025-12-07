from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('questionnaire-intro/', views.questionnaire_intro, name='questionnaire_intro'),
    path('sentiment-analysis/', views.sentiment_analysis, name='sentiment_analysis'),
    path('questionnaire-congratulations/<int:response_id>/', views.questionnaire_congratulations, name='questionnaire_congratulations'),
    path('questionnaire-results/<int:response_id>/', views.questionnaire_results, name='questionnaire_results'),
#   path('raw-data/', views.raw_data, name='raw_data'),
    path('upload-data/', views.upload_data, name='upload_data'),
#   path('support/', views.support, name='support'),
    path('accounts-settings/', views.accounts_settings, name='accounts_settings'),
    path('logout/', views.logout_view, name='logout'),
    path('api/data/', views.api_data, name='api_data'),
    # Special questionnaire URLs
    path('special-questionnaire/<uuid:token>/', views.special_questionnaire_view, name='special_questionnaire'),
    path('special-questionnaire/<uuid:token>/thank-you/', views.special_questionnaire_thank_you, name='special_questionnaire_thank_you'),
]
