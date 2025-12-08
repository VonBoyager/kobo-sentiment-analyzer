from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'tokens', views.APITokenViewSet, basename='apitoken')
router.register(r'questionnaire-sections', views.QuestionnaireSectionViewSet, basename='questionnairesection')
router.register(r'questionnaire-questions', views.QuestionnaireQuestionViewSet, basename='questionnairequestion')
router.register(r'questionnaire-responses', views.QuestionnaireResponseViewSet, basename='questionnaireresponse')
router.register(r'sentiment-analysis', views.SentimentAnalysisViewSet, basename='sentimentanalysis')
router.register(r'topic-analysis', views.TopicAnalysisViewSet, basename='topicanalysis')
router.register(r'correlations', views.SectionTopicCorrelationViewSet, basename='correlation')
router.register(r'ml-models', views.MLModelViewSet, basename='mlmodel')
router.register(r'training-data', views.TrainingDataViewSet, basename='trainingdata')
router.register(r'feedback', views.UserFeedbackViewSet, basename='feedback')
router.register(r'tenants', views.TenantViewSet, basename='tenant')
router.register(r'tenant-files', views.TenantFileViewSet, basename='tenantfile')
router.register(r'tenant-models', views.TenantModelViewSet, basename='tenantmodel')

urlpatterns = [
    # API router endpoints
    path('', include(router.urls)),
    
    # Statistics endpoints
    path('stats/', views.APIStatsView.as_view(), name='api-stats'),
    path('ml-stats/', views.MLStatsView.as_view(), name='ml-stats'),
    
    # Dashboard and Results endpoints
    path('ml/dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('ml/results-data/', views.ResultsDataView.as_view(), name='results-data'),
    path('ml/test-models/', views.TestModelsView.as_view(), name='test-models'),
    path('upload/', views.CSVUploadView.as_view(), name='csv-upload'),
    
    # Utility endpoints
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('version/', views.APIVersionView.as_view(), name='api-version'),
    
    # Authentication endpoints
    path('auth/login/', views.CustomAuthToken.as_view(), name='api_login'),
    path('auth/logout/', views.CustomLogoutView.as_view(), name='api_logout'),
    path('auth/', include('rest_framework.urls')),
]