from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db import models
import json
import logging

from .services import MLPipeline
from .models import SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation, UserFeedback
from frontend.models import QuestionnaireResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

class MLAnalysisView(View):
    """Main ML analysis view"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Display ML analysis dashboard"""
        # Get user's latest response
        latest_response = QuestionnaireResponse.objects.filter(
            user=request.user,
            is_complete=True
        ).order_by('-submitted_at').first()
        
        # Get comprehensive data for the user (include similar usernames for testing)
        similar_usernames = [request.user.username.lower(), request.user.username.upper(), 
                           request.user.username.capitalize()]
        
        # Use all similar usernames for the main counts
        total_responses = QuestionnaireResponse.objects.filter(
            user__username__in=similar_usernames, 
            is_complete=True
        ).count()
        
        sentiment_analyses = SentimentAnalysis.objects.filter(
            response__user__username__in=similar_usernames
        ).count()
        
        topic_analyses = TopicAnalysis.objects.filter(
            response__user__username__in=similar_usernames
        ).count()
        
        correlations = SectionTopicCorrelation.objects.count()
        
        # Check if there's data under the exact current username
        exact_responses = QuestionnaireResponse.objects.filter(user=request.user, is_complete=True).count()
        has_similar_data = total_responses > exact_responses
        
        # Get sentiment breakdown (include similar usernames)
        from django.db.models import Count
        sentiment_breakdown = SentimentAnalysis.objects.filter(
            response__user__username__in=similar_usernames
        ).values('sentiment_label').annotate(count=Count('id'))
        sentiment_dict = {item['sentiment_label']: item['count'] for item in sentiment_breakdown}
        
        # Get average confidence (include similar usernames)
        avg_confidence = SentimentAnalysis.objects.filter(
            response__user__username__in=similar_usernames
        ).aggregate(
            avg_conf=models.Avg('confidence')
        )['avg_conf'] or 0
        
        # Get correlation insights
        positive_correlations = SectionTopicCorrelation.objects.filter(
            correlation_score__gt=0.5
        ).order_by('-correlation_score')[:5]
        
        negative_correlations = SectionTopicCorrelation.objects.filter(
            correlation_score__lt=-0.3
        ).order_by('correlation_score')[:5]
        
        context = {
            'latest_response': latest_response,
            'total_responses': total_responses,
            'has_similar_data': has_similar_data,
            'sentiment_analyses': sentiment_analyses,
            'total_topic_analyses': topic_analyses,
            'correlations': correlations,
            'sentiment_breakdown': sentiment_dict,
            'avg_confidence': avg_confidence * 100,  # Convert to percentage
            'has_analysis': False,
            'sentiment_analysis': None,
            'topic_analyses': [],
            'section_insights': {},
            'positive_correlations': positive_correlations,
            'negative_correlations': negative_correlations,
            'has_correlations': SectionTopicCorrelation.objects.exists()
        }
        
        if latest_response:
            # Get sentiment analysis
            try:
                sentiment_analysis = latest_response.sentiment_analysis
                context['sentiment_analysis'] = sentiment_analysis
                context['has_analysis'] = True
            except SentimentAnalysis.DoesNotExist:
                pass
            
            # Get topic analyses
            topic_analyses = latest_response.topic_analyses.all()
            context['topic_analyses'] = topic_analyses
            
            # Get section insights
            if context['has_analysis']:
                pipeline = MLPipeline()
                context['section_insights'] = pipeline.get_section_insights(latest_response)
        
        return render(request, 'ml_analysis/dashboard.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class TrainModelsView(View):
    """Train ML models endpoint - runs synchronously to ensure data availability"""
    
    def post(self, request):
        try:
            pipeline = MLPipeline()
            # Run synchronously so the frontend waits
            results = pipeline.train_all_models()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Models trained successfully',
                'results': results
            })
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

