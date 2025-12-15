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
from django.core.cache import cache
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
                
                # 4. Trigger ML Pipeline
                try:
                    if review_text and len(review_text.strip()) > 0:
                        from ml_analysis.services import SentimentAnalyzer, MLPipeline
                        
                        # Run Sentiment Analysis
                        analyzer = SentimentAnalyzer()
                        result = analyzer.analyze_text(review_text)
                        
                        # Save Sentiment Analysis
                        SentimentAnalysis.objects.create(
                            response=response,
                            compound_score=result['compound'],
                            positive_score=result['pos'],
                            negative_score=result['neg'],
                            neutral_score=result['neu'],
                            sentiment_label=result['sentiment'],
                            confidence=result['confidence'],
                            text_length=len(review_text)
                        )
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
            # Convert counts to percentages, but keep original if needed
            # For the pie chart, we need either counts or percentages, Recharts handles both
            # but sticking to percentages as frontend expects
            if total_sentiment > 0:
                sentiment_breakdown = {
                    k: round((v / total_sentiment) * 100, 1)
                    for k, v in sentiment_breakdown.items()
                }
            else:
                # If no sentiments found yet (e.g. not analyzed), try to infer from section scores
                # This is a fallback for data that might be missing SentimentAnalysis
                logger.info("No sentiment analysis found, inferring from scores")
                positive_count = 0
                negative_count = 0
                neutral_count = 0
                
                for response in responses:
                    avg_score = response.section_scores.aggregate(avg=Avg('average_score'))['avg']
                    if avg_score:
                        if avg_score >= 4.0:
                            positive_count += 1
                        elif avg_score <= 2.5:
                            negative_count += 1
                        else:
                            neutral_count += 1
                
                total_inferred = positive_count + negative_count + neutral_count
                if total_inferred > 0:
                    sentiment_breakdown = {
                        'positive': round((positive_count / total_inferred) * 100, 1),
                        'negative': round((negative_count / total_inferred) * 100, 1),
                        'neutral': round((neutral_count / total_inferred) * 100, 1)
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
            
            # Sentiment trend by quarters
            # Improved robust calculation that handles missing SentimentAnalysis
            sentiment_trend = []
            
            try:
                # Get all responses with dates
                all_responses = responses.filter(submitted_at__isnull=False).order_by('submitted_at')
                
                if all_responses.exists():
                    from django.db.models import Case, When, IntegerField, F
                    from django.db.models.functions import ExtractYear, ExtractMonth
                    
                    # Group by Year-Quarter
                    # We can't easily join with SentimentAnalysis if it doesn't exist for some records
                    # So we'll iterate through responses and bucket them manually or use a more robust query
                    
                    # Calculate quarter for each response
                    responses_with_quarter = all_responses.annotate(
                        year=ExtractYear('submitted_at'),
                        month=ExtractMonth('submitted_at'),
                        quarter=Case(
                            When(month__lte=3, then=1),
                            When(month__lte=6, then=2),
                            When(month__lte=9, then=3),
                            default=4,
                            output_field=IntegerField()
                        )
                    )
                    
                    # Use a dictionary to aggregate scores by quarter
                    quarter_scores = defaultdict(list)
                    
                    for resp in responses_with_quarter:
                        key = f"{resp.year}-Q{resp.quarter}"
                        
                        # Try to get sentiment score, otherwise fallback to section average mapped to -1..1
                        score = 0.0
                        try:
                            # Check for pre-fetched or related sentiment analysis
                            if hasattr(resp, 'sentiment_analysis'):
                                score = resp.sentiment_analysis.compound_score
                            else:
                                # Fallback: Map 1-5 rating to -1 to 1 compound score
                                # 5 -> 1.0, 3 -> 0.0, 1 -> -1.0
                                avg_section_score = resp.section_scores.aggregate(avg=Avg('average_score'))['avg']
                                if avg_section_score:
                                    # Normalize 1-5 to -1-1: (x - 3) / 2
                                    score = (avg_section_score - 3.0) / 2.0
                        except Exception:
                            score = 0.0
                            
                        quarter_scores[key].append(score)
                    
                    # Calculate averages and format for frontend
                    sorted_quarters = sorted(quarter_scores.keys())
                    for q in sorted_quarters:
                        scores = quarter_scores[q]
                        avg = sum(scores) / len(scores) if scores else 0
                        sentiment_trend.append({
                            'month': q,
                            'avg_score': round(avg, 2)
                        })
                        
            except Exception as e:
                logger.error(f"Error calculating sentiment trend: {e}", exc_info=True)
                sentiment_trend = []
            
            # Identify user's latest submission for highlighting on the trend chart
            user_latest_submission = None
            if hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_staff:
                latest_response = QuestionnaireResponse.objects.filter(
                    user=request.user,
                    is_complete=True
                ).order_by('-submitted_at').first()
                
                if latest_response and latest_response.submitted_at:
                    month = latest_response.submitted_at.month
                    quarter_num = (month - 1) // 3 + 1
                    quarter_str = f"{latest_response.submitted_at.year}-Q{quarter_num}"
                    
                    user_latest_submission = {
                        'date': latest_response.submitted_at.date().isoformat(),
                        'quarter': quarter_str,
                        'review': latest_response.review[:50] + '...' if latest_response.review else 'No review'
                    }

            return Response({
                'total_responses': total_responses,
                'sentiment_breakdown': sentiment_breakdown,
                'company_performance': section_performance,
                'generated_insights': {
                    'strengths': strengths,
                    'weaknesses': weaknesses
                },
                'sentiment_trend': sentiment_trend,
                'user_latest_submission': user_latest_submission
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
        
        # Reset progress
        cache.set('training_status', {
            'status': 'starting',
            'progress': 0,
            'message': 'Initializing training process...'
        }, 300)
        
        def train_models_async():
            """Train models in background thread"""
            try:
                ml_pipeline = MLPipeline()
                results = ml_pipeline.train_all_models()
                logger.info(f"Model training completed: {results}")
            except Exception as e:
                logger.error(f"Error in background model training: {e}", exc_info=True)
                cache.set('training_status', {
                    'status': 'error',
                    'progress': 0,
                    'message': f'Error: {str(e)}'
                }, 300)
        
        # Start training in background thread
        thread = threading.Thread(target=train_models_async, daemon=True)
        thread.start()
        
        return Response({
            'status': 'success',
            'message': 'Models are being trained in the background.',
        })

class TrainingStatusView(APIView):
    """Check status of background training"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        status = cache.get('training_status', {
            'status': 'idle',
            'progress': 0,
            'message': 'No training in progress'
        })
        return Response(status)

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

class PublicDashboardStatsView(APIView):
    """Public view for demo dashboard"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            # Get demo user
            try:
                demo_user = User.objects.get(username='demo')
            except User.DoesNotExist:
                return Response({'error': 'Demo user not configured'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get user's latest response
            latest_response = QuestionnaireResponse.objects.filter(
                user=demo_user,
                is_complete=True
            ).order_by('-submitted_at').first()
            
            # Get comprehensive data for the user
            similar_usernames = [demo_user.username.lower(), demo_user.username.upper(),
                               demo_user.username.capitalize()]
            
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
            
            # Get sentiment breakdown
            sentiment_breakdown = SentimentAnalysis.objects.filter(
                response__user__username__in=similar_usernames
            ).values('sentiment_label').annotate(count=Count('id'))
            sentiment_dict = {item['sentiment_label']: item['count'] for item in sentiment_breakdown}
            
            # Get average confidence
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
            
            data = {
                'total_responses': total_responses,
                'sentiment_analyses': sentiment_analyses,
                'total_topic_analyses': topic_analyses,
                'correlations': correlations,
                'sentiment_breakdown': sentiment_dict,
                'avg_confidence': avg_confidence * 100,
                'positive_correlations': list(positive_correlations.values(
                    'section_name', 'topic_name', 'correlation_score', 'sample_size'
                )),
                'negative_correlations': list(negative_correlations.values(
                    'section_name', 'topic_name', 'correlation_score', 'sample_size'
                ))
            }
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"Public dashboard stats failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PublicResultsView(APIView):
    """Public view for demo results"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            # Get demo user
            try:
                demo_user = User.objects.get(username='demo')
            except User.DoesNotExist:
                return Response({'error': 'Demo user not configured'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get all responses for the demo user
            responses = QuestionnaireResponse.objects.filter(
                user=demo_user,
                is_complete=True
            ).order_by('-submitted_at')
            
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = 10
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = responses.count()
            page_responses = responses[start:end]
            
            data = []
            for response in page_responses:
                item = {
                    'id': str(response.id),
                    'submitted_at': response.submitted_at.isoformat(),
                    'review': response.review[:100] + '...' if response.review else 'No review',
                    'sentiment': 'N/A',
                    'confidence': 0
                }
                
                try:
                    analysis = response.sentiment_analysis
                    item['sentiment'] = analysis.sentiment_label
                    item['confidence'] = analysis.confidence
                except SentimentAnalysis.DoesNotExist:
                    pass
                    
                data.append(item)
            
            return Response({
                'count': total_count,
                'results': data,
                'total_pages': (total_count + page_size - 1) // page_size
            })
            
        except Exception as e:
            logger.error(f"Public results failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

