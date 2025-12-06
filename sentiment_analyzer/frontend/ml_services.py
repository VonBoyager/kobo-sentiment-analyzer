from django.db import models
from django.utils import timezone
from .models import (
    QuestionnaireResponse, QuestionnaireSection, QuestionResponse, 
    SectionScore, MLTopicAnalysis, MLInsight
)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MLAnalysisService:
    """Service for performing machine learning analysis on questionnaire responses"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.topic_keywords = {
            'Compensation & Benefits': ['salary', 'pay', 'compensation', 'benefits', 'insurance', 'retirement', 'bonus'],
            'Work-Life Balance': ['workload', 'schedule', 'flexible', 'vacation', 'leave', 'balance', 'time'],
            'Work Environment': ['safe', 'comfortable', 'tools', 'resources', 'culture', 'inclusive', 'workplace'],
            'Career Development': ['growth', 'training', 'development', 'skills', 'career', 'progression', 'learning'],
            'Management & Leadership': ['manager', 'leadership', 'communication', 'support', 'concerns', 'guidance'],
            'Job Security & Stability': ['secure', 'stable', 'financial', 'changes', 'organization', 'job security'],
            'Colleague & Team Dynamics': ['team', 'colleagues', 'collaboration', 'respect', 'conflicts', 'relationships'],
            'Autonomy & Role Clarity': ['responsibilities', 'autonomy', 'decisions', 'role', 'skills', 'expertise'],
            'Recognition & Appreciation': ['acknowledged', 'appreciated', 'evaluations', 'rewards', 'recognition', 'efforts'],
            'Organizational Factors': ['mission', 'values', 'innovation', 'adaptability', 'ethics', 'responsibility']
        }
    
    def analyze_response(self, response_id):
        """Perform comprehensive ML analysis on a questionnaire response"""
        try:
            response = QuestionnaireResponse.objects.get(id=response_id)
            
            # Clear existing analyses
            MLTopicAnalysis.objects.filter(response=response).delete()
            MLInsight.objects.filter(response=response).delete()
            
            # Get all responses for comparison
            all_responses = QuestionnaireResponse.objects.filter(is_complete=True)
            
            # Perform topic analysis
            self._analyze_topics(response, all_responses)
            
            # Generate insights
            self._generate_insights(response, all_responses)
            
            logger.info(f"ML analysis completed for response {response_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in ML analysis for response {response_id}: {str(e)}")
            return False
    
    def _analyze_topics(self, response, all_responses):
        """Analyze topic contributions to each section"""
        try:
            # Get section scores for this response
            section_scores = SectionScore.objects.filter(response=response)
            
            for section_score in section_scores:
                section = section_score.section
                
                # Get question responses for this section
                question_responses = QuestionResponse.objects.filter(
                    response=response,
                    question__section=section
                )
                
                if not question_responses.exists():
                    continue
                
                # Calculate topic contribution
                topic_contribution = self._calculate_topic_contribution(
                    section, question_responses, all_responses
                )
                
                # Analyze sentiment for this section
                sentiment_score = self._analyze_section_sentiment(
                    section, question_responses
                )
                
                # Create ML topic analysis record
                MLTopicAnalysis.objects.create(
                    response=response,
                    section=section,
                    topic_keywords=', '.join(self.topic_keywords.get(section.name, [])),
                    topic_contribution_score=topic_contribution,
                    sentiment_score=sentiment_score
                )
                
        except Exception as e:
            logger.error(f"Error in topic analysis: {str(e)}")
    
    def _calculate_topic_contribution(self, section, question_responses, all_responses):
        """Calculate how much this topic contributes to the section score"""
        try:
            # Get average scores for this section across all responses
            all_section_scores = SectionScore.objects.filter(section=section)
            
            if not all_section_scores.exists():
                return 0.5  # Default contribution
            
            # Calculate this response's score vs average
            current_score = sum(qr.score for qr in question_responses) / len(question_responses)
            avg_score = sum(ss.average_score for ss in all_section_scores) / len(all_section_scores)
            
            # Calculate contribution based on deviation from average
            if avg_score > 0:
                contribution = min(1.0, max(0.0, (current_score - avg_score) / avg_score + 0.5))
            else:
                contribution = 0.5
            
            return contribution
            
        except Exception as e:
            logger.error(f"Error calculating topic contribution: {str(e)}")
            return 0.5
    
    def _analyze_section_sentiment(self, section, question_responses):
        """Analyze sentiment for a specific section"""
        try:
            # Combine review text with question context
            text_to_analyze = ""
            
            # Add review if available
            if question_responses.first().response.review:
                text_to_analyze += question_responses.first().response.review + " "
            
            # Add section context
            text_to_analyze += f"{section.name} {section.description} "
            
            # Add question context
            for qr in question_responses:
                text_to_analyze += f"{qr.question.text} "
            
            # Perform sentiment analysis
            sentiment_scores = self.sentiment_analyzer.polarity_scores(text_to_analyze)
            
            # Return compound score (-1 to 1)
            return sentiment_scores['compound']
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return 0.0
    
    def _generate_insights(self, response, all_responses):
        """Generate ML insights and recommendations"""
        try:
            # Get topic analyses for this response
            topic_analyses = MLTopicAnalysis.objects.filter(response=response)
            
            if not topic_analyses.exists():
                return
            
            # Find the section with highest contribution
            top_contribution = topic_analyses.order_by('-topic_contribution_score').first()
            
            if top_contribution:
                # Generate topic contribution insight
                insight_text = (
                    f"The topic '{top_contribution.topic_keywords}' contributed the most "
                    f"to your {top_contribution.section.name} section score "
                    f"(contribution: {top_contribution.topic_contribution_score:.2f}). "
                    f"This suggests that {top_contribution.section.name.lower()} is a key "
                    f"factor in your overall satisfaction."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='topic_contribution',
                    insight_text=insight_text,
                    confidence_score=top_contribution.topic_contribution_score,
                    related_sections=[top_contribution.section]
                )
            
            # Generate sentiment trend insights
            self._generate_sentiment_insights(response, topic_analyses)
            
            # Generate section correlation insights
            self._generate_correlation_insights(response, topic_analyses)
            
            # Generate improvement suggestions
            self._generate_improvement_suggestions(response, topic_analyses)
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
    
    def _generate_sentiment_insights(self, response, topic_analyses):
        """Generate insights based on sentiment analysis"""
        try:
            positive_sections = []
            negative_sections = []
            low_score_sections = []
            
            for analysis in topic_analyses:
                if analysis.sentiment_score > 0.1:
                    positive_sections.append(analysis.section.name)
                elif analysis.sentiment_score < -0.1:
                    negative_sections.append(analysis.section.name)
                
                # Also check for low scores (1-2 ratings)
                section_score = SectionScore.objects.filter(
                    response=response, 
                    section=analysis.section
                ).first()
                
                if section_score and section_score.average_score <= 2.0:
                    low_score_sections.append(analysis.section.name)
            
            if positive_sections:
                insight_text = (
                    f"Your responses show positive sentiment in: {', '.join(positive_sections)}. "
                    f"These areas appear to be strengths in your work experience."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='sentiment_trend',
                    insight_text=insight_text,
                    confidence_score=0.8,
                    related_sections=[analysis.section for analysis in topic_analyses 
                                    if analysis.section.name in positive_sections]
                )
            
            if negative_sections:
                insight_text = (
                    f"Your responses indicate areas for improvement in: {', '.join(negative_sections)}. "
                    f"Consider discussing these topics with your manager or HR."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='improvement_suggestion',
                    insight_text=insight_text,
                    confidence_score=0.7,
                    related_sections=[analysis.section for analysis in topic_analyses 
                                    if analysis.section.name in negative_sections]
                )
            
            # Generate specific insights about topics correlated with low scores
            if low_score_sections:
                self._generate_low_score_correlation_insights(response, topic_analyses, low_score_sections)
                
        except Exception as e:
            logger.error(f"Error generating sentiment insights: {str(e)}")
    
    def _generate_low_score_correlation_insights(self, response, topic_analyses, low_score_sections):
        """Generate insights about topics that correlate with low scores"""
        try:
            # Find topics that appear in low-scoring sections
            correlated_topics = []
            
            for analysis in topic_analyses:
                if analysis.section.name in low_score_sections:
                    # Extract key topics from the keywords
                    topics = analysis.topic_keywords.split(', ')
                    correlated_topics.extend(topics[:3])  # Take top 3 topics
            
            if correlated_topics:
                # Remove duplicates and create insight
                unique_topics = list(set(correlated_topics))
                
                insight_text = (
                    f"These topics correlated to your low ratings: {', '.join(unique_topics[:5])}. "
                    f"This suggests that issues in these areas significantly impact your overall satisfaction. "
                    f"Focus on addressing these specific topics to improve your work experience."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='topic_contribution',
                    insight_text=insight_text,
                    confidence_score=0.85,
                    related_sections=[analysis.section for analysis in topic_analyses 
                                    if analysis.section.name in low_score_sections]
                )
                
        except Exception as e:
            logger.error(f"Error generating low score correlation insights: {str(e)}")
    
    def _generate_correlation_insights(self, response, topic_analyses):
        """Generate insights about section correlations"""
        try:
            if len(topic_analyses) < 2:
                return
            
            # Find sections with similar contribution scores
            scores = [(analysis.section.name, analysis.topic_contribution_score) 
                     for analysis in topic_analyses]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Check for strong correlations
            top_sections = scores[:3]
            if len(top_sections) >= 2:
                insight_text = (
                    f"Your responses show strong performance across multiple areas: "
                    f"{', '.join([section[0] for section in top_sections[:2]])}. "
                    f"This suggests a well-rounded work experience."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='section_correlation',
                    insight_text=insight_text,
                    confidence_score=0.75,
                    related_sections=[analysis.section for analysis in topic_analyses 
                                    if analysis.section.name in [s[0] for s in top_sections[:2]]]
                )
                
        except Exception as e:
            logger.error(f"Error generating correlation insights: {str(e)}")
    
    def _generate_improvement_suggestions(self, response, topic_analyses):
        """Generate improvement suggestions based on analysis"""
        try:
            # Find section with lowest contribution
            lowest_contribution = topic_analyses.order_by('topic_contribution_score').first()
            
            if lowest_contribution and lowest_contribution.topic_contribution_score < 0.4:
                section_name = lowest_contribution.section.name
                
                # Generate specific suggestions based on section
                suggestions = {
                    'Compensation & Benefits': 'Consider discussing salary review or benefits package with HR',
                    'Work-Life Balance': 'Explore flexible work arrangements or workload management strategies',
                    'Work Environment': 'Address workplace comfort or resource needs with your manager',
                    'Career Development': 'Request additional training opportunities or career planning discussions',
                    'Management & Leadership': 'Schedule regular one-on-ones with your manager',
                    'Job Security & Stability': 'Seek more information about company stability and future plans',
                    'Colleague & Team Dynamics': 'Participate in team-building activities or conflict resolution',
                    'Autonomy & Role Clarity': 'Request clearer role definitions or more decision-making authority',
                    'Recognition & Appreciation': 'Discuss recognition programs or performance feedback processes',
                    'Organizational Factors': 'Engage more with company mission and values initiatives'
                }
                
                suggestion = suggestions.get(section_name, 'Consider discussing this area with your manager')
                
                insight_text = (
                    f"Based on your responses, {section_name} shows room for improvement. "
                    f"Suggestion: {suggestion}."
                )
                
                MLInsight.objects.create(
                    response=response,
                    insight_type='improvement_suggestion',
                    insight_text=insight_text,
                    confidence_score=0.6,
                    related_sections=[lowest_contribution.section]
                )
                
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")

def analyze_response_ml(response_id):
    """Convenience function to analyze a response with ML"""
    service = MLAnalysisService()
    return service.analyze_response(response_id)