@login_required
def analyze_response(request, response_id):
    """Analyze a specific questionnaire response"""
    response = get_object_or_404(QuestionnaireResponse, id=response_id, user=request.user)
    
    if not response.review:
        return JsonResponse({'error': 'No review text available for analysis'}, status=400)
    
    try:
        pipeline = MLPipeline()
        analysis_result = pipeline.analyze_response(response)
        
        if 'error' in analysis_result:
            return JsonResponse(analysis_result, status=500)
        
        return JsonResponse(analysis_result)
    except Exception as e:
        logger.error(f"Analysis failed for response {response_id}: {e}")
        return JsonResponse({'error': 'Analysis failed'}, status=500)

@login_required
def get_section_insights(request, response_id):
    """Get insights for why sections scored low"""
    response = get_object_or_404(QuestionnaireResponse, id=response_id, user=request.user)
    
    try:
        pipeline = MLPipeline()
        insights = pipeline.get_section_insights(response)
        return JsonResponse(insights)
    except Exception as e:
        logger.error(f"Insights generation failed for response {response_id}: {e}")
        return JsonResponse({'error': 'Insights generation failed'}, status=500)

@login_required
def get_topic_correlations(request):
    """Get topic correlations with section scores"""
    try:
        correlations = SectionTopicCorrelation.objects.all().order_by('-abs(correlation_score)')[:20]
        
        data = []
        for correlation in correlations:
            data.append({
                'section_name': correlation.section_name,
                'topic_name': correlation.topic_name,
                'correlation_score': correlation.correlation_score,
                'negative_correlation': correlation.negative_correlation,
                'sample_size': correlation.sample_size
            })
        
        return JsonResponse({'correlations': data})
    except Exception as e:
        logger.error(f"Correlations retrieval failed: {e}")
        return JsonResponse({'error': 'Failed to retrieve correlations'}, status=500)

@csrf_exempt
@login_required
def submit_feedback(request):
    """Submit user feedback on ML analysis"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        response_id = data.get('response_id')
        feedback_type = data.get('feedback_type')
        feedback_text = data.get('feedback_text', '')
        
        response = get_object_or_404(QuestionnaireResponse, id=response_id, user=request.user)
        
        # Create feedback
        feedback = UserFeedback.objects.create(
            user=request.user,
            response=response,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            sentiment_accuracy=data.get('sentiment_accuracy'),
            topic_relevance=data.get('topic_relevance'),
            section_correlation=data.get('section_correlation')
        )
        
        return JsonResponse({'status': 'success', 'feedback_id': str(feedback.id)})
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return JsonResponse({'error': 'Feedback submission failed'}, status=500)

@login_required
def training_data_upload(request):
    """Upload training data CSV"""
    if request.method != 'POST':
        return render(request, 'ml_analysis/upload_training_data.html')
    
    try:
        csv_file = request.FILES['csv_file']
        
        # Process CSV file
        import pandas as pd
        from io import StringIO
        
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Validate required columns
        required_columns = ['text', 'sentiment_label']
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f'CSV must contain columns: {", ".join(required_columns)}')
            return render(request, 'ml_analysis/upload_training_data.html')
        
        # Process each row
        created_count = 0
        for _, row in df.iterrows():
            # Create training data entry
            from .models import TrainingData
            TrainingData.objects.create(
                text=row['text'],
                sentiment_label=row['sentiment_label'],
                section_scores=row.get('section_scores', {}),
                source='csv_upload',
                is_verified=True
            )
            created_count += 1
        
        messages.success(request, f'Successfully uploaded {created_count} training samples')
        return render(request, 'ml_analysis/upload_training_data.html')
        
    except Exception as e:
        logger.error(f"Training data upload failed: {e}")
        messages.error(request, f'Upload failed: {str(e)}')
        return render(request, 'ml_analysis/upload_training_data.html')

@login_required
def retrain_models(request):
    """Retrain ML models with latest data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        pipeline = MLPipeline()
        
        # Train correlation analyzer
        training_result = pipeline.correlation_analyzer.train_model()
        
        if 'error' in training_result:
            return JsonResponse(training_result, status=500)
        
        # Save correlations
        pipeline.correlation_analyzer.save_correlations()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Models retrained successfully',
            'training_result': training_result
        })
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return JsonResponse({'error': 'Model retraining failed'}, status=500)