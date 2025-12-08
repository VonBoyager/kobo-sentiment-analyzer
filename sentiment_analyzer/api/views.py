from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Q, Min, Max, Value
from django.db import models
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import hashlib
import secrets

from .models import APIToken, APIRequest, APILog, APIConfiguration, APIVersion
from .serializers import (
    UserSerializer, QuestionnaireResponseSerializer, CompleteAnalysisSerializer,
    SentimentAnalysisSerializer, TopicAnalysisSerializer, SectionTopicCorrelationSerializer,
    MLModelSerializer, TrainingDataSerializer, UserFeedbackSerializer,
    TenantSerializer, TenantFileSerializer, TenantModelSerializer, TenantUserSerializer,
    APITokenSerializer, APIRequestSerializer, APILogSerializer,
    APIConfigurationSerializer, APIVersionSerializer, APIStatsSerializer, MLStatsSerializer,
    QuestionnaireSectionSerializer, QuestionnaireQuestionSerializer
)
from frontend.models import QuestionnaireResponse, QuestionnaireSection, QuestionnaireQuestion, SectionScore
from ml_analysis.models import SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation, MLModel, TrainingData, UserFeedback
from ml_analysis.services import MLPipeline
from tenants.models import Tenant, TenantFile, TenantModel, TenantUser
from django.core.management import call_command
from django.core.files.uploadedfile import InMemoryUploadedFile
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # Case-insensitive username handling
        if 'username' in request.data:
            username = request.data['username']
            # Find user case-insensitively
            user = User.objects.filter(username__iexact=username).first()
            if user:
                # Update request data with correct case username
                # We need to make a mutable copy if it's QueryDict
                if hasattr(request.data, '_mutable'):
                    request.data._mutable = True
                    request.data['username'] = user.username
                    request.data._mutable = False
                else:
                    # For JSON data (dict)
                    request.data['username'] = user.username
        
        serializer = self.serializer_class(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'username': user.username,
                'email': user.email,
                'is_staff': user.is_staff,
                'id': user.id
            }
        })

class CustomLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the token to force logout
            if hasattr(request, 'auth') and hasattr(request.auth, 'delete'):
                request.auth.delete()
        except:
            pass
        return Response(status=status.HTTP_200_OK)

class APITokenViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API tokens"""
    queryset = APIToken.objects.all()
    serializer_class = APITokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return APIToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        serializer.save(user=self.request.user, token=token)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate a token"""
        token = self.get_object()
        if token.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        new_token = secrets.token_urlsafe(32)
        token.token = new_token
        token.save()
        
        return Response({'token': new_token})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a token"""
        token = self.get_object()
        if token.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        token.is_active = False
        token.save()
        
        return Response({'message': 'Token deactivated'})

class QuestionnaireSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for questionnaire sections"""
    queryset = QuestionnaireSection.objects.all()
    serializer_class = QuestionnaireSectionSerializer
    permission_classes = [permissions.AllowAny]

class QuestionnaireQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for questionnaire questions"""
    queryset = QuestionnaireQuestion.objects.all()
    serializer_class = QuestionnaireQuestionSerializer
    permission_classes = [permissions.AllowAny]

class QuestionnaireResponseViewSet(viewsets.ModelViewSet):
    """ViewSet for questionnaire responses"""
    queryset = QuestionnaireResponse.objects.all()
    serializer_class = QuestionnaireResponseSerializer
    
    def get_permissions(self):
        """Allow anonymous users to create responses, but restrict listing"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        # Staff can see all, regular users see their own
        if self.request.user.is_anonymous:
            return QuestionnaireResponse.objects.none()
        if self.request.user.is_staff:
            return QuestionnaireResponse.objects.all()
        return QuestionnaireResponse.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Handle questionnaire submission with answers"""
        try:
            from frontend.models import QuestionResponse, QuestionnaireQuestion, SectionScore
            from django.db import transaction

            # Extract data
            review_text = request.data.get('review', '')
            answers = request.data.get('answers', []) # List of {question_id, score}

            if not answers:
                return Response({'error': 'No answers provided'}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # 1. Create Response
                user = request.user if request.user.is_authenticated else None
                response = QuestionnaireResponse.objects.create(
                    user=user,
                    review=review_text,
                    is_complete=True # Assuming submitted means complete
                )

                # 2. Create Question Responses and Calculate Section Scores
                section_scores = defaultdict(list)
                
                for answer in answers:
                    q_id = answer.get('question_id')
                    score = answer.get('score')
                    
                    if q_id and score:
                        question = QuestionnaireQuestion.objects.get(id=q_id)
                        QuestionResponse.objects.create(
                            response=response,
                            question=question,
                            score=score
                        )
                        section_scores[question.section].append(int(score))
                
                # 3. Save Section Scores
                for section, scores in section_scores.items():
                    avg_score = sum(scores) / len(scores)
                    SectionScore.objects.create(
                        response=response,
                        section=section,
                        average_score=avg_score,
                        total_questions=len(scores)
                    )
                
                # 4. Trigger ML Pipeline (optional/async)
                try:
                    # Run synchronously for now to give immediate feedback or use Celery
                    # For now, let's just trigger it if available
                    pass
                except Exception as e:
                    logger.error(f"Error triggering ML: {e}")

                serializer = self.get_serializer(response)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating response: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def complete_analysis(self, request, pk=None):
        """Get complete analysis for a response including sentiment, topics, and correlations"""
        response = self.get_object()
        serializer = CompleteAnalysisSerializer(response)
        return Response(serializer.data)

class SentimentAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for sentiment analysis results"""
    queryset = SentimentAnalysis.objects.all()
    serializer_class = SentimentAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SentimentAnalysis.objects.filter(response__user=self.request.user)

class TopicAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for topic analysis results"""
    queryset = TopicAnalysis.objects.all()
    serializer_class = TopicAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TopicAnalysis.objects.filter(response__user=self.request.user)

class SectionTopicCorrelationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for section-topic correlations"""
    queryset = SectionTopicCorrelation.objects.all()
    serializer_class = SectionTopicCorrelationSerializer
    permission_classes = [permissions.IsAuthenticated]

class MLModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ML models"""
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [permissions.IsAuthenticated]

class TrainingDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for training data"""
    queryset = TrainingData.objects.all()
    serializer_class = TrainingDataSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for user feedback"""
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserFeedback.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenants"""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return tenants where user is owner or member
        return Tenant.objects.filter(
            Q(owner=self.request.user) | 
            Q(tenant_users__user=self.request.user, tenant_users__is_active=True)
        ).distinct()

class TenantFileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant files"""
    queryset = TenantFile.objects.all()
    serializer_class = TenantFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return files from tenants where user has access
        accessible_tenants = Tenant.objects.filter(
            Q(owner=self.request.user) | 
            Q(tenant_users__user=self.request.user, tenant_users__is_active=True)
        ).distinct()
        return TenantFile.objects.filter(tenant__in=accessible_tenants)

class TenantModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tenant models"""
    queryset = TenantModel.objects.all()
    serializer_class = TenantModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return models from tenants where user has access
        accessible_tenants = Tenant.objects.filter(
            Q(owner=self.request.user) | 
            Q(tenant_users__user=self.request.user, tenant_users__is_active=True)
        ).distinct()
        return TenantModel.objects.filter(tenant__in=accessible_tenants)

