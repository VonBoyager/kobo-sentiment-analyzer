from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import hashlib
import secrets

from .models import APIToken, APIRequest, APILog, APIConfiguration, APIVersion
from .serializers import (
    UserSerializer, QuestionnaireResponseSerializer, CompleteAnalysisSerializer,
    SentimentAnalysisSerializer, TopicAnalysisSerializer, SectionTopicCorrelationSerializer,
    MLModelSerializer, TrainingDataSerializer, UserFeedbackSerializer,
    TenantSerializer, TenantFileSerializer, TenantModelSerializer, TenantUserSerializer,
    APITokenSerializer, APIRequestSerializer, APILogSerializer,
    APIConfigurationSerializer, APIVersionSerializer, APIStatsSerializer, MLStatsSerializer
)
from frontend.models import QuestionnaireResponse, QuestionnaireSection, QuestionnaireQuestion
from ml_analysis.models import SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation, MLModel, TrainingData, UserFeedback
from tenants.models import Tenant, TenantFile, TenantModel, TenantUser

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

class QuestionnaireResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for questionnaire responses"""
    queryset = QuestionnaireResponse.objects.all()
    serializer_class = QuestionnaireResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return QuestionnaireResponse.objects.filter(user=self.request.user)
    
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

