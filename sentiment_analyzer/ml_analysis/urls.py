from django.urls import path
from . import views

app_name = 'ml_analysis'

urlpatterns = [
    path('', views.MLAnalysisView.as_view(), name='dashboard'),
    path('analyze/<uuid:response_id>/', views.analyze_response, name='analyze_response'),
    path('insights/<uuid:response_id>/', views.get_section_insights, name='get_insights'),
    path('correlations/', views.get_topic_correlations, name='get_correlations'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
    path('upload-training/', views.training_data_upload, name='upload_training'),
    path('retrain/', views.retrain_models, name='retrain_models'),
    path('train-models/', views.TrainModelsView.as_view(), name='train_models'),
]