class APIStatsView(APIView):
    """API statistics endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Calculate API statistics
        total_requests = APIRequest.objects.count()
        successful_requests = APIRequest.objects.filter(status_code__lt=400).count()
        failed_requests = APIRequest.objects.filter(status_code__gte=400).count()
        average_response_time = APIRequest.objects.aggregate(
            avg_time=Avg('response_time')
        )['avg_time'] or 0
        
        today = timezone.now().date()
        requests_today = APIRequest.objects.filter(
            created_at__date=today
        ).count()
        
        active_tokens = APIToken.objects.filter(is_active=True).count()
        total_users = User.objects.count()
        
        stats = {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'average_response_time': round(average_response_time, 2),
            'requests_today': requests_today,
            'active_tokens': active_tokens,
            'total_users': total_users
        }
        
        serializer = APIStatsSerializer(stats)
        return Response(serializer.data)

class MLStatsView(APIView):
    """ML analysis statistics endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Calculate ML statistics
        total_analyses = SentimentAnalysis.objects.count()
        sentiment_analyses = SentimentAnalysis.objects.count()
        topic_analyses = TopicAnalysis.objects.count()
        correlation_analyses = SectionTopicCorrelation.objects.count()
        
        avg_confidence = SentimentAnalysis.objects.aggregate(
            avg_conf=Avg('confidence')
        )['avg_conf'] or 0
        
        # Most common sentiment
        sentiment_counts = SentimentAnalysis.objects.values('sentiment_label').annotate(
            count=Count('sentiment_label')
        ).order_by('-count')
        most_common_sentiment = sentiment_counts[0]['sentiment_label'] if sentiment_counts else 'neutral'
        
        total_topics = TopicAnalysis.objects.values('topic_id').distinct().count()
        
        stats = {
            'total_analyses': total_analyses,
            'sentiment_analyses': sentiment_analyses,
            'topic_analyses': topic_analyses,
            'correlation_analyses': correlation_analyses,
            'average_confidence': round(avg_confidence, 3),
            'most_common_sentiment': most_common_sentiment,
            'total_topics': total_topics
        }
        
        serializer = MLStatsSerializer(stats)
        return Response(serializer.data)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class HealthCheckView(APIView):
    """Health check endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        from django.db import connection
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        health_data = {
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'database': db_status,
            'version': '1.0.0',
            'uptime': 'N/A'  # Could be implemented with process monitoring
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return Response(health_data, status=status_code)

class APIVersionView(APIView):
    """API version information"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        current_version = APIVersion.objects.filter(is_current=True).first()
        if current_version:
            serializer = APIVersionSerializer(current_version)
            return Response(serializer.data)
        else:
            return Response({
                'version': '1.0.0',
                'is_current': True,
                'is_deprecated': False
            })

