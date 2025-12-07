from rest_framework import serializers
from django.contrib.auth.models import User
from .models import APIToken, APIRequest, APILog, APIConfiguration, APIVersion
from frontend.models import (
    QuestionnaireResponse, QuestionResponse, SectionScore,
    QuestionnaireSection, QuestionnaireQuestion, SpecialQuestionnaire
)
from ml_analysis.models import (
    SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation,
    MLModel, TrainingData, UserFeedback
)
from tenants.models import Tenant, TenantFile, TenantModel, TenantUser

# User serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

# Questionnaire serializers
class QuestionnaireSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionnaireSection
        fields = ['id', 'name', 'description', 'order']

class QuestionnaireQuestionSerializer(serializers.ModelSerializer):
    section = QuestionnaireSectionSerializer(read_only=True)
    
    class Meta:
        model = QuestionnaireQuestion
        fields = ['id', 'section', 'text', 'order']

class SpecialQuestionnaireSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    unique_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = SpecialQuestionnaire
        fields = [
            'id', 'title', 'description', 'unique_token', 'created_at',
            'expires_at', 'is_active', 'max_responses', 'current_responses',
            'created_by', 'unique_url', 'is_expired'
        ]
        read_only_fields = ['unique_token', 'created_at', 'current_responses', 'created_by']

    def get_unique_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.unique_url)
        return obj.unique_url

class QuestionResponseSerializer(serializers.ModelSerializer):
    question = QuestionnaireQuestionSerializer(read_only=True)
    
    class Meta:
        model = QuestionResponse
        fields = ['id', 'question', 'score']

class SectionScoreSerializer(serializers.ModelSerializer):
    section = QuestionnaireSectionSerializer(read_only=True)
    
    class Meta:
        model = SectionScore
        fields = ['id', 'section', 'average_score', 'total_questions']

class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    question_responses = QuestionResponseSerializer(many=True, read_only=True)
    section_scores = SectionScoreSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionnaireResponse
        fields = [
            'id', 'user', 'submitted_at', 'updated_at', 'is_complete', 'review',
            'question_responses', 'section_scores'
        ]
        read_only_fields = ['id', 'submitted_at', 'updated_at']

# ML Analysis serializers
class SentimentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentAnalysis
        fields = [
            'id', 'compound_score', 'positive_score', 'negative_score', 
            'neutral_score', 'sentiment_label', 'confidence', 
            'analyzed_at', 'text_length'
        ]
        read_only_fields = ['id', 'analyzed_at']

class TopicAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicAnalysis
        fields = [
            'id', 'topic_id', 'topic_name', 'topic_keywords', 
            'topic_probability', 'analyzed_at'
        ]
        read_only_fields = ['id', 'analyzed_at']

class SectionTopicCorrelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionTopicCorrelation
        fields = [
            'id', 'section_name', 'section_id', 'topic_name', 'topic_id',
            'correlation_score', 'negative_correlation', 'sample_size',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MLModelSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'model_type', 'version', 'model_config',
            'accuracy', 'precision', 'recall', 'f1_score',
            'is_active', 'created_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at']

class TrainingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingData
        fields = [
            'id', 'text', 'sentiment_label', 'section_scores',
            'source', 'created_at', 'updated_at', 'is_verified'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserFeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserFeedback
        fields = [
            'id', 'user', 'feedback_type', 'feedback_text',
            'sentiment_accuracy', 'topic_relevance', 'section_correlation',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Tenant serializers
class TenantSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'description', 'owner',
            'created_at', 'updated_at', 'is_active', 'database_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'database_name']

class TenantFileSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TenantFile
        fields = [
            'id', 'tenant', 'name', 'file_type', 'file',
            'description', 'uploaded_by', 'uploaded_at', 'file_size'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_size']

class TenantModelSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TenantModel
        fields = [
            'id', 'tenant', 'name', 'model_type', 'model_file',
            'description', 'version', 'accuracy', 'created_by',
            'created_at', 'is_active', 'training_data_size',
            'features_count', 'last_trained'
        ]
        read_only_fields = ['id', 'created_at']

class TenantUserSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id', 'tenant', 'user', 'role', 'joined_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at']

# API Management serializers
class APITokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = APIToken
        fields = [
            'id', 'user', 'name', 'token', 'is_active',
            'created_at', 'last_used', 'expires_at'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'last_used']
        extra_kwargs = {
            'token': {'write_only': True}
        }

class APIRequestSerializer(serializers.ModelSerializer):
    token = APITokenSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = APIRequest
        fields = [
            'id', 'token', 'user', 'endpoint', 'method',
            'status_code', 'response_time', 'ip_address',
            'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class APILogSerializer(serializers.ModelSerializer):
    request = APIRequestSerializer(read_only=True)
    
    class Meta:
        model = APILog
        fields = [
            'id', 'request', 'level', 'message', 'data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class APIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIConfiguration
        fields = [
            'id', 'name', 'value', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class APIVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIVersion
        fields = [
            'id', 'version', 'is_current', 'is_deprecated',
            'deprecation_date', 'end_of_life_date', 'changelog',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Combined analysis serializers
class CompleteAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for complete analysis data including sentiment, topics, and correlations"""
    sentiment_analysis = SentimentAnalysisSerializer(read_only=True)
    topic_analyses = TopicAnalysisSerializer(many=True, read_only=True)
    section_scores = SectionScoreSerializer(many=True, read_only=True)
    question_responses = QuestionResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionnaireResponse
        fields = [
            'id', 'user', 'submitted_at', 'updated_at', 'is_complete', 'review',
            'sentiment_analysis', 'topic_analyses', 'section_scores',
            'question_responses'
        ]

# Statistics serializers
class APIStatsSerializer(serializers.Serializer):
    """Serializer for API statistics"""
    total_requests = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    requests_today = serializers.IntegerField()
    active_tokens = serializers.IntegerField()
    total_users = serializers.IntegerField()

class MLStatsSerializer(serializers.Serializer):
    """Serializer for ML analysis statistics"""
    total_analyses = serializers.IntegerField()
    sentiment_analyses = serializers.IntegerField()
    topic_analyses = serializers.IntegerField()
    correlation_analyses = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    most_common_sentiment = serializers.CharField()
    total_topics = serializers.IntegerField()
