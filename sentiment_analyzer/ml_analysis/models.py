from django.db import models
from django.contrib.auth.models import User
from frontend.models import QuestionnaireResponse
import uuid

class SentimentAnalysis(models.Model):
    """Model for storing VADER sentiment analysis results"""
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.OneToOneField(QuestionnaireResponse, on_delete=models.CASCADE, related_name='sentiment_analysis')
    
    # VADER scores
    compound_score = models.FloatField(help_text="VADER compound score (-1 to 1)")
    positive_score = models.FloatField(help_text="VADER positive score (0 to 1)")
    negative_score = models.FloatField(help_text="VADER negative score (0 to 1)")
    neutral_score = models.FloatField(help_text="VADER neutral score (0 to 1)")
    
    # Classified sentiment
    sentiment_label = models.CharField(max_length=10, choices=SENTIMENT_CHOICES)
    confidence = models.FloatField(help_text="Confidence score for sentiment classification")
    
    # Analysis metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    text_length = models.PositiveIntegerField(help_text="Length of analyzed text")
    
    class Meta:
        ordering = ['-analyzed_at']
    
    def __str__(self):
        return f"{self.response.user.username} - {self.sentiment_label} ({self.confidence:.2f})"

class TopicAnalysis(models.Model):
    """Model for storing BERTopic analysis results"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='topic_analyses')
    
    # Topic information
    topic_id = models.IntegerField(help_text="BERTopic topic ID")
    topic_name = models.CharField(max_length=200, help_text="Generated topic name")
    topic_keywords = models.JSONField(help_text="Top keywords for this topic")
    topic_probability = models.FloatField(help_text="Probability of this topic in the text")
    
    # Topic metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-topic_probability']
        unique_together = ['response', 'topic_id']
    
    def __str__(self):
        return f"{self.response.user.username} - Topic {self.topic_id}: {self.topic_name}"

class SectionTopicCorrelation(models.Model):
    """Model for storing correlations between topics and questionnaire sections"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Section information
    section_name = models.CharField(max_length=100, help_text="Questionnaire section name")
    section_id = models.IntegerField(help_text="Questionnaire section ID")
    
    # Topic information
    topic_name = models.CharField(max_length=200, help_text="Topic name")
    topic_id = models.IntegerField(help_text="Topic ID")
    
    # Correlation metrics
    correlation_score = models.FloatField(help_text="Correlation between topic and section score")
    negative_correlation = models.BooleanField(default=False, help_text="True if topic correlates with low scores")
    sample_size = models.PositiveIntegerField(help_text="Number of samples used for correlation")
    
    # Keywords for this topic (from TF-IDF analysis)
    keywords = models.JSONField(default=list, help_text="Top keywords for this topic (excluding common words)")
    
    # Analysis metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-correlation_score']
        unique_together = ['section_id', 'topic_id']
    
    def __str__(self):
        return f"{self.section_name} - {self.topic_name} ({self.correlation_score:.3f})"

class MLModel(models.Model):
    """Model for storing trained ML models"""
    MODEL_TYPES = [
        ('random_forest', 'Random Forest'),
        ('naive_bayes', 'Naive Bayes'),
        ('bertopic', 'BERTopic'),
        ('vader', 'VADER'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Model name")
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=50, default='1.0')
    
    # Model storage
    model_file = models.FileField(upload_to='ml_models/', help_text="Serialized model file")
    model_config = models.JSONField(help_text="Model configuration parameters")
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True, help_text="Model accuracy")
    precision = models.FloatField(null=True, blank=True, help_text="Model precision")
    recall = models.FloatField(null=True, blank=True, help_text="Model recall")
    f1_score = models.FloatField(null=True, blank=True, help_text="Model F1 score")
    
    # Model metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.model_type}) - v{self.version}"

class TrainingData(models.Model):
    """Model for storing training data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Text data
    text = models.TextField(help_text="Training text")
    sentiment_label = models.CharField(max_length=10, choices=SentimentAnalysis.SENTIMENT_CHOICES)
    
    # Section scores (for correlation training)
    section_scores = models.JSONField(help_text="Dictionary of section scores")
    
    # Metadata
    source = models.CharField(max_length=100, default='manual', help_text="Source of training data")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when record was last updated")
    is_verified = models.BooleanField(default=False, help_text="Whether data has been verified")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.text[:50]}... - {self.sentiment_label}"

class UserFeedback(models.Model):
    """Model for storing user feedback on ML analysis"""
    FEEDBACK_TYPES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
        ('partially_helpful', 'Partially Helpful'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ml_feedback')
    response = models.ForeignKey(QuestionnaireResponse, on_delete=models.CASCADE, related_name='feedback')
    
    # Feedback content
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    feedback_text = models.TextField(blank=True, help_text="Additional feedback text")
    
    # Analysis feedback
    sentiment_accuracy = models.BooleanField(null=True, help_text="Was sentiment analysis accurate?")
    topic_relevance = models.BooleanField(null=True, help_text="Were topics relevant?")
    section_correlation = models.BooleanField(null=True, help_text="Were section correlations helpful?")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.feedback_type} - {self.response.id}"