# Utility functions for API logging
def log_api_request(request, endpoint, status_code, response_time, user=None, token=None):
    """Log an API request"""
    api_request = APIRequest.objects.create(
        token=token,
        user=user,
        endpoint=endpoint,
        method=request.method,
        status_code=status_code,
        response_time=response_time,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    return api_request

def log_api_event(request_id, level, message, data=None):
    """Log an API event"""
    APILog.objects.create(
        request_id=request_id,
        level=level,
        message=message,
        data=data
    )

class DashboardStatsView(APIView):
    """Dashboard statistics with ML insights"""
    permission_classes = [permissions.AllowAny]  # Allow anonymous for development
    
    def get(self, request):
        try:
            # Get all responses (for admin) or user's responses
            # Handle anonymous users
            if hasattr(request, 'user') and request.user.is_authenticated:
                if request.user.is_staff:
                    responses = QuestionnaireResponse.objects.filter(is_complete=True)
                else:
                    responses = QuestionnaireResponse.objects.filter(user=request.user, is_complete=True)
            else:
                # For anonymous access, return all responses
                responses = QuestionnaireResponse.objects.filter(is_complete=True)
            
            # Ensure Unified Data Source for Statistics
            # We are already fetching all completed responses, which includes
            # both uploaded CSV data and individual questionnaire submissions.
            # No additional filtering is needed to combine them.
            
            total_responses = responses.count()
            
            # Sentiment breakdown
            sentiment_analyses = SentimentAnalysis.objects.filter(response__in=responses)
            sentiment_counts = sentiment_analyses.values('sentiment_label').annotate(
                count=Count('sentiment_label')
            )
            sentiment_breakdown = {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            }
            for item in sentiment_counts:
                label = item['sentiment_label'].lower()
                if label in sentiment_breakdown:
                    sentiment_breakdown[label] = item['count']
            
            total_sentiment = sum(sentiment_breakdown.values())
            if total_sentiment > 0:
                sentiment_breakdown = {
                    k: round((v / total_sentiment) * 100, 1) 
                    for k, v in sentiment_breakdown.items()
                }
            
            # Company Performance (section averages)
            section_performance = []
            sections = QuestionnaireSection.objects.all()
            for section in sections:
                section_scores = SectionScore.objects.filter(
                    section=section,
                    response__in=responses
                )
                if section_scores.exists():
                    avg_score = section_scores.aggregate(avg=Avg('average_score'))['avg'] or 0
                    section_performance.append({
                        'section__name': section.name,
                        'average_score': round(avg_score, 2)
                    })
            
            # Generated Insights from ML
            strengths = []
            weaknesses = []
            
            try:
                ml_pipeline = MLPipeline()
                
                # Load feature importance if available
                if not ml_pipeline.section_feature_importance:
                    ml_pipeline.section_feature_importance = ml_pipeline._load_section_feature_importance_from_db()
                
                # Get feature importance data
                importance_data = ml_pipeline.section_feature_importance or {}
                positive_data = importance_data.get('positive', {})
                negative_data = importance_data.get('negative', {})
                
                for section_name, data in positive_data.items():
                    keywords = data.get('keywords', [])[:3]
                    if keywords:
                        strengths.append({
                            'section': section_name,
                            'keywords': keywords
                        })
                
                for section_name, data in negative_data.items():
                    keywords = data.get('keywords', [])[:3]
                    if keywords:
                        weaknesses.append({
                            'section': section_name,
                            'keywords': keywords
                        })
                
                # If no insights from feature importance, try to get from correlations
                if not strengths and not weaknesses:
                    # Get insights from section topic correlations
                    from ml_analysis.models import SectionTopicCorrelation
                    positive_correlations = SectionTopicCorrelation.objects.filter(
                        negative_correlation=False
                    ).exclude(topic_name__icontains='Feature Importance').order_by('-correlation_score')[:5]
                    
                    for corr in positive_correlations:
                        keywords = list(corr.keywords.keys())[:3] if isinstance(corr.keywords, dict) else []
                        if keywords:
                            strengths.append({
                                'section': corr.section_name,
                                'keywords': keywords
                            })
                    
                    negative_correlations = SectionTopicCorrelation.objects.filter(
                        negative_correlation=True
                    ).exclude(topic_name__icontains='Feature Importance').order_by('correlation_score')[:5]
                    
                    for corr in negative_correlations:
                        keywords = list(corr.keywords.keys())[:3] if isinstance(corr.keywords, dict) else []
                        if keywords:
                            weaknesses.append({
                                'section': corr.section_name,
                                'keywords': keywords
                            })
            except Exception as e:
                logger.warning(f"Error generating insights: {e}")
                # Return empty insights if generation fails
            
            # Sentiment trend by quarters (based on review_date from CSV)
            # Use efficient database aggregation instead of Python loops
            sentiment_trend = []
            
            try:
                # Get all responses with dates and their sentiment analyses
                all_responses = responses.filter(submitted_at__isnull=False)
                
                if all_responses.exists():
                    from django.db.models import Case, When, IntegerField, CharField
                    from django.db.models.functions import Concat, Cast, ExtractYear
                    
                    # Annotate sentiment analyses with year and quarter from their responses
                    # This is more efficient than looping through responses
                    quarter_sentiments = SentimentAnalysis.objects.filter(
                        response__in=all_responses
                    ).annotate(
                        year=ExtractYear('response__submitted_at'),
                        quarter=Case(
                            When(response__submitted_at__month__lte=3, then=1),
                            When(response__submitted_at__month__lte=6, then=2),
                            When(response__submitted_at__month__lte=9, then=3),
                            default=4,
                            output_field=IntegerField()
                        )
                    ).values('year', 'quarter').annotate(
                        avg_score=Avg('compound_score')
                    ).order_by('year', 'quarter')
                    
                    # Build trend list from aggregated data
                    for item in quarter_sentiments:
                        sentiment_trend.append({
                            'month': f"{item['year']}-Q{item['quarter']}",
                            'avg_score': round(item['avg_score'] or 0, 2)
                        })
            except Exception as e:
                logger.error(f"Error calculating sentiment trend: {e}", exc_info=True)
                sentiment_trend = []
            
            return Response({
                'total_responses': total_responses,
                'sentiment_breakdown': sentiment_breakdown,
                'company_performance': section_performance,
                'generated_insights': {
                    'strengths': strengths,
                    'weaknesses': weaknesses
                },
                'sentiment_trend': sentiment_trend
            })
        except Exception as e:
            logger.error(f"Error in DashboardStatsView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResultsDataView(APIView):
    """Results data with ML features"""
    permission_classes = [permissions.AllowAny]  # Allow anonymous for development
    
    def get(self, request):
        try:
            from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection
            from ml_analysis.models import SentimentAnalysis
            from collections import Counter
            import re
            
            # Get all responses
            responses = QuestionnaireResponse.objects.filter(is_complete=True)
            
            # Calculate Overall Company Score (average of all section averages)
            all_section_scores = SectionScore.objects.filter(response__in=responses)
            overall_score = 0.0
            if all_section_scores.exists():
                overall_score = all_section_scores.aggregate(avg=Avg('average_score'))['avg'] or 0.0
            
            # Get section-level feature importance (not question-level)
            correlations = SectionTopicCorrelation.objects.filter(
                topic_name__icontains='Feature Importance'
            )
            
            # Group by section (remove question-level details)
            section_importance = {}
            for corr in correlations:
                section_name = corr.section_name
                # Extract section name only (remove any question details)
                if section_name not in section_importance:
                    section_importance[section_name] = {
                        'importance': 0.0,
                        'sample_size': 0
                    }
                # Use absolute correlation score for importance
                section_importance[section_name]['importance'] += abs(float(corr.correlation_score))
                section_importance[section_name]['sample_size'] = max(
                    section_importance[section_name]['sample_size'],
                    corr.sample_size
                )
            
            # Normalize section importance to sum to 1.0 (100%)
            total_importance = sum(s['importance'] for s in section_importance.values())
            if total_importance > 0:
                for section_name in section_importance:
                    section_importance[section_name]['importance'] /= total_importance
            
            # Get most repeated words with sentiments from all feedback text
            word_sentiments = {}
            word_counts = Counter()
            
            for response in responses:
                if response.review:
                    # Get sentiment for this response
                    try:
                        sentiment_analysis = response.sentiment_analysis
                        sentiment_label = sentiment_analysis.sentiment_label.lower()
                    except:
                        sentiment_label = 'neutral'
                    
                    # Extract words from review text
                    words = re.findall(r'\b[a-zA-Z]{3,}\b', response.review.lower())
                    for word in words:
                        # Skip common stop words
                        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'she', 'use', 'her', 'many', 'than', 'them', 'these', 'this', 'that', 'with', 'have', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'back', 'after', 'years', 'many', 'where', 'much', 'should', 'well', 'people', 'through', 'being', 'work', 'make', 'good', 'great', 'company', 'management', 'team', 'employee', 'employees', 'feel', 'feeling', 'feelings'}
                        if word not in stop_words and len(word) > 2:
                            word_counts[word] += 1
                            if word not in word_sentiments:
                                word_sentiments[word] = {'positive': 0, 'negative': 0, 'neutral': 0}
                            word_sentiments[word][sentiment_label] += 1
            
            # Get top 50 most repeated words with their dominant sentiment
            top_words = []
            for word, count in word_counts.most_common(50):
                sentiments = word_sentiments[word]
                total = sum(sentiments.values())
                if total > 0:
                    # Determine dominant sentiment
                    max_sentiment = max(sentiments.items(), key=lambda x: x[1])
                    dominant_sentiment = max_sentiment[0] if max_sentiment[1] > 0 else 'neutral'
                    sentiment_ratio = max_sentiment[1] / total
                    
                    top_words.append({
                        'word': word,
                        'count': count,
                        'sentiment': dominant_sentiment,
                        'sentiment_ratio': round(sentiment_ratio, 2),
                        'positive_count': sentiments['positive'],
                        'negative_count': sentiments['negative'],
                        'neutral_count': sentiments['neutral']
                    })
            
            return Response({
                'overall_company_score': round(overall_score, 2),
                'section_importance': [
                    {
                        'section': section_name,
                        'importance': round(data['importance'], 4),
                        'sample_size': data['sample_size']
                    }
                    for section_name, data in sorted(
                        section_importance.items(),
                        key=lambda x: x[1]['importance'],
                        reverse=True
                    )
                ],
                'trending_words': top_words
            })
        except Exception as e:
            logger.error(f"Error in ResultsDataView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TestModelsView(APIView):
    """Test ML models - runs in background thread"""
    permission_classes = [permissions.AllowAny]  # Allow anonymous for development
    
    def post(self, request):
        import threading
        
        def train_models_async():
            """Train models in background thread"""
            try:
                ml_pipeline = MLPipeline()
                results = ml_pipeline.train_all_models()
                logger.info(f"Model training completed: {results}")
            except Exception as e:
                logger.error(f"Error in background model training: {e}", exc_info=True)
        
        # Start training in background thread
        thread = threading.Thread(target=train_models_async, daemon=True)
        thread.start()
        
        return Response({
            'status': 'success',
            'message': 'Models are being trained in the background. You can continue using the application.',
        })

class CSVUploadView(APIView):
    """Upload CSV file"""
    permission_classes = [permissions.AllowAny]  # Allow anonymous for development
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                return Response({'error': 'No CSV file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not csv_file.name.lower().endswith('.csv'):
                return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create a default user for uploads
            from django.contrib.auth.models import User
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.filter(is_staff=True).first()
            if not user:
                # Create a default user if none exists
                # Try to get existing user first to avoid race conditions
                user, created = User.objects.get_or_create(
                    username='default_user',
                    defaults={
                        'email': 'default@kobo.com',
                        'password': 'default123'
                    }
                )
                if created:
                    user.set_password('default123')
                    user.save()
            
            # Temporarily set request.user for the command
            request.user = user
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                for chunk in csv_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # Load data using management command
                from io import StringIO
                import sys
                
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                call_command('load_dataset', 
                           csv_file=tmp_file_path, 
                           username=user.username,
                           batch_size=50)
                
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # Check if data was actually loaded
                from ml_analysis.models import QuestionnaireResponse
                response_count = QuestionnaireResponse.objects.count()
                
                # Check for actual errors (not warnings)
                output_lower = output.lower()
                # Only treat as errors if they're actual errors, not warnings
                error_indicators = ['traceback', 'exception', 'failed to', 'cannot', 'unable to', 'critical', 'error:']
                has_error = any(indicator in output_lower for indicator in error_indicators)
                
                if has_error:
                    error_lines = [line for line in output.split('\n') 
                                 if any(indicator in line.lower() for indicator in error_indicators)]
                    error_message = error_lines[0] if error_lines else 'Unknown error'
                    return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
                
                # Success - data was loaded
                return Response({
                    'status': 'success',
                    'message': f'CSV file uploaded and processed successfully. Loaded {response_count} responses.',
                    'responses_loaded': response_count,
                    'output': output[:500] if output else ''
                })
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in CSVUploadView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

