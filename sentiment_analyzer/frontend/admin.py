from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    QuestionnaireSection, QuestionnaireQuestion, 
    QuestionnaireResponse, QuestionResponse, SectionScore,
    SpecialQuestionnaire, SpecialQuestionnaireResponse, 
    SpecialQuestionResponse, SpecialSectionScore,
    MLTopicAnalysis, MLInsight
)

@admin.register(QuestionnaireSection)
class QuestionnaireSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'question_count']
    ordering = ['order']
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

@admin.register(QuestionnaireQuestion)
class QuestionnaireQuestionAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'section', 'order']
    list_filter = ['section']
    ordering = ['section__order', 'order']
    
    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Question'

@admin.register(QuestionnaireResponse)
class QuestionnaireResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'submitted_at', 'is_complete', 'section_count']
    list_filter = ['is_complete', 'submitted_at']
    ordering = ['-submitted_at']
    
    def section_count(self, obj):
        return obj.section_scores.count()
    section_count.short_description = 'Sections'

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['response', 'question_short', 'score']
    list_filter = ['score', 'question__section']
    
    def question_short(self, obj):
        return obj.question.text[:30] + '...' if len(obj.question.text) > 30 else obj.question.text
    question_short.short_description = 'Question'

@admin.register(SectionScore)
class SectionScoreAdmin(admin.ModelAdmin):
    list_display = ['response', 'section', 'average_score', 'total_questions']
    list_filter = ['section']
    ordering = ['-response__submitted_at']

@admin.register(SpecialQuestionnaire)
class SpecialQuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'expires_at', 'status', 'response_count', 'unique_url_link']
    list_filter = ['is_active', 'created_at', 'expires_at', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['unique_token', 'created_at', 'current_responses']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'created_by')
        }),
        ('Settings', {
            'fields': ('expires_at', 'max_responses', 'is_active')
        }),
        ('System Information', {
            'fields': ('unique_token', 'created_at', 'current_responses'),
            'classes': ('collapse',)
        }),
    )
    
    def status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif not obj.is_active:
            return format_html('<span style="color: orange;">Inactive</span>')
        elif obj.current_responses >= obj.max_responses:
            return format_html('<span style="color: red;">Full</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')
    status.short_description = 'Status'
    
    def response_count(self, obj):
        return f"{obj.current_responses} / {obj.max_responses}"
    response_count.short_description = 'Responses'
    
    def unique_url_link(self, obj):
        url = f"http://localhost:8000{obj.unique_url}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.unique_token)
    unique_url_link.short_description = 'Unique URL'

@admin.register(SpecialQuestionnaireResponse)
class SpecialQuestionnaireResponseAdmin(admin.ModelAdmin):
    list_display = ['questionnaire', 'submitted_at', 'is_complete', 'ip_address', 'section_count']
    list_filter = ['is_complete', 'submitted_at', 'questionnaire']
    search_fields = ['ip_address', 'review']
    readonly_fields = ['submitted_at', 'ip_address', 'user_agent']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Response Information', {
            'fields': ('questionnaire', 'is_complete', 'review')
        }),
        ('Technical Details', {
            'fields': ('submitted_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def section_count(self, obj):
        return obj.section_scores.count()
    section_count.short_description = 'Sections'

@admin.register(SpecialQuestionResponse)
class SpecialQuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['response', 'question_short', 'score']
    list_filter = ['score', 'question__section']
    
    def question_short(self, obj):
        return obj.question.text[:30] + '...' if len(obj.question.text) > 30 else obj.question.text
    question_short.short_description = 'Question'

@admin.register(SpecialSectionScore)
class SpecialSectionScoreAdmin(admin.ModelAdmin):
    list_display = ['response', 'section', 'average_score', 'total_questions']
    list_filter = ['section']
    ordering = ['-response__submitted_at']

@admin.register(MLTopicAnalysis)
class MLTopicAnalysisAdmin(admin.ModelAdmin):
    list_display = ['response', 'section', 'topic_keywords_short', 'topic_contribution_score', 'sentiment_score']
    list_filter = ['section', 'analysis_timestamp']
    search_fields = ['topic_keywords']
    readonly_fields = ['analysis_timestamp']
    ordering = ['-topic_contribution_score']
    
    def topic_keywords_short(self, obj):
        return obj.topic_keywords[:30] + '...' if len(obj.topic_keywords) > 30 else obj.topic_keywords
    topic_keywords_short.short_description = 'Topic Keywords'

@admin.register(MLInsight)
class MLInsightAdmin(admin.ModelAdmin):
    list_display = ['response', 'insight_type', 'insight_text_short', 'confidence_score', 'generated_at']
    list_filter = ['insight_type', 'generated_at']
    search_fields = ['insight_text']
    readonly_fields = ['generated_at']
    ordering = ['-confidence_score', '-generated_at']
    
    def insight_text_short(self, obj):
        return obj.insight_text[:50] + '...' if len(obj.insight_text) > 50 else obj.insight_text
    insight_text_short.short_description = 'Insight'
