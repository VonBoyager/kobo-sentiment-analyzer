from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Avg, Count
from datetime import timedelta
import logging
import pandas as pd
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)
from .models import (
    QuestionnaireSection, QuestionnaireQuestion, 
    QuestionnaireResponse, QuestionResponse, SectionScore,
    SpecialQuestionnaire, SpecialQuestionnaireResponse, 
    SpecialQuestionResponse, SpecialSectionScore,
    MLTopicAnalysis, MLInsight
)
from .ml_services import analyze_response_ml
from ml_analysis.models import SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation
from ml_analysis.services import MLPipeline

def home(request):
    """Serve React frontend application"""
    import os
    from django.conf import settings
    from django.http import HttpResponse
    
    # Path to React app's index.html (built version)
    # Check multiple possible locations
    possible_paths = [
        os.path.join('/app', 'sentiment_analyzer', 'frontend', 'static', 'frontend', 'dist', 'index.html'),
        os.path.join('/app', 'frontend', 'dist', 'index.html'),
        os.path.join(settings.BASE_DIR, 'frontend', 'static', 'frontend', 'dist', 'index.html'),
        os.path.join(settings.BASE_DIR.parent, 'frontend', 'static', 'frontend', 'dist', 'index.html'),
    ]
    
    react_index_path = None
    for path in possible_paths:
        if os.path.exists(path):
            react_index_path = path
            logger.info(f"Serving React app from: {react_index_path}")
            break
    
    # If React app exists, serve it
    if react_index_path:
        try:
            with open(react_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Update asset paths to use /static/ prefix
            content = content.replace('src="/assets/', 'src="/static/frontend/dist/assets/')
            content = content.replace('href="/assets/', 'href="/static/frontend/dist/assets/')
            return HttpResponse(content, content_type='text/html')
        except Exception as e:
            logger.error(f"Error serving React app: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Fallback to old Django views
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')
    return redirect('frontend:login')

def dashboard(request):
    """Main dashboard after login - merged with ML analysis"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
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
    sentiment_breakdown = SentimentAnalysis.objects.filter(
        response__user__username__in=similar_usernames
    ).values('sentiment_label').annotate(count=Count('id'))
    sentiment_dict = {item['sentiment_label']: item['count'] for item in sentiment_breakdown}
    
    # Calculate overall_sentiment_data for charts (format: {positive: count, negative: count, neutral: count})
    overall_sentiment_data = {
        'positive': sentiment_dict.get('positive', 0),
        'negative': sentiment_dict.get('negative', 0),
        'neutral': sentiment_dict.get('neutral', 0)
    }
    
    # Get ML-essential sections for charts
    ml_essential_sections = [
        'Compensation & Benefits',
        'Work-Life Balance',
        'Culture & Values',
        'Diversity & Inclusion',
        'Career Development',
        'Management & Leadership'
    ]
    sections = QuestionnaireSection.objects.filter(name__in=ml_essential_sections).order_by('order', 'id')
    
    # Calculate section_sentiment_data for each section
    # Show sentiment for responses where this section scored in different ranges
    # This makes each section show different results based on section performance
    section_sentiment_data = {}
    for section in sections:
        # Get sentiment for responses where this section scored low (< 3.0)
        # This shows sentiment correlation with poor performance in this section
        from django.db.models import Q
        from frontend.models import SectionScore
        
        # Get responses with low scores in this section
        low_score_section_scores = SectionScore.objects.filter(
            section=section,
            average_score__lt=3.0,
            response__user__username__in=similar_usernames,
            response__is_complete=True
        ).select_related('response', 'response__sentiment_analysis')
        
        # Get responses with high scores in this section
        high_score_section_scores = SectionScore.objects.filter(
            section=section,
            average_score__gte=4.0,
            response__user__username__in=similar_usernames,
            response__is_complete=True
        ).select_related('response', 'response__sentiment_analysis')
        
        # Aggregate sentiment for low-scoring responses in this section
        low_sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for section_score in low_score_section_scores:
            try:
                sentiment = section_score.response.sentiment_analysis
                if sentiment:
                    label = sentiment.sentiment_label
                    low_sentiment_counts[label] = low_sentiment_counts.get(label, 0) + 1
            except:
                continue
        
        # Aggregate sentiment for high-scoring responses in this section
        high_sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for section_score in high_score_section_scores:
            try:
                sentiment = section_score.response.sentiment_analysis
                if sentiment:
                    label = sentiment.sentiment_label
                    high_sentiment_counts[label] = high_sentiment_counts.get(label, 0) + 1
            except:
                continue
        
        # Show combined sentiment: emphasize positive for high scores, negative for low scores
        # This makes each section show different results based on performance
        total_low = sum(low_sentiment_counts.values())
        total_high = sum(high_sentiment_counts.values())
        
        if total_low > 0 or total_high > 0:
            # Weighted combination: more weight to high scores for positive, low scores for negative
            section_sentiment_data[section.name] = {
                'positive': max(0, int(high_sentiment_counts['positive'] * 1.5 + low_sentiment_counts['positive'] * 0.5)),
                'negative': max(0, int(low_sentiment_counts['negative'] * 1.5 + high_sentiment_counts['negative'] * 0.5)),
                'neutral': max(0, int((low_sentiment_counts['neutral'] + high_sentiment_counts['neutral']) * 0.8))
            }
        else:
            # Fallback: use overall sentiment distribution divided by sections
            # Ensure we have meaningful numbers for visualization
            section_sentiment_data[section.name] = {
                'positive': max(10, sentiment_dict.get('positive', 0) // len(sections)),
                'negative': max(10, sentiment_dict.get('negative', 0) // len(sections)),
                'neutral': max(10, sentiment_dict.get('neutral', 0) // len(sections))
            }
        
        logger.debug(f"Section {section.name} sentiment data: {section_sentiment_data[section.name]}")
    
    # Get correlation insights (exclude Feature Importance entries)
    # Lower thresholds to show more correlations: positive > 0.1, negative < -0.1
    # Only get correlations that have keywords (actual topics, not section-based)
    # Prepare keyword lists for template display
    positive_correlations_raw = SectionTopicCorrelation.objects.filter(
        correlation_score__gt=0.1
    ).exclude(
        topic_name__icontains='Feature Importance'
    ).exclude(
        keywords__isnull=True
    ).exclude(
        keywords={}
    ).order_by('-correlation_score')[:10]
    
    negative_correlations_raw = SectionTopicCorrelation.objects.filter(
        correlation_score__lt=-0.1
    ).exclude(
        topic_name__icontains='Feature Importance'
    ).exclude(
        keywords__isnull=True
    ).exclude(
        keywords={}
    ).order_by('correlation_score')[:10]
    
    # Convert keywords dict to list for template display
    positive_correlations = []
    for corr in positive_correlations_raw:
        keywords_list = []
        if corr.keywords:
            if isinstance(corr.keywords, dict):
                # Sort by score (value) and take top 10
                sorted_keywords = sorted(corr.keywords.items(), key=lambda x: x[1], reverse=True)[:10]
                keywords_list = [word for word, score in sorted_keywords]
            elif isinstance(corr.keywords, list):
                keywords_list = corr.keywords[:10]
        positive_correlations.append({
            'correlation': corr,
            'keywords_list': keywords_list
        })
    
    negative_correlations = []
    for corr in negative_correlations_raw:
        keywords_list = []
        if corr.keywords:
            if isinstance(corr.keywords, dict):
                # Sort by score (value) and take top 10
                sorted_keywords = sorted(corr.keywords.items(), key=lambda x: x[1], reverse=True)[:10]
                keywords_list = [word for word, score in sorted_keywords]
            elif isinstance(corr.keywords, list):
                keywords_list = corr.keywords[:10]
        negative_correlations.append({
            'correlation': corr,
            'keywords_list': keywords_list
        })
    
    # Calculate section performance summary (strong/weak sections)
    section_performance_summary = None
    if total_responses > 0:
        from django.db.models import Avg
        from frontend.models import SectionScore
        
        # Calculate average score for each section across all responses
        section_averages = {}
        for section in sections:
            avg_score = SectionScore.objects.filter(
                section=section,
                response__user__username__in=similar_usernames,
                response__is_complete=True
            ).aggregate(avg=Avg('average_score'))['avg']
            
            if avg_score is not None:
                section_averages[section.name] = round(avg_score, 2)
        
        if section_averages:
            # Determine strong (>= 3.0) and weak (< 3.0) sections
            strong_sections = [name for name, score in section_averages.items() if score >= 3.0]
            weak_sections = [name for name, score in section_averages.items() if score < 3.0]
            
            # Generate feedback message
            if len(weak_sections) == len(section_averages):
                # All sections are below average
                feedback_message = "Uh oh, seems like everyone in the company is displeased with everything. All sections are scoring below average, indicating widespread dissatisfaction across all areas of the organization."
                weak_sections_with_scores = [(name, section_averages[name]) for name in weak_sections]
                section_performance_summary = {
                    'message': feedback_message,
                    'strong_sections': [],
                    'weak_sections': weak_sections,
                    'strong_sections_with_scores': [],
                    'weak_sections_with_scores': weak_sections_with_scores,
                    'section_averages': section_averages,
                    'all_below_average': True
                }
            else:
                # Mix of strong and weak sections
                strong_sections_with_scores = [(name, section_averages[name]) for name in strong_sections]
                weak_sections_with_scores = [(name, section_averages[name]) for name in weak_sections]
                
                if strong_sections and weak_sections:
                    feedback_message = f"Your company seems to be strong on these sections: {', '.join(strong_sections)}. However, your company seems to be weak on these sections: {', '.join(weak_sections)}."
                elif strong_sections:
                    feedback_message = f"Your company seems to be strong on these sections: {', '.join(strong_sections)}. Great job maintaining high satisfaction across these areas!"
                else:
                    feedback_message = f"Your company seems to be weak on these sections: {', '.join(weak_sections)}. Consider focusing improvement efforts on these areas."
                
                section_performance_summary = {
                    'message': feedback_message,
                    'strong_sections': strong_sections,
                    'weak_sections': weak_sections,
                    'strong_sections_with_scores': strong_sections_with_scores,
                    'weak_sections_with_scores': weak_sections_with_scores,
                    'section_averages': section_averages,
                    'all_below_average': False
                }
    
    context = {
        'current_time': timezone.now(),
        'user': request.user,
        'latest_response': latest_response,
        'total_responses': total_responses,
        'has_similar_data': has_similar_data,
        'sentiment_analyses': sentiment_analyses,
        'total_topic_analyses': topic_analyses,
        'correlations': correlations,
        'sentiment_breakdown': sentiment_dict,
        'overall_sentiment_data': overall_sentiment_data,
        'section_sentiment_data': section_sentiment_data,
        'sections': sections,
        'has_analysis': False,
        'sentiment_analysis': None,
        'topic_analyses': [],
        'section_insights': {},
        'positive_correlations': positive_correlations,
        'negative_correlations': negative_correlations,
        'has_correlations': SectionTopicCorrelation.objects.exclude(
            topic_name__icontains='Feature Importance'
        ).exists(),
        'section_performance_summary': section_performance_summary
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
        
        # Get section insights - only if response has section scores
        if context['has_analysis']:
            # Check if response has section scores before generating insights
            if latest_response.section_scores.exists():
                try:
                    if 'pipeline' not in locals():
                        pipeline = MLPipeline()
                    context['section_insights'] = pipeline.get_section_insights(latest_response)
                    logger.info(f"Section insights generated: {len(context['section_insights'])} sections")
                except Exception as e:
                    logger.error(f"Error getting section insights: {e}", exc_info=True)
                    context['section_insights'] = {}
            else:
                logger.warning(f"Response {latest_response.id} has no section scores - cannot generate insights. This may be a data issue.")
                # Generate insights with no_data flag for all sections
                context['section_insights'] = {}
                ml_essential_sections = [
                    'Compensation & Benefits',
                    'Work-Life Balance',
                    'Culture & Values',
                    'Diversity & Inclusion',
                    'Career Development',
                    'Management & Leadership'
                ]
                for section_name in ml_essential_sections:
                    context['section_insights'][section_name] = {
                        'score': None,
                        'is_low': False,
                        'negative_topics': [],
                        'recommendations': [],
                        'no_data': True
                    }
    
    # Get global topics from trained BERTopic model
    try:
        if 'pipeline' not in locals():
            pipeline = MLPipeline()
        global_topics = pipeline.topic_analyzer.get_global_topics()
        context['global_topics'] = global_topics if global_topics else []
    except Exception as e:
        logger.error(f"Error getting global topics: {e}")
        context['global_topics'] = []
    
    # Get aggregated topic analyses across all responses (similar to questionnaire results)
    try:
        from collections import defaultdict
        from django.db.models import Avg
        
        # Get all topic analyses from all responses
        all_topic_analyses = MLTopicAnalysis.objects.filter(
            response__user__username__in=similar_usernames,
            response__is_complete=True
        ).select_related('section', 'response')
        
        # Group by section and aggregate
        section_topics = defaultdict(lambda: {
            'section': None,
            'contributions': [],
            'keywords': defaultdict(float),
            'sentiment_scores': [],
            'count': 0
        })
        
        for topic_analysis in all_topic_analyses:
            section_name = topic_analysis.section.name if topic_analysis.section else 'Unknown'
            section_data = section_topics[section_name]
            
            if not section_data['section']:
                section_data['section'] = topic_analysis.section
            
            section_data['contributions'].append(topic_analysis.topic_contribution_score)
            section_data['sentiment_scores'].append(topic_analysis.sentiment_score)
            section_data['count'] += 1
            
            # Aggregate keywords (weight by contribution)
            if topic_analysis.topic_keywords:
                keywords = topic_analysis.topic_keywords.split(',') if isinstance(topic_analysis.topic_keywords, str) else topic_analysis.topic_keywords
                for keyword in keywords[:10]:  # Top 10 keywords
                    keyword = keyword.strip()
                    if keyword:
                        section_data['keywords'][keyword] += topic_analysis.topic_contribution_score
        
        # Create aggregated topic analyses list
        aggregated_topics = []
        for section_name, data in section_topics.items():
            if data['count'] > 0:
                avg_contribution = sum(data['contributions']) / len(data['contributions'])
                avg_sentiment = sum(data['sentiment_scores']) / len(data['sentiment_scores'])
                
                # Get top keywords
                sorted_keywords = sorted(data['keywords'].items(), key=lambda x: x[1], reverse=True)
                top_keywords = [kw[0] for kw in sorted_keywords[:10]]
                
                aggregated_topics.append({
                    'section_name': section_name,
                    'section': data['section'],
                    'topic_contribution_score': avg_contribution,
                    'sentiment_score': avg_sentiment,
                    'topic_keywords': ', '.join(top_keywords) if top_keywords else 'No keywords available',
                    'response_count': data['count']
                })
        
        # Sort by contribution score
        aggregated_topics.sort(key=lambda x: x['topic_contribution_score'], reverse=True)
        context['aggregated_topic_analyses'] = aggregated_topics
        
    except Exception as e:
        logger.error(f"Error getting aggregated topic analyses: {e}", exc_info=True)
        context['aggregated_topic_analyses'] = []
    
    # Initialize pipeline if not already available
    if 'pipeline' not in locals():
        pipeline = MLPipeline()
    
    # Get lacking features summary (Overall Rating + section-specific topics with correlations)
    try:
        lacking_summary = pipeline.get_lacking_features_summary()
        context['lacking_summary'] = lacking_summary
    except Exception as e:
        logger.error(f"Error getting lacking features summary: {e}")
        context['lacking_summary'] = {'overall_rating': None, 'sections': {}}
    
    # Generate feedback summary based on sentiment distribution
    try:
        feedback_summary = _generate_feedback_summary(request.user, sentiment_dict, total_responses, pipeline)
        context['feedback_summary'] = feedback_summary
    except Exception as e:
        logger.error(f"Error generating feedback summary: {e}")
        context['feedback_summary'] = None
    
    # Generate forecast for recent reviews
    try:
        forecast_data = _generate_sentiment_forecast(request.user)
        if forecast_data:
            # Convert to JSON for template
            import json
            context['forecast_data'] = json.dumps(forecast_data)
        else:
            context['forecast_data'] = None
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        context['forecast_data'] = None
    
    # Convert feedback_summary section_importance to JSON if it exists
    if context.get('feedback_summary') and context['feedback_summary']:
        section_importance = context['feedback_summary'].get('section_importance')
        if section_importance:
            import json
            try:
                context['feedback_summary']['section_importance'] = json.dumps(section_importance)
                logger.info(f"Section importance JSON serialized successfully. Length: {len(context['feedback_summary']['section_importance'])}")
            except Exception as e:
                logger.error(f"Error serializing section_importance to JSON: {e}")
                context['feedback_summary']['section_importance'] = None
        else:
            logger.warning("section_importance is None in feedback_summary")
    
    # Prepare strengths and weaknesses based on feature importance
    strengths_data = None
    weaknesses_data = None
    
    if context.get('feedback_summary') and context['feedback_summary'].get('section_importance'):
        try:
            import json
            section_importance = json.loads(context['feedback_summary']['section_importance'])
            sorted_sections = section_importance.get('sorted_sections', [])
            aggregated_topics = context.get('aggregated_topic_analyses', [])
            
            # Get section with highest feature importance (strength)
            if sorted_sections:
                strongest_section = sorted_sections[0]
                # Find topics for this section from aggregated topics
                for topic in aggregated_topics:
                    if topic.get('section_name') == strongest_section:
                        strengths_data = topic
                        break
                
                # If not found in aggregated topics, try to get from feature importance topics
                if not strengths_data:
                    try:
                        positive_topics = pipeline.get_section_feature_importance_topics('positive', top_n=10)
                        for topic in positive_topics:
                            if topic.get('section') == strongest_section:
                                strengths_data = {
                                    'section_name': topic['section'],
                                    'topic_keywords': ', '.join(topic.get('keywords', [])[:10]),
                                    'sentiment_score': 0.5,  # Positive
                                    'response_count': topic.get('frequency', 0)
                                }
                                break
                    except Exception as e:
                        logger.error(f"Error getting positive topics: {e}")
            
            # Get section with lowest feature importance (weakness)
            if sorted_sections:
                weakest_section = sorted_sections[-1]
                # Find topics for this section from aggregated topics
                for topic in aggregated_topics:
                    if topic.get('section_name') == weakest_section:
                        weaknesses_data = topic
                        break
                
                # If not found in aggregated topics, try to get from feature importance topics
                if not weaknesses_data:
                    try:
                        negative_topics = pipeline.get_section_feature_importance_topics('negative', top_n=10)
                        for topic in negative_topics:
                            if topic.get('section') == weakest_section:
                                weaknesses_data = {
                                    'section_name': topic['section'],
                                    'topic_keywords': ', '.join(topic.get('keywords', [])[:10]),
                                    'sentiment_score': -0.5,  # Negative
                                    'response_count': topic.get('frequency', 0)
                                }
                                break
                    except Exception as e:
                        logger.error(f"Error getting negative topics: {e}")
        except Exception as e:
            logger.error(f"Error preparing strengths/weaknesses: {e}", exc_info=True)
    
    context['strengths_data'] = strengths_data
    context['weaknesses_data'] = weaknesses_data
    
    return render(request, 'frontend/dashboard.html', context)

def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('frontend:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'frontend/login.html')

def register_view(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect('frontend:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('frontend:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'frontend/register.html', context)

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('frontend:login')

def questionnaire_intro(request):
    """Intro page before starting the questionnaire"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    return render(request, 'frontend/questionnaire_intro.html')

def sentiment_analysis(request):
    """Sentiment Analysis page view with questionnaire"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    try:
        # Check if user has already completed the questionnaire (but allow them to take it again)
        existing_response = QuestionnaireResponse.objects.filter(
            user=request.user, 
            is_complete=True
        ).first()
        
        if request.method == 'POST':
            return handle_questionnaire_submission(request)
        
        # Always show the questionnaire form, even if they've completed it before
        # (They can submit a new response)
        
        # Get only the 6 ML-essential sections (used by the ML model)
        ml_essential_sections = [
            'Compensation & Benefits',
            'Work-Life Balance',
            'Culture & Values',
            'Diversity & Inclusion',
            'Career Development',
            'Management & Leadership'
        ]
        sections = QuestionnaireSection.objects.prefetch_related('questions').filter(
            name__in=ml_essential_sections,
            questions__isnull=False
        ).distinct().order_by('order', 'id')
        
        # Check if sections exist - if not, show error message but still render the page
        if not sections.exists():
            logger.error(f"No sections found for questionnaire. Available sections: {list(QuestionnaireSection.objects.all().values_list('name', flat=True))}")
            messages.error(request, 'Questionnaire is not available. Please contact administrator to set up the questionnaire sections.')
            # Still render the page with empty sections so user can see the error
            sections = QuestionnaireSection.objects.none()
        
        context = {
            'current_time': timezone.now(),
            'sections': sections,
            'existing_response': existing_response,
            'scale_choices': [
                (1, '1 - Strongly Disagree'),
                (2, '2 - Disagree'),
                (3, '3 - Neutral'),
                (4, '4 - Agree'),
                (5, '5 - Strongly Agree'),
            ]
        }
        return render(request, 'frontend/sentiment_analysis.html', context)
    except Exception as e:
        logger.error(f"Error in sentiment_analysis view: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while loading the questionnaire: {str(e)}')
        # Instead of redirecting, render the page with empty context to show the error
        return render(request, 'frontend/sentiment_analysis.html', {
            'sections': QuestionnaireSection.objects.none(),
            'existing_response': None,
            'scale_choices': [
                (1, '1 - Strongly Disagree'),
                (2, '2 - Disagree'),
                (3, '3 - Neutral'),
                (4, '4 - Agree'),
                (5, '5 - Strongly Agree'),
            ]
        })

def handle_questionnaire_submission(request):
    """Handle questionnaire form submission - unified with CSV data structure"""
    try:
        with transaction.atomic():
            # Get review from form
            review = request.POST.get('review', '').strip()
            if not review:
                messages.error(request, 'Review is required. Please provide your feedback.')
                return redirect('frontend:sentiment_analysis')
            
            # Create new response (always create new, don't update existing)
            response = QuestionnaireResponse.objects.create(
                user=request.user,
                submitted_at=timezone.now(),
                review=review,
                is_complete=True  # Mark as complete immediately
            )
            
            # Process form data and calculate section scores
            section_totals = {}
            section_counts = {}
            
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    try:
                        question_id = int(key.split('_')[1])
                        score = int(value)
                        
                        question = get_object_or_404(QuestionnaireQuestion, id=question_id)
                        
                        # Create question response
                        QuestionResponse.objects.create(
                            response=response,
                            question=question,
                            score=score
                        )
                        
                        # Calculate section totals
                        section = question.section
                        if section.id not in section_totals:
                            section_totals[section.id] = 0
                            section_counts[section.id] = 0
                        
                        section_totals[section.id] += score
                        section_counts[section.id] += 1
                        
                    except (ValueError, IndexError):
                        continue
            
            # Calculate and save section scores (same as CSV upload)
            for section_id, total in section_totals.items():
                section = get_object_or_404(QuestionnaireSection, id=section_id)
                average_score = total / section_counts[section_id]
                
                SectionScore.objects.create(
                    response=response,
                    section=section,
                    average_score=average_score,
                    total_questions=section_counts[section_id]
                )
            
            # Perform sentiment analysis (same as CSV upload)
            from ml_analysis.services import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_result = sentiment_analyzer.analyze_text(review)
            
            # Create sentiment analysis (same as CSV upload)
            from ml_analysis.models import SentimentAnalysis
            SentimentAnalysis.objects.create(
                response=response,
                compound_score=sentiment_result['compound'],
                positive_score=sentiment_result['pos'],
                negative_score=sentiment_result['neg'],
                neutral_score=sentiment_result['neu'],
                sentiment_label=sentiment_result['sentiment'],
                confidence=sentiment_result['confidence'],
                text_length=len(review)
            )
            
            # Create training data entry (same as CSV upload)
            from ml_analysis.models import TrainingData
            TrainingData.objects.create(
                text=review,
                sentiment_label=sentiment_result['sentiment'],
                section_scores={section.name: score.average_score for score in response.section_scores.all()},
                source='questionnaire',
                is_verified=True
            )
            
            # Perform ML analysis
            try:
                analyze_response_ml(response.id)
            except Exception as e:
                logger.warning(f"ML analysis failed for response {response.id}: {str(e)}")  # Don't fail the submission if ML fails
            
            logger.info(f"Successfully created questionnaire response {response.id} for user {request.user.username}")
            messages.success(request, 'Questionnaire submitted successfully! Thank you for your feedback.')
            return redirect('frontend:questionnaire_congratulations', response_id=response.id)
            
    except Exception as e:
        logger.error(f"Error submitting questionnaire for user {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, f'Error submitting questionnaire: {str(e)}')
        return redirect('frontend:dashboard')

def questionnaire_congratulations(request, response_id):
    """Congratulations page after completing the questionnaire"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    response = get_object_or_404(QuestionnaireResponse, id=response_id, user=request.user)
    
    context = {
        'response': response,
    }
    
    return render(request, 'frontend/questionnaire_congratulations.html', context)

def questionnaire_results(request, response_id):
    """Display questionnaire results with ML insights"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    response = get_object_or_404(QuestionnaireResponse, id=response_id, user=request.user)
    section_scores = response.section_scores.select_related('section').all()
    
    # Calculate overall average
    overall_average = sum(score.average_score for score in section_scores) / len(section_scores) if section_scores else 0
    
    # Get ML insights
    ml_insights = MLInsight.objects.filter(response=response).order_by('-confidence_score')
    topic_analyses = response.ml_topic_analyses.order_by('-topic_contribution_score')
    
    context = {
        'response': response,
        'section_scores': section_scores,
        'overall_average': overall_average,
        'ml_insights': ml_insights,
        'topic_analyses': topic_analyses,
        'current_time': timezone.now(),
    }
    return render(request, 'frontend/questionnaire_results.html', context)

#def support(request):
#    """Support page view"""
#    if not request.user.is_authenticated:
#        return redirect('frontend:login')
#    
#    context = {
#        'current_time': timezone.now(),
#    }
#    return render(request, 'frontend/support.html', context)

def accounts_settings(request):
    """Accounts & Settings page view"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    context = {
        'current_time': timezone.now(),
    }
    return render(request, 'frontend/accounts_settings.html', context)

def api_data(request):
    """API endpoint for frontend data"""
    data = {
        'message': 'Hello from Django API!',
        'timestamp': timezone.now().isoformat(),
        'status': 'success'
    }
    return JsonResponse(data)

#def raw_data(request):
#    """Display all responses (questionnaire + CSV) in unified table format for current user/tenant"""
#    if not request.user.is_authenticated:
#        return redirect('frontend:login')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    sentiment_filter = request.GET.get('sentiment', '')
    section_filter = request.GET.get('section', '')
    source_filter = request.GET.get('source', '')  # New filter for data source
    page_number = request.GET.get('page', 1)
    
    # Get all responses for current user/tenant (include similar usernames for testing)
    similar_usernames = [request.user.username.lower(), request.user.username.upper(), 
                       request.user.username.capitalize()]
    
    responses = QuestionnaireResponse.objects.filter(
        user__username__in=similar_usernames,
        is_complete=True
    ).select_related('user').prefetch_related(
        'section_scores__section',
        'sentiment_analysis',
        'topic_analyses'
    ).order_by('-submitted_at')
    
    # Apply filters
    if search_query:
        responses = responses.filter(
            Q(review__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if sentiment_filter:
        responses = responses.filter(
            sentiment_analysis__sentiment_label=sentiment_filter
        )
    
    if section_filter:
        responses = responses.filter(
            section_scores__section__name=section_filter
        )
    
    if source_filter:
        # Filter by data source (questionnaire vs CSV)
        if source_filter == 'questionnaire':
            responses = responses.filter(
                training_data__source='questionnaire'
            ).distinct()
        elif source_filter == 'csv':
            responses = responses.filter(
                training_data__source='dataset_import'
            ).distinct()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(responses, 50)  # 50 responses per page
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters (include similar usernames)
    from ml_analysis.models import SentimentAnalysis, TrainingData
    sentiment_choices = SentimentAnalysis.objects.filter(
        response__user__username__in=similar_usernames
    ).values_list('sentiment_label', flat=True).distinct()
    section_choices = QuestionnaireSection.objects.values_list('name', flat=True).distinct()
    source_choices = TrainingData.objects.filter(
        user__username__in=similar_usernames
    ).values_list('source', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'responses': page_obj,
        'search_query': search_query,
        'sentiment_filter': sentiment_filter,
        'section_filter': section_filter,
        'source_filter': source_filter,
        'sentiment_choices': sentiment_choices,
        'section_choices': section_choices,
        'source_choices': source_choices,
        'total_responses': paginator.count,
    }
    
    return render(request, 'frontend/raw_data.html', context)

def upload_data(request):
    """Upload CSV data for current user/tenant"""
    if not request.user.is_authenticated:
        return redirect('frontend:login')
    
    # Get current user's data summary (include similar usernames for testing)
    similar_usernames = [request.user.username.lower(), request.user.username.upper(), 
                        request.user.username.capitalize()]
    
    total_responses = QuestionnaireResponse.objects.filter(
        user__username__in=similar_usernames, 
        is_complete=True
    ).count()
    from ml_analysis.models import SentimentAnalysis
    sentiment_analyses = SentimentAnalysis.objects.filter(
        response__user__username__in=similar_usernames
    ).count()
    
    # Get last upload date
    last_response = QuestionnaireResponse.objects.filter(
        user__username__in=similar_usernames
    ).order_by('-submitted_at').first()
    last_upload = last_response.submitted_at if last_response else None
    
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        description = request.POST.get('description', '')
        
        if not csv_file:
            messages.error(request, 'Please select a CSV file to upload.')
            return render(request, 'frontend/upload_data.html', {
                'total_responses': total_responses,
                'sentiment_analyses': sentiment_analyses,
                'last_upload': last_upload,
            })
        
        if not csv_file.name.lower().endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return render(request, 'frontend/upload_data.html', {
                'total_responses': total_responses,
                'sentiment_analyses': sentiment_analyses,
                'last_upload': last_upload,
            })
        
        # Check file size (50MB limit)
        if csv_file.size > 50 * 1024 * 1024:
            messages.error(request, 'File size must be less than 50MB.')
            return render(request, 'frontend/upload_data.html', {
                'total_responses': total_responses,
                'sentiment_analyses': sentiment_analyses,
                'last_upload': last_upload,
            })
        
        try:
            # Save uploaded file temporarily
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                for chunk in csv_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Load data using the management command
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            # Capture command output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                logger.info(f"Starting CSV upload for user {request.user.username}, file: {csv_file.name}")
                call_command('load_dataset', 
                           csv_file=tmp_file_path, 
                           username=request.user.username,
                           batch_size=50)
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                
                # Check for errors in output
                output_lower = output.lower()
                error_indicators = ['error', 'not found', 'does not exist', 'failed', 'exception']
                has_error = any(indicator in output_lower for indicator in error_indicators)
                
                if has_error:
                    # Extract error message
                    error_lines = [line for line in output.split('\n') if any(indicator in line.lower() for indicator in error_indicators)]
                    error_message = error_lines[0] if error_lines else 'Unknown error occurred during CSV processing'
                    logger.error(f"CSV upload failed: {error_message}")
                    messages.error(request, f'CSV upload failed: {error_message}')
                    return render(request, 'frontend/upload_data.html', {
                        'total_responses': total_responses,
                        'sentiment_analyses': sentiment_analyses,
                        'last_upload': last_upload,
                    })
                
                # Parse output to get success count
                lines = output.split('\n')
                success_line = [line for line in lines if 'Successfully loaded' in line]
                if success_line:
                    logger.info(f"CSV upload successful: {success_line[0]}")
                    messages.success(request, success_line[0])
                    # Redirect to prevent form resubmission
                    return redirect('frontend:upload_data')
                else:
                    # Check if any data was actually created
                    new_total = QuestionnaireResponse.objects.filter(
                        user__username__in=similar_usernames, 
                        is_complete=True
                    ).count()
                    if new_total > total_responses:
                        logger.info(f"CSV upload successful: {new_total - total_responses} new records created")
                        messages.success(request, f'Data uploaded successfully! {new_total - total_responses} new records added.')
                        # Redirect to prevent form resubmission
                        return redirect('frontend:upload_data')
                    else:
                        logger.warning(f"CSV upload completed but no new records found. Output: {output[:500]}")
                        messages.warning(request, f'CSV processing completed, but no new records were created. Please check the file format and try again.')
                        # Still redirect to prevent form resubmission
                        return redirect('frontend:upload_data')
                
            except Exception as e:
                sys.stdout = old_stdout
                logger.error(f"Error processing CSV file for user {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, f'Error processing CSV file: {str(e)}')
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        
        except Exception as e:
            logger.error(f"Error uploading file for user {request.user.username}: {str(e)}", exc_info=True)
            messages.error(request, f'Error uploading file: {str(e)}')
    
    context = {
        'total_responses': total_responses,
        'sentiment_analyses': sentiment_analyses,
        'last_upload': last_upload,
    }
    
    return render(request, 'frontend/upload_data.html', context)

def special_questionnaire_view(request, token):
    """View for accessing special questionnaires via unique token"""
    try:
        questionnaire = SpecialQuestionnaire.objects.get(unique_token=token)
    except SpecialQuestionnaire.DoesNotExist:
        messages.error(request, 'Questionnaire not found or invalid link.')
        return render(request, 'frontend/questionnaire_not_found.html')
    
    # Check if questionnaire is available
    if not questionnaire.is_available:
        if questionnaire.is_expired:
            messages.error(request, 'This questionnaire has expired.')
        elif not questionnaire.is_active:
            messages.error(request, 'This questionnaire is no longer active.')
        elif questionnaire.current_responses >= questionnaire.max_responses:
            messages.error(request, 'This questionnaire has reached its maximum number of responses.')
        return render(request, 'frontend/questionnaire_unavailable.html', {
            'questionnaire': questionnaire
        })
    
    # Check if already responded (by IP address)
    client_ip = get_client_ip(request)
    existing_response = SpecialQuestionnaireResponse.objects.filter(
        questionnaire=questionnaire,
        ip_address=client_ip,
        is_complete=True
    ).first()
    
    if existing_response:
        messages.info(request, 'You have already completed this questionnaire.')
        return render(request, 'frontend/questionnaire_already_completed.html', {
            'questionnaire': questionnaire,
            'response': existing_response
        })
    
    if request.method == 'POST':
        return handle_special_questionnaire_submission(request, questionnaire)
    
    # Get only the 6 ML-essential sections (used by the ML model)
    ml_essential_sections = [
        'Compensation & Benefits',
        'Work-Life Balance',
        'Culture & Values',
        'Diversity & Inclusion',
        'Career Development',
        'Management & Leadership'
    ]
    sections = QuestionnaireSection.objects.prefetch_related('questions').filter(
        name__in=ml_essential_sections,
        questions__isnull=False
    ).distinct().order_by('order', 'id')
    
    context = {
        'questionnaire': questionnaire,
        'sections': sections,
        'scale_choices': [
            (1, '1 - Strongly Disagree'),
            (2, '2 - Disagree'),
            (3, '3 - Neutral'),
            (4, '4 - Agree'),
            (5, '5 - Strongly Agree'),
        ]
    }
    return render(request, 'frontend/special_questionnaire.html', context)

def handle_special_questionnaire_submission(request, questionnaire):
    """Handle special questionnaire form submission using unified response system"""
    try:
        with transaction.atomic():
            # Get review from form
            review = request.POST.get('review', '').strip()
            if not review:
                messages.error(request, 'Review is required. Please provide your feedback.')
                return redirect('frontend:special_questionnaire', token=questionnaire.unique_token)
            
            # Get client information
            client_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create unified response (no user for special questionnaires)
            response = QuestionnaireResponse.objects.create(
                user=None,  # Anonymous response
                submitted_at=timezone.now(),
                review=review,
                is_complete=True,
                ip_address=client_ip,
                user_agent=user_agent,
                is_special_response=True
            )
            
            # Update questionnaire response count
            questionnaire.current_responses += 1
            questionnaire.save()
            
            # Process form data and calculate section scores
            section_totals = {}
            section_counts = {}
            
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    try:
                        question_id = int(key.split('_')[1])
                        score = int(value)
                        
                        question = get_object_or_404(QuestionnaireQuestion, id=question_id)
                        
                        # Create question response using unified system
                        QuestionResponse.objects.create(
                            response=response,
                            question=question,
                            score=score
                        )
                        
                        # Calculate section totals
                        section = question.section
                        if section.id not in section_totals:
                            section_totals[section.id] = 0
                            section_counts[section.id] = 0
                        
                        section_totals[section.id] += score
                        section_counts[section.id] += 1
                        
                    except (ValueError, IndexError):
                        continue
            
            # Calculate and save section scores using unified system
            for section_id, total in section_totals.items():
                section = get_object_or_404(QuestionnaireSection, id=section_id)
                average_score = total / section_counts[section_id]
                
                SectionScore.objects.create(
                    response=response,
                    section=section,
                    average_score=average_score,
                    total_questions=section_counts[section_id]
                )
            
            # Perform ML analysis
            try:
                analyze_response_ml(response.id)
            except Exception as e:
                logger.warning(f"ML analysis failed for special questionnaire response: {str(e)}")  # Don't fail the submission if ML fails
            
            messages.success(request, 'Thank you for completing the questionnaire! Your feedback has been submitted successfully.')
            return redirect('frontend:special_questionnaire_thank_you', token=questionnaire.unique_token)
            
    except Exception as e:
        messages.error(request, f'Error submitting questionnaire: {str(e)}')
        return redirect('frontend:special_questionnaire', token=questionnaire.unique_token)

def special_questionnaire_thank_you(request, token):
    """Thank you page after completing special questionnaire"""
    try:
        questionnaire = SpecialQuestionnaire.objects.get(unique_token=token)
    except SpecialQuestionnaire.DoesNotExist:
        messages.error(request, 'Questionnaire not found.')
        return redirect('frontend:home')
    
    return render(request, 'frontend/special_questionnaire_thank_you.html', {
        'questionnaire': questionnaire
    })

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _generate_feedback_summary(user, sentiment_dict, total_responses, pipeline=None):
    """Generate feedback summary based on sentiment distribution and topics"""
    if not sentiment_dict or total_responses == 0:
        logger.warning(f"Feedback summary: sentiment_dict={sentiment_dict}, total_responses={total_responses}")
        return None
    
    # Calculate sentiment percentages
    positive_count = sentiment_dict.get('positive', 0)
    negative_count = sentiment_dict.get('negative', 0)
    neutral_count = sentiment_dict.get('neutral', 0)
    
    positive_pct = (positive_count / total_responses) * 100
    negative_pct = (negative_count / total_responses) * 100
    neutral_pct = (neutral_count / total_responses) * 100
    
    # Determine majority sentiment (threshold: >40% for majority)
    majority_sentiment = None
    if positive_pct > 40:
        majority_sentiment = 'positive'
    elif negative_pct > 40:
        majority_sentiment = 'negative'
    else:
        majority_sentiment = 'neutral'
    
    # Extract topics from responses with positive sentiment (strengths)
    # and negative sentiment (weaknesses)
    positive_topics_list = []
    negative_topics_list = []
    
    if pipeline:
        try:
            # Use section feature importance models (trained during pipeline)
            # These use Random Forest to identify words that contribute to high scores
            positive_topics = pipeline.get_section_feature_importance_topics('positive', top_n=5)
            negative_topics = pipeline.get_section_feature_importance_topics('negative', top_n=5)
            
            # If feature importance data not available, fall back to sentiment-based
            if not positive_topics and not negative_topics:
                logger.info("Feature importance data not available, using sentiment-based topics")
                positive_topics = pipeline.get_sentiment_based_topics('positive', top_n=5)
                negative_topics = pipeline.get_sentiment_based_topics('negative', top_n=5)
            
            positive_topics_list = [
                {
                    'topic_name': topic['topic_name'],
                    'section': topic['section'],
                    'keywords': topic['keywords'][:5],  # Top 5 keywords
                    'frequency': topic['frequency'],
                    'sentiment': 'positive'
                }
                for topic in positive_topics
            ]
            
            negative_topics_list = [
                {
                    'topic_name': topic['topic_name'],
                    'section': topic['section'],
                    'keywords': topic['keywords'][:5],  # Top 5 keywords
                    'frequency': topic['frequency'],
                    'sentiment': 'negative'
                }
                for topic in negative_topics
            ]
            
            logger.info(f"Feedback summary: Found {len(positive_topics_list)} strength topics, {len(negative_topics_list)} weakness topics")
            
        except Exception as e:
            logger.error(f"Error extracting sentiment-based topics: {e}", exc_info=True)
            # Fallback to correlation-based topics if sentiment-based extraction fails
            positive_topics = list(SectionTopicCorrelation.objects.filter(
                correlation_score__gt=0.1
            ).order_by('-correlation_score')[:5])
            
            negative_topics = list(SectionTopicCorrelation.objects.filter(
                correlation_score__lt=-0.1
            ).order_by('correlation_score')[:5])
            
            stop_words_to_filter = {'there', 'There', 'THERE'}
            
            def filter_keywords(keywords_list):
                """Filter out stop words from keywords list"""
                if not keywords_list:
                    return []
                return [kw for kw in keywords_list if kw.lower() not in stop_words_to_filter]
            
            positive_topics_list = [
                {
                    'topic_name': topic.topic_name,
                    'section': topic.section_name,
                    'keywords': filter_keywords(
                        list(topic.keywords.keys())[:10] if isinstance(topic.keywords, dict) else topic.keywords[:10] if isinstance(topic.keywords, list) else []
                    )[:5]
                }
                for topic in positive_topics
            ]
            
            negative_topics_list = [
                {
                    'topic_name': topic.topic_name,
                    'section': topic.section_name,
                    'keywords': filter_keywords(
                        list(topic.keywords.keys())[:10] if isinstance(topic.keywords, dict) else topic.keywords[:10] if isinstance(topic.keywords, list) else []
                    )[:5]
                }
                for topic in negative_topics
            ]
    
    # Generate message based on majority sentiment
    # Always show both strengths (positive sentiment topics) and weaknesses (negative sentiment topics)
    if majority_sentiment == 'positive':
        message = "Your company has been doing great! Here are your strengths and areas for improvement:"
        topics_to_show = {
            'positive': positive_topics_list[:5] if positive_topics_list else [],
            'negative': negative_topics_list[:3] if negative_topics_list else []
        }
    elif majority_sentiment == 'negative':
        message = "Your company has areas that need attention. Here are your strengths and weaknesses:"
        topics_to_show = {
            'positive': positive_topics_list[:3] if positive_topics_list else [],
            'negative': negative_topics_list[:5] if negative_topics_list else []
        }
    else:  # neutral
        message = "Your company shows mixed feedback. Here are your strengths and weaknesses:"
        topics_to_show = {
            'positive': positive_topics_list[:3] if positive_topics_list else [],
            'negative': negative_topics_list[:3] if negative_topics_list else []
        }
    
    # If no topics found, show a message
    if not positive_topics_list and not negative_topics_list:
        message = "Your company feedback analysis is ready. Train models to see detailed topic insights."
        topics_to_show = {
            'positive': [],
            'negative': []
        }
    
    # Get section importance analysis (feature importance from Random Forest)
    section_importance = None
    if pipeline:
        try:
            section_importance = pipeline.get_section_importance_analysis()
            if section_importance:
                logger.info(f"Section importance analysis successful: {len(section_importance.get('sorted_sections', []))} sections")
            else:
                logger.warning("Section importance analysis returned None - may need more data or all sections")
        except Exception as e:
            logger.error(f"Error getting section importance: {e}", exc_info=True)
            section_importance = None
    
    # Calculate confidence rating based on sample size
    confidence_level = 'Low'
    if total_responses >= 30:
        confidence_level = 'High'
    elif total_responses >= 10:
        confidence_level = 'Medium'
    
    return {
        'majority_sentiment': majority_sentiment,
        'message': message,
        'topics': topics_to_show,
        'sentiment_percentages': {
            'positive': positive_pct,
            'negative': negative_pct,
            'neutral': neutral_pct
        },
        'sentiment_counts': {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        },
        'section_importance': section_importance,
        'confidence_rating': confidence_level,
        'sample_size': total_responses
    }

def _generate_sentiment_forecast(user):
    """Generate forecast for sentiment trends based on recent reviews"""
    # Get similar usernames for testing
    similar_usernames = [user.username.lower(), user.username.upper(), user.username.capitalize()]
    
    # Get responses from last 90 days, ordered by date
    cutoff_date = timezone.now() - timedelta(days=90)
    responses = QuestionnaireResponse.objects.filter(
        user__username__in=similar_usernames,
        is_complete=True,
        submitted_at__gte=cutoff_date
    ).select_related('sentiment_analysis').order_by('submitted_at')
    
    response_count = responses.count()
    logger.info(f"Forecast: Found {response_count} responses in last 90 days")
    
    if response_count < 5:  # Need at least 5 data points
        logger.warning(f"Forecast: Not enough data points ({response_count} < 5)")
        return None
    
    # Create time series data
    data_points = []
    for response in responses:
        try:
            sentiment = response.sentiment_analysis
            if sentiment:
                # Convert sentiment to numeric (positive=1, neutral=0, negative=-1)
                sentiment_score = 0
                if sentiment.sentiment_label == 'positive':
                    sentiment_score = 1
                elif sentiment.sentiment_label == 'negative':
                    sentiment_score = -1
                
                data_points.append({
                    'date': response.submitted_at.date(),
                    'sentiment_score': sentiment_score,
                    'compound_score': sentiment.compound_score
                })
        except:
            continue
    
    if len(data_points) < 5:
        return None
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(data_points)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # Group by date and calculate average sentiment
    daily_avg = df.groupby(df.index.date)['sentiment_score'].mean().reset_index()
    daily_avg.columns = ['date', 'avg_sentiment']
    daily_avg['date'] = pd.to_datetime(daily_avg['date'])
    
    # Simple linear regression for forecasting (next 7 days)
    if len(daily_avg) >= 7:
        # Fit a simple trend line
        x = np.arange(len(daily_avg))
        y = daily_avg['avg_sentiment'].values
        
        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        trend_line = np.poly1d(coeffs)
        
        # Generate forecast dates (next 7 days)
        last_date = daily_avg['date'].iloc[-1]
        forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=7, freq='D')
        forecast_x = np.arange(len(daily_avg), len(daily_avg) + 7)
        forecast_values = trend_line(forecast_x)
        
        # Prepare data for chart
        historical_dates = daily_avg['date'].tolist()
        historical_values = daily_avg['avg_sentiment'].tolist()
        forecast_dates_list = forecast_dates.tolist()
        forecast_values_list = forecast_values.tolist()
        
        return {
            'historical': {
                'dates': [d.strftime('%Y-%m-%d') for d in historical_dates],
                'values': historical_values
            },
            'forecast': {
                'dates': [d.strftime('%Y-%m-%d') for d in forecast_dates_list],
                'values': forecast_values_list.tolist()
            },
            'trend': 'increasing' if coeffs[0] > 0 else 'decreasing' if coeffs[0] < 0 else 'stable'
        }
    
    return None
