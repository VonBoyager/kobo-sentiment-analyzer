from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

class QuestionnaireSection(models.Model):
    """Model for questionnaire sections"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name

class QuestionnaireQuestion(models.Model):
    """Model for individual questions within sections"""
    section = models.ForeignKey(QuestionnaireSection, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['section__order', 'order']
    
    def __str__(self):
        return f"{self.section.name}: {self.text[:50]}..."

class QuestionnaireResponse(models.Model):
    """Model for storing questionnaire responses (unified for both regular and special questionnaires)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questionnaire_responses', null=True, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now, help_text="Timestamp when questionnaire was first submitted")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when record was last updated")
    is_complete = models.BooleanField(default=False)
    review = models.TextField(help_text="Additional review or feedback", default="")
    
    # Fields for special questionnaires
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_special_response = models.BooleanField(default=False, help_text="True if this is from a special questionnaire")
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"Anonymous - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"

class QuestionResponse(models.Model):
    """Model for individual question responses"""
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='question_responses')
    question = models.ForeignKey(QuestionnaireQuestion, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
    )
    
    class Meta:
        unique_together = ['response', 'question']
    
    def __str__(self):
        return f"{self.response.user.username} - {self.question.text[:30]}... - Score: {self.score}"

class SectionScore(models.Model):
    """Model for storing calculated section scores"""
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='section_scores')
    section = models.ForeignKey(QuestionnaireSection, on_delete=models.CASCADE)
    average_score = models.FloatField()
    total_questions = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ['response', 'section']
    
    def __str__(self):
        return f"{self.response.user.username} - {self.section.name}: {self.average_score:.2f}"

class SpecialQuestionnaire(models.Model):
    """Model for special time-limited questionnaires with unique URLs"""
    title = models.CharField(max_length=200, default="Employee Satisfaction Survey")
    description = models.TextField(blank=True, help_text="Instructions for the questionnaire")
    unique_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this questionnaire expires")
    is_active = models.BooleanField(default=True)
    max_responses = models.PositiveIntegerField(default=1, help_text="Maximum number of responses allowed")
    current_responses = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_questionnaires')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.unique_token}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_available(self):
        return self.is_active and not self.is_expired and self.current_responses < self.max_responses
    
    @property
    def unique_url(self):
        return f"/special-questionnaire/{self.unique_token}/"

class SpecialQuestionnaireResponse(models.Model):
    """Model for responses to special questionnaires"""
    questionnaire = models.ForeignKey(SpecialQuestionnaire, on_delete=models.CASCADE, related_name='responses')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    review = models.TextField(help_text="Additional review or feedback", default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Response to {self.questionnaire.title} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"

class SpecialQuestionResponse(models.Model):
    """Model for individual question responses in special questionnaires"""
    response = models.ForeignKey(SpecialQuestionnaireResponse, on_delete=models.CASCADE, related_name='question_responses')
    question = models.ForeignKey(QuestionnaireQuestion, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
    )
    
    class Meta:
        unique_together = ['response', 'question']
    
    def __str__(self):
        return f"{self.response.questionnaire.title} - {self.question.text[:30]}... - Score: {self.score}"

class SpecialSectionScore(models.Model):
    """Model for storing calculated section scores in special questionnaires"""
    response = models.ForeignKey(SpecialQuestionnaireResponse, on_delete=models.CASCADE, related_name='section_scores')
    section = models.ForeignKey(QuestionnaireSection, on_delete=models.CASCADE)
    average_score = models.FloatField()
    total_questions = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ['response', 'section']
    
    def __str__(self):
        return f"{self.response.questionnaire.title} - {self.section.name}: {self.average_score:.2f}"

class MLTopicAnalysis(models.Model):
    """Model for storing ML topic analysis results"""
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='ml_topic_analyses')
    section = models.ForeignKey(QuestionnaireSection, on_delete=models.CASCADE)
    topic_keywords = models.TextField(help_text="Comma-separated keywords for the main topic")
    topic_contribution_score = models.FloatField(help_text="How much this topic contributes to the section score")
    sentiment_score = models.FloatField(help_text="Sentiment analysis score for this topic")
    analysis_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-topic_contribution_score']
    
    def __str__(self):
        return f"{self.response} - {self.section.name}: {self.topic_keywords[:30]}..."

class MLInsight(models.Model):
    """Model for storing ML-generated insights and recommendations"""
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=50, choices=[
        ('topic_contribution', 'Topic Contribution'),
        ('sentiment_trend', 'Sentiment Trend'),
        ('section_correlation', 'Section Correlation'),
        ('improvement_suggestion', 'Improvement Suggestion')
    ])
    insight_text = models.TextField(help_text="The generated insight text")
    confidence_score = models.FloatField(help_text="ML confidence score (0-1)")
    related_sections = models.ManyToManyField(QuestionnaireSection, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-confidence_score', '-generated_at']
    
    def __str__(self):
        return f"{self.response} - {self.insight_type}: {self.insight_text[:50]}..."