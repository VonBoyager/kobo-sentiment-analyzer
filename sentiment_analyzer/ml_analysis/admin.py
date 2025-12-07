from django.contrib import admin
from .models import (
    SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation,
    MLModel, TrainingData, UserFeedback
)

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['response', 'sentiment_label', 'confidence', 'compound_score', 'analyzed_at']
    list_filter = ['sentiment_label', 'analyzed_at']
    search_fields = ['response__user__username', 'response__user__email']
    ordering = ['-analyzed_at']
    readonly_fields = ['analyzed_at']

@admin.register(TopicAnalysis)
class TopicAnalysisAdmin(admin.ModelAdmin):
    list_display = ['response', 'topic_id', 'topic_name', 'topic_probability', 'analyzed_at']
    list_filter = ['topic_id', 'analyzed_at']
    search_fields = ['response__user__username', 'topic_name']
    ordering = ['-topic_probability']
    readonly_fields = ['analyzed_at']

@admin.register(SectionTopicCorrelation)
class SectionTopicCorrelationAdmin(admin.ModelAdmin):
    list_display = ['section_name', 'topic_name', 'correlation_score', 'negative_correlation', 'sample_size']
    list_filter = ['section_name', 'negative_correlation', 'created_at']
    search_fields = ['section_name', 'topic_name']
    ordering = ['-correlation_score']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'version', 'is_active', 'accuracy', 'created_at']
    list_filter = ['model_type', 'is_active', 'created_at']
    search_fields = ['name', 'version']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

@admin.register(TrainingData)
class TrainingDataAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'sentiment_label', 'source', 'is_verified', 'created_at']
    list_filter = ['sentiment_label', 'source', 'is_verified', 'created_at']
    search_fields = ['text']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Text'

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'response', 'feedback_type', 'sentiment_accuracy', 'topic_relevance', 'created_at']
    list_filter = ['feedback_type', 'sentiment_accuracy', 'topic_relevance', 'created_at']
    search_fields = ['user__username', 'feedback_text']
    ordering = ['-created_at']
    readonly_fields = ['created_at']