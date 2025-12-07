import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from django.db import transaction
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

try:
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from sentence_transformers import SentenceTransformer
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTopic = None
    ClassTfidfTransformer = None
    SentenceTransformer = None
    BERTOPIC_AVAILABLE = False
    logger.warning("BERTopic not available. Install with: pip install bertopic sentence-transformers")
# from sentence_transformers import SentenceTransformer

from .models import (
    SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation, 
    MLModel, TrainingData, UserFeedback
)
from frontend.models import QuestionnaireResponse, SectionScore
from .preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """VADER-based sentiment analysis service"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the latest sentiment model from database"""
        try:
            model_obj = MLModel.objects.filter(
                model_type='vader',
                is_active=True
            ).order_by('-created_at').first()
            
            if model_obj and model_obj.model_file:
                self.model = joblib.load(model_obj.model_file.path)
                logger.info(f"Loaded sentiment model: {model_obj.name}")
        except Exception as e:
            logger.warning(f"Could not load sentiment model: {e}")
            self.model = None
    
    def save_model(self, accuracy: float = None):
        """Save the current model to database"""
        try:
            # Create a temporary file to save the model
            import tempfile
            import time
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_file:
                joblib.dump(self.analyzer, tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Create model record
            model_obj = MLModel.objects.create(
                name=f"VADER_Sentiment_Model_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                model_type='vader',
                version='1.0',
                accuracy=accuracy,
                model_config={
                    'analyzer_type': 'VADER',
                    'version': '1.0',
                    'features': ['compound', 'pos', 'neu', 'neg']
                },
                is_active=True
            )
            
            # Save the file
            with open(tmp_file_path, 'rb') as f:
                model_obj.model_file.save(
                    f"sentiment_model_{model_obj.id}.joblib",
                    f,
                    save=True
                )
            
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass  # Ignore cleanup errors
                
                # Deactivate old models
                MLModel.objects.filter(
                    model_type='vader',
                    is_active=True
                ).exclude(id=model_obj.id).update(is_active=False)
                
                logger.info(f"Saved sentiment model: {model_obj.name}")
                return model_obj
                
        except Exception as e:
            logger.error(f"Failed to save sentiment model: {e}")
            return None
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text sentiment using VADER"""
        if not text or not text.strip():
            return {
                'compound': 0.0,
                'pos': 0.0,
                'neu': 1.0,
                'neg': 0.0,
                'sentiment': 'neutral',
                'confidence': 0.0
            }
        
        scores = self.analyzer.polarity_scores(text)
        
        # Determine sentiment label
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
            confidence = compound
        elif compound <= -0.05:
            sentiment = 'negative'
            confidence = abs(compound)
        else:
            sentiment = 'neutral'
            confidence = scores['neu']
        
        return {
            'compound': compound,
            'pos': scores['pos'],
            'neu': scores['neu'],
            'neg': scores['neg'],
            'sentiment': sentiment,
            'confidence': confidence
        }
    
    def save_analysis(self, response: QuestionnaireResponse, text: str) -> SentimentAnalysis:
        """Analyze text and save results to database"""
        analysis_result = self.analyze_text(text)
        
        with transaction.atomic():
            sentiment_analysis, created = SentimentAnalysis.objects.update_or_create(
                response=response,
                defaults={
                    'compound_score': analysis_result['compound'],
                    'positive_score': analysis_result['pos'],
                    'negative_score': analysis_result['neg'],
                    'neutral_score': analysis_result['neu'],
                    'sentiment_label': analysis_result['sentiment'],
                    'confidence': analysis_result['confidence'],
                    'text_length': len(text)
                }
            )
        
        return sentiment_analysis

class TopicAnalyzer:
    """BERTopic-based topic modeling service"""
    
    def __init__(self):
        self.model = None
        self.embedding_model = None
        self._load_model()
        if not self.model:
            self._initialize_model()
    
    def _load_model(self):
        """Load the latest topic model from database"""
        try:
            model_obj = MLModel.objects.filter(
                model_type='bertopic',
                is_active=True
            ).order_by('-created_at').first()
            
            if model_obj and model_obj.model_file:
                self.model = joblib.load(model_obj.model_file.path)
                logger.info(f"Loaded topic model: {model_obj.name}")
        except Exception as e:
            logger.warning(f"Could not load topic model: {e}")
            self.model = None
    
    def save_model(self, accuracy: float = None):
        """Save the current model to database"""
        try:
            if not self.model:
                logger.warning("No model to save")
                return None
                
            # Create a temporary file to save the model
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_file:
                joblib.dump(self.model, tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Create model record
            model_obj = MLModel.objects.create(
                name=f"BERTopic_Model_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                model_type='bertopic',
                version='1.0',
                accuracy=accuracy,
                model_config={
                    'embedding_model': 'all-MiniLM-L6-v2',
                    'vectorizer': 'TfidfVectorizer',
                    'min_df': 2,
                    'max_df': 0.95,
                    'nr_topics': 10
                },
                is_active=True
            )
            
            # Save the file
            with open(tmp_file_path, 'rb') as f:
                model_obj.model_file.save(
                    f"topic_model_{model_obj.id}.joblib",
                    f,
                    save=True
                )
            
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass  # Ignore cleanup errors
                
                # Deactivate old models
                MLModel.objects.filter(
                    model_type='bertopic',
                    is_active=True
                ).exclude(id=model_obj.id).update(is_active=False)
                
                logger.info(f"Saved topic model: {model_obj.name}")
                return model_obj
                
        except Exception as e:
            logger.error(f"Failed to save topic model: {e}")
            return None
    
    def _initialize_model(self):
        """Initialize BERTopic model"""
        if not BERTOPIC_AVAILABLE:
            logger.error("BERTopic is not available. Please install it with: pip install bertopic sentence-transformers")
            self.model = None
            return
        
        try:
            # Use a lightweight embedding model for better performance
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize BERTopic with custom parameters
            self.model = BERTopic(
                embedding_model=self.embedding_model,
                vectorizer_model=TfidfVectorizer(
                    min_df=2,
                    max_df=0.95,
                    ngram_range=(1, 2),
                    stop_words='english'
                ),
                ctfidf_model=ClassTfidfTransformer(reduce_frequent_words=True),
                min_topic_size=2,
                nr_topics=10,  # Limit topics for better interpretability
                verbose=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize BERTopic model: {e}")
            self.model = None
    
    def train_model(self, texts: List[str]) -> Dict:
        """
        Train BERTopic model on all training texts
        Returns dict with training results
        """
        if not BERTOPIC_AVAILABLE:
            return {'error': 'BERTopic is not available. Please install it with: pip install bertopic sentence-transformers'}
        
        if not texts or len(texts) < 2:
            return {'error': 'Not enough training data (need at least 2 texts)'}
        
        try:
            # Initialize model if not already done
            if not self.model:
                self._initialize_model()
            
            if not self.model:
                return {'error': 'Failed to initialize BERTopic model'}
            
            # Fit the model on all training texts
            logger.info(f"Training BERTopic on {len(texts)} texts...")
            topics, probabilities = self.model.fit_transform(texts)
            
            # Get topic information
            topic_info = self.model.get_topic_info()
            
            # Extract topics with their keywords
            trained_topics = []
            for topic_id in topic_info['Topic'].values:
                if topic_id == -1:  # Skip outlier topic
                    continue
                
                topic_words = self.model.get_topic(topic_id)
                if topic_words:
                    keywords = [word for word, _ in topic_words[:10]]  # Top 10 keywords
                    count = len([t for t in topics if t == topic_id])
                    
                    trained_topics.append({
                        'topic_id': int(topic_id),
                        'topic_name': f"Topic {topic_id}",
                        'keywords': keywords,
                        'count': count,
                        'percentage': (count / len(texts)) * 100
                    })
            
            logger.info(f"BERTopic training completed. Found {len(trained_topics)} topics.")
            
            return {
                'topics_found': len(trained_topics),
                'total_texts': len(texts),
                'topics': trained_topics
            }
        except Exception as e:
            logger.error(f"BERTopic training failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def analyze_text(self, text: str) -> List[Dict]:
        """Analyze text and extract topics"""
        if not self.model or not text or not text.strip():
            return []
        
        try:
            # Fit the model on the text
            topics, probabilities = self.model.fit_transform([text])
            
            # Get topic information
            topic_info = self.model.get_topic_info()
            
            results = []
            for idx, (topic_id, prob) in enumerate(zip(topics[0], probabilities[0])):
                if prob > 0.1:  # Only include topics with significant probability
                    topic_name = f"Topic {topic_id}"
                    keywords = []
                    
                    # Get keywords for this topic
                    if topic_id in self.model.get_topics():
                        keywords = [word for word, _ in self.model.get_topics()[topic_id][:5]]
                    
                    results.append({
                        'topic_id': int(topic_id),
                        'topic_name': topic_name,
                        'keywords': keywords,
                        'probability': float(prob)
                    })
            
            return results
        except Exception as e:
            logger.error(f"Topic analysis failed: {e}")
            return []
    
    def save_analysis(self, response: QuestionnaireResponse, text: str) -> List[TopicAnalysis]:
        """Analyze text and save topic results to database"""
        topic_results = self.analyze_text(text)
        
        saved_topics = []
        with transaction.atomic():
            # Clear existing topic analyses for this response
            TopicAnalysis.objects.filter(response=response).delete()
            
            for topic_data in topic_results:
                topic_analysis = TopicAnalysis.objects.create(
                    response=response,
                    topic_id=topic_data['topic_id'],
                    topic_name=topic_data['topic_name'],
                    topic_keywords=topic_data['keywords'],
                    topic_probability=topic_data['probability']
                )
                saved_topics.append(topic_analysis)
        
        return saved_topics
    
    def get_global_topics(self) -> List[Dict]:
        """
        Get global topics from the trained model
        Returns list of topic dictionaries with id, name, keywords, count, percentage
        """
        if not BERTOPIC_AVAILABLE or not self.model:
            return []
        
        try:
            # Check if model is fitted by checking for topic_info method
            if not hasattr(self.model, 'get_topic_info'):
                return []
            
            # Try to get topic info - will raise error if model not fitted
            topic_info = self.model.get_topic_info()
            
            if topic_info is None or len(topic_info) == 0:
                return []
            
            global_topics = []
            
            for _, row in topic_info.iterrows():
                topic_id = row['Topic']
                if topic_id == -1:  # Skip outlier topic
                    continue
                
                topic_words = self.model.get_topic(topic_id)
                if topic_words:
                    keywords = [word for word, _ in topic_words[:10]]  # Top 10 keywords
                    count = int(row['Count']) if 'Count' in row else 0
                    
                    global_topics.append({
                        'topic_id': int(topic_id),
                        'topic_name': f"Topic {topic_id}",
                        'keywords': keywords,
                        'count': count,
                        'percentage': float(row['Percentage']) if 'Percentage' in row else 0.0
                    })
            
            return sorted(global_topics, key=lambda x: x['count'], reverse=True)
        except (AttributeError, ValueError, RuntimeError) as e:
            # Model not fitted yet or other expected errors - return empty list silently
            logger.debug(f"Model not fitted yet or error getting topics: {e}")
            return []
        except Exception as e:
            # Log unexpected errors but still return empty list to prevent dashboard crash
            logger.error(f"Unexpected error getting global topics: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

class SectionCorrelationAnalyzer:
    """Random Forest-based correlation analysis between topics and section scores"""
    
    def __init__(self, n_estimators=100, max_depth=None, min_samples_split=2, random_state=42):
        self.models = {}  # Dictionary to store models for each rating feature
        self.vectorizer = None
        self.preprocessor = TextPreprocessor()
        self.correlation_data = {}
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self._load_model()
    
    def _load_model(self):
        """Load the latest correlation model from database"""
        try:
            model_obj = MLModel.objects.filter(
                model_type='random_forest',
                is_active=True
            ).order_by('-created_at').first()
            
            if model_obj and model_obj.model_file:
                model_data = joblib.load(model_obj.model_file.path)
                self.models = model_data.get('models', {})
                self.vectorizer = model_data.get('vectorizer')
                logger.info(f"Loaded correlation model: {model_obj.name}")
        except Exception as e:
            logger.warning(f"Could not load correlation model: {e}")
            self.models = {}
            self.vectorizer = None
    
    def save_model(self, accuracy: float = None):
        """Save the current model to database"""
        try:
            if not self.models or not self.vectorizer:
                logger.warning("No models or vectorizer to save")
                return None
                
            # Create a temporary file to save the model
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp_file:
                model_data = {
                    'models': self.models,
                    'vectorizer': self.vectorizer,
                    'training_results': self._last_training_results
                }
                joblib.dump(model_data, tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Calculate average metrics for model record
            avg_mae = 0.0
            avg_r2 = 0.0
            if hasattr(self, '_last_training_results'):
                results = self._last_training_results.get('results', {})
                if results:
                    mae_values = [r.get('mae', 0) for r in results.values()]
                    r2_values = [r.get('r2_score', 0) for r in results.values()]
                    avg_mae = np.mean(mae_values) if mae_values else 0.0
                    avg_r2 = np.mean(r2_values) if r2_values else 0.0
            
            # Create model record
            model_obj = MLModel.objects.create(
                name=f"RandomForest_Model_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                model_type='random_forest',
                version='1.0',
                accuracy=avg_r2,  # Use R2 as accuracy metric for regression
                model_config={
                    'algorithm': 'RandomForestRegressor',
                    'n_estimators': self.n_estimators,
                    'max_depth': self.max_depth,
                    'min_samples_split': self.min_samples_split,
                    'random_state': self.random_state,
                    'features': ['tfidf_vectorized_text'],
                    'target_columns': list(self.models.keys())
                },
                is_active=True
            )
            
            # Save the file
            with open(tmp_file_path, 'rb') as f:
                model_obj.model_file.save(
                    f"correlation_model_{model_obj.id}.joblib",
                    f,
                    save=True
                )
            
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass  # Ignore cleanup errors
                
                # Deactivate old models
                MLModel.objects.filter(
                    model_type='random_forest',
                    is_active=True
                ).exclude(id=model_obj.id).update(is_active=False)
                
                logger.info(f"Saved correlation model: {model_obj.name}")
                return model_obj
                
        except Exception as e:
            logger.error(f"Failed to save correlation model: {e}")
            return None
    
    def prepare_training_data(self) -> Tuple[List[str], Dict[str, np.ndarray]]:
        """
        Prepare training data from questionnaire responses
        Returns:
            - texts: List of preprocessed text strings
            - target_ratings: Dict mapping rating feature names to numpy arrays
        """
        # Get all responses with reviews
        responses = QuestionnaireResponse.objects.filter(
            is_complete=True
        ).prefetch_related('section_scores')
        
        if not responses.exists():
            return [], {}
        
        texts = []
        target_ratings = {
            'overall_rating': [],
            'work_life_balance': [],
            'culture_values': [],
            'diversity_inclusion': [],
            'career_opp': [],
            'comp_benefits': [],
            'senior_mgmt': []
        }
        
        # Map section names to target columns
        section_to_target = {
            'Work-Life Balance': 'work_life_balance',
            'Culture & Values': 'culture_values',
            'Diversity & Inclusion': 'diversity_inclusion',
            'Career Development': 'career_opp',
            'Compensation & Benefits': 'comp_benefits',
            'Management & Leadership': 'senior_mgmt',
        }
        
        for response in responses:
            if not response.review:
                continue
            
            # Preprocess text
            preprocessed = self.preprocessor.preprocess_text(response.review)
            cleaned_text = preprocessed['cleaned_text_for_vader_bertopic']
            
            if not cleaned_text:
                continue
            
            texts.append(cleaned_text)
            
            # Get section scores and map to target columns
            section_scores_dict = {}
            for score in response.section_scores.all():
                section_name = score.section.name
                if section_name in section_to_target:
                    target_col = section_to_target[section_name]
                    section_scores_dict[target_col] = score.average_score
            
            # Get overall rating (average of all section scores or use a default)
            if section_scores_dict:
                overall = np.mean(list(section_scores_dict.values()))
            else:
                overall = 3.0  # Default neutral rating
            
            # Add ratings to target arrays
            target_ratings['overall_rating'].append(overall)
            for target_col in ['work_life_balance', 'culture_values', 'diversity_inclusion', 
                             'career_opp', 'comp_benefits', 'senior_mgmt']:
                target_ratings[target_col].append(section_scores_dict.get(target_col, overall))
        
        # Convert to numpy arrays
        for key in target_ratings:
            target_ratings[key] = np.array(target_ratings[key])
        
        return texts, target_ratings
    
    def train_model(self) -> Dict:
        """
        Train Random Forest Regressor models for each rating feature
        Based on notebook approach: separate model per feature
        """
        texts, target_ratings = self.prepare_training_data()
        
        if len(texts) == 0:
            return {'error': 'No training data available'}
        
        try:
            # Initialize TF-IDF vectorizer
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer()
            
            # Fit and transform texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Target columns (from notebook)
            target_columns = ['overall_rating', 'work_life_balance', 'culture_values', 
                            'diversity_inclusion', 'career_opp', 'comp_benefits', 'senior_mgmt']
            
            results = {}
            self.models = {}
            
            # Train a separate RandomForestRegressor for each target feature
            for col in target_columns:
                if col not in target_ratings or len(target_ratings[col]) == 0:
                    logger.warning(f"No data for target column: {col}")
                    continue
                
                y = target_ratings[col]
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                        tfidf_matrix, y, test_size=0.2, random_state=self.random_state
                )
                
                # Train RandomForestRegressor
                model = RandomForestRegressor(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    min_samples_split=self.min_samples_split,
                    random_state=self.random_state,
                    n_jobs=-1
                )
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                # Store model
                self.models[col] = model
                
                results[col] = {
                    'mae': mae,
                    'r2_score': r2,
                    'training_samples': X_train.shape[0],
                    'test_samples': X_test.shape[0]
                }
                
                logger.info(f"Trained model for {col}: MAE={mae:.4f}, R2={r2:.4f}")
            
            # Calculate correlations
            self._calculate_correlations(texts, target_ratings)
            
            # Store results for save_model
            self._last_training_results = {
                'results': results,
                'correlations_calculated': len(self.correlation_data)
            }
            
            return {
                'models_trained': len(self.models),
                'results': results,
                'correlations_calculated': len(self.correlation_data)
            }
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def _calculate_correlations(self, texts: List[str], target_ratings: Dict[str, np.ndarray]):
        """
        Calculate correlations and extract TF-IDF topic words for "lacking" sections
        Following notebook approach:
        1. Identify "lacking" texts using predicted ratings < 3.0 threshold
        2. Aggregate common words across ALL lacking features first
        3. Extract specialized words for each section from its "lacking" texts, excluding common words
        4. Create Overall Rating from aggregated words across all lacking texts
        """
        if not texts or not self.vectorizer or not self.models:
            return
        
        try:
            # Vectorize texts
            tfidf_matrix = self.vectorizer.transform(texts)
            
            # Target columns (excluding overall_rating for section-specific analysis)
            target_columns = ['work_life_balance', 'culture_values', 
                            'diversity_inclusion', 'career_opp', 'comp_benefits', 'senior_mgmt']
            
            threshold = 3.0  # From notebook
            ambiguous_positive_words = {'good', 'nice', 'great', 'positive'}
            
            # Step 1: Identify "lacking" texts for each section and aggregate common words
            all_lacking_words_scores = {}  # Aggregate scores across all lacking features
            lacking_data = {}  # Store lacking texts for each column
            
            for col in target_columns:
                if col not in self.models or col not in target_ratings:
                    continue
                
                model = self.models[col]
                predicted_ratings = model.predict(tfidf_matrix)
                
                # Identify "lacking" texts (predicted rating < 3.0)
                lacking_mask = predicted_ratings < threshold
                lacking_texts = [texts[i] for i in range(len(texts)) if lacking_mask[i]]
                
                if len(lacking_texts) > 0:
                    lacking_data[col] = lacking_texts
                    
                    # Extract words for this lacking feature
                    # Create a NEW vectorizer for each feature to ensure vocabulary is specific to the subset
                    topic_vectorizer = TfidfVectorizer(max_features=5000)
                    tfidf_lacking = topic_vectorizer.fit_transform(lacking_texts)
                    feature_names = topic_vectorizer.get_feature_names_out()
                    # Sum TF-IDF scores for each word across all documents
                    word_scores = tfidf_lacking.sum(axis=0)
                    
                    # Handle sparse matrix format
                    if hasattr(word_scores, 'A1'):
                        word_scores_flat = word_scores.A1
                    elif hasattr(word_scores, 'tolist'):
                        word_scores_list = word_scores.tolist()
                        if isinstance(word_scores_list[0], list):
                            word_scores_flat = word_scores_list[0]
                        else:
                            word_scores_flat = word_scores_list
                    else:
                        word_scores_flat = word_scores
                    
                    # Aggregate scores across all features
                    for word, score in zip(feature_names, word_scores_flat):
                        all_lacking_words_scores[word] = all_lacking_words_scores.get(word, 0) + score
            
            # Step 2: Filter out ambiguous positive words and get top 30-40 common words (more aggressive)
            filtered_common_words = {
                word: score for word, score in all_lacking_words_scores.items()
                if word not in ambiguous_positive_words
            }
            sorted_common_words = sorted(filtered_common_words.items(), key=lambda x: x[1], reverse=True)
            # Use top 35 common words (middle of 30-40 range) for filtering
            common_lacking_words_set = {word for word, score in sorted_common_words[:35]}
            
            # Store overall word scores for relative specialization calculation
            overall_word_scores = dict(sorted_common_words)  # All words with their overall scores
            
            # Step 3: Create Overall Rating from aggregated common words (top 10)
            # These are the words that appear frequently across ALL lacking sections
            overall_words_with_scores = dict(sorted_common_words[:10])
            self.correlation_data['overall_rating_topics'] = {
                'section_name': 'Overall Rating',
                'topic_id': hash('overall_rating') % 1000,
                'topic_name': 'Overall Rating Topics',
                'correlation': 0.0,
                'sample_size': len(texts),
                'avg_score': np.mean(target_ratings['overall_rating']) if 'overall_rating' in target_ratings and len(target_ratings['overall_rating']) > 0 else 0.0,
                'keywords': overall_words_with_scores
            }
            
            # Step 4: Extract specialized words for each section (excluding common words)
            # Map column names to section names
            section_name_map = {
                'work_life_balance': 'Work-Life Balance',
                'culture_values': 'Culture & Values',
                'diversity_inclusion': 'Diversity & Inclusion',
                'career_opp': 'Career Development',
                'comp_benefits': 'Compensation & Benefits',
                'senior_mgmt': 'Management & Leadership',
            }

            for col in target_columns:
                if col not in self.models or col not in target_ratings:
                    continue
                
                model = self.models[col]
                actual_ratings = target_ratings[col]
                predicted_ratings = model.predict(tfidf_matrix)
                
                section_name = section_name_map.get(col, col.replace('_', ' ').title())

                # Calculate correlation
                if len(actual_ratings) > 1:
                    correlation = np.corrcoef(actual_ratings, predicted_ratings)[0, 1]
                    # Handle NaN values (can occur if all values are the same)
                    if np.isnan(correlation):
                        correlation = 0.0
                    logger.debug(f"Correlation for {col} ({section_name}): {correlation:.4f} (n={len(actual_ratings)})")
                else:
                    correlation = 0.0
                    logger.warning(f"Insufficient data for correlation calculation in {col} ({section_name}): only {len(actual_ratings)} samples")
                
                # Extract specialized words from "lacking" texts for this section
                if col in lacking_data and len(lacking_data[col]) > 0:
                    lacking_texts = lacking_data[col]
                    
                    # Extract specialized dominant words (excluding common words)
                    # Create a NEW vectorizer for each feature to ensure vocabulary is specific to the subset
                    topic_vectorizer = TfidfVectorizer(max_features=5000)
                    tfidf_lacking = topic_vectorizer.fit_transform(lacking_texts)
                    
                    feature_names = topic_vectorizer.get_feature_names_out()
                    # Sum TF-IDF scores for each word across all documents in the filtered subset
                    # Following notebook: word_scores = tfidf_matrix_lacking.sum(axis=0)
                    word_scores = tfidf_lacking.sum(axis=0)
                    
                    # Convert to dictionary - following notebook exactly: word_scores.tolist()[0]
                    # The sum(axis=0) on sparse matrix returns a numpy.matrix with shape (1, n)
                    word_scores_list = word_scores.tolist()
                    if word_scores_list and isinstance(word_scores_list[0], list):
                        # 2D array - take first row (as in notebook: word_scores.tolist()[0])
                        word_scores_flat = word_scores_list[0]
                    else:
                        # Already 1D
                        word_scores_flat = word_scores_list
                    
                    # Create word-score dictionary
                    word_scores_dict = dict(zip(feature_names, word_scores_flat))
                    
                    # Calculate relative specialization scores (Hybrid Approach - Option 4)
                    # Specialization score = (section_score / overall_score) * section_score
                    # This highlights words that are both important in this section AND relatively more important here
                    specialization_threshold = 1.0  # Word must be at least as important in this section (1.0 = equal, allows words when texts are identical)
                    min_section_score = 0.05  # Minimum TF-IDF score to consider (lowered to allow more words)
                    specialized_words = []
                    
                    for word, section_score in word_scores_dict.items():
                        # Skip ambiguous positive words and top common words
                        if word in ambiguous_positive_words or word in common_lacking_words_set:
                            continue
                        
                        # Skip words with very low scores
                        if section_score < min_section_score:
                            continue
                        
                        # Get overall score for this word (across all sections)
                        overall_score = overall_word_scores.get(word, 0.0)
                        
                        # Calculate specialization score
                        if overall_score > 0:
                            specialization_ratio = section_score / overall_score
                            specialization_score = specialization_ratio * section_score
                        else:
                            # If word doesn't appear in overall, use section score directly
                            # This is a truly section-specific word
                            specialization_ratio = float('inf')
                            specialization_score = section_score
                        
                        # Only include words that are significantly more important in this section
                        # OR words that don't appear in overall (truly section-specific)
                        if specialization_ratio >= specialization_threshold or overall_score == 0:
                            specialized_words.append((word, section_score, specialization_score))
                    
                    # Sort by specialization score (most specialized first)
                    specialized_words.sort(key=lambda x: x[2], reverse=True)
                    
                    # Always prepare fallback words (in case specialization filtering is too strict)
                    filtered_words = [
                        (w, s) for w, s in sorted(word_scores_dict.items(), key=lambda x: x[1], reverse=True)
                        if w not in ambiguous_positive_words and w not in common_lacking_words_set and s >= min_section_score
                    ]
                    
                    # Use specialized words if we have enough (at least 5), otherwise use fallback
                    # This ensures we always have words to display, even when all sections share texts
                    if len(specialized_words) >= 5:
                        # Store top keywords with their original TF-IDF scores (for display)
                        # Take top 10 specialized words
                        top_keywords_for_lacking = {word: score for word, score, _ in specialized_words[:10]}
                    else:
                        # Fallback: use top words that aren't in common set
                        # This handles the case where all sections share identical texts
                        top_keywords_for_lacking = dict(filtered_words[:10])
                    
                    self.correlation_data[f"{col}_general_topics"] = {
                            'section_name': section_name,
                        'topic_id': hash(col + "_general") % 1000,
                        'topic_name': f"{section_name} General Topics",
                        'correlation': correlation,
                        'sample_size': len(lacking_texts),
                        'avg_score': np.mean(predicted_ratings[predicted_ratings < threshold]) if np.any(predicted_ratings < threshold) else 0.0,
                        'keywords': top_keywords_for_lacking
                    }
                else:
                    # No lacking texts for this section
                    self.correlation_data[f"{col}_general_topics"] = {
                        'section_name': section_name,
                        'topic_id': hash(col + "_general") % 1000,
                        'topic_name': f"{section_name} General Topics",
                        'correlation': correlation,
                        'sample_size': 0,
                        'avg_score': 0.0,
                        'keywords': {}
                    }
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def save_correlations(self):
        """Save correlation data to database"""
        with transaction.atomic():
            # Clear existing correlations
            SectionTopicCorrelation.objects.all().delete()
            
            saved_count = 0
            positive_count = 0
            negative_count = 0
            
            for key, data in self.correlation_data.items():
                # Store keywords as JSON (can be dict with word: score or list)
                keywords = data.get('keywords', {})
                
                # Convert dict to dict format (word: score pairs)
                if isinstance(keywords, dict):
                    # Keep as dict for word: score format
                    keywords_data = keywords
                elif isinstance(keywords, list):
                    # Convert list to dict with default score of 1.0
                    keywords_data = {word: 1.0 for word in keywords}
                else:
                    keywords_data = {}
                
                correlation_score = data['correlation']
                
                # Log correlation values for debugging
                if correlation_score > 0.1:
                    positive_count += 1
                elif correlation_score < -0.1:
                    negative_count += 1
                
                SectionTopicCorrelation.objects.create(
                    section_name=data['section_name'],
                    section_id=data['topic_id'],
                    topic_name=data['topic_name'],
                    topic_id=data['topic_id'],
                    correlation_score=correlation_score,
                    negative_correlation=correlation_score < 0,
                    sample_size=data['sample_size'],
                    keywords=keywords_data  # Store as dict with word: score
                )
                saved_count += 1
                
                # Log each correlation for debugging
                logger.info(f"Saved correlation: {data['section_name']} - {data['topic_name']}: {correlation_score:.4f} (sample_size={data['sample_size']})")
            
            logger.info(f"Saved {saved_count} correlations total: {positive_count} positive (>0.1), {negative_count} negative (<-0.1)")

class MLPipeline:
    """Main ML pipeline orchestrator"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_analyzer = TopicAnalyzer()
        self.correlation_analyzer = SectionCorrelationAnalyzer()
        self.preprocessor = TextPreprocessor()
        # Load feature importance data from database if available
        self.section_feature_importance = self._load_section_feature_importance_from_db()
    
    def analyze_response(self, response: QuestionnaireResponse) -> Dict:
        """Complete ML analysis for a questionnaire response"""
        if not response.review:
            return {'error': 'No review text available for analysis'}
        
        try:
            # Sentiment analysis
            sentiment_result = self.sentiment_analyzer.save_analysis(response, response.review)
            
            # Topic analysis
            topic_results = self.topic_analyzer.save_analysis(response, response.review)
            
            # Update correlations if we have enough data
            if QuestionnaireResponse.objects.filter(is_complete=True).count() > 10:
                self.correlation_analyzer.train_model()
                self.correlation_analyzer.save_correlations()
            
            return {
                'sentiment': {
                    'label': sentiment_result.sentiment_label,
                    'confidence': sentiment_result.confidence,
                    'compound_score': sentiment_result.compound_score
                },
                'topics': [
                    {
                        'id': topic.topic_id,
                        'name': topic.topic_name,
                        'keywords': topic.topic_keywords,
                        'probability': topic.topic_probability
                    }
                    for topic in topic_results
                ],
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"ML analysis failed for response {response.id}: {e}")
            return {'error': str(e)}
    
    def save_all_models(self):
        """Save all trained models to database"""
        results = {}
        
        # Save sentiment model
        try:
            sentiment_model = self.sentiment_analyzer.save_model()
            if sentiment_model:
                results['sentiment'] = f"Saved: {sentiment_model.name}"
            else:
                results['sentiment'] = "No sentiment model to save"
        except Exception as e:
            results['sentiment'] = f"Error: {e}"
        
        # Save topic model
        try:
            topic_model = self.topic_analyzer.save_model()
            if topic_model:
                results['topic'] = f"Saved: {topic_model.name}"
            else:
                results['topic'] = "No topic model to save"
        except Exception as e:
            results['topic'] = f"Error: {e}"
        
        # Save correlation model
        try:
            # Get metrics from last training if available
            correlation_model = self.correlation_analyzer.save_model()
            if correlation_model:
                results['correlation'] = f"Saved: {correlation_model.name}"
            else:
                results['correlation'] = "No correlation model to save"
        except Exception as e:
            results['correlation'] = f"Error: {e}"
        
        return results
    
    def train_section_feature_importance(self) -> Dict:
        """
        Train Random Forest models per section to identify words/topics that contribute to high/low scores.
        Uses TF-IDF and BERTopic features to predict section scores and extract feature importance.
        
        Trains SEPARATE models for:
        - Positive/Strengths: high scores (>= 4.0) per section
        - Negative/Weaknesses: low scores (< 3.0) per section
        
        Returns:
            Dict with 'positive' and 'negative' keys, each mapping section names to important words/topics
        """
        from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        
        section_names = [
            'Compensation & Benefits',
            'Work-Life Balance',
            'Culture & Values',
            'Diversity & Inclusion',
            'Career Development',
            'Management & Leadership'
        ]
        
        # Store separately for positive and negative
        positive_importance_data = {}
        negative_importance_data = {}
        
        # Get all responses with section scores
        responses = QuestionnaireResponse.objects.filter(
            is_complete=True
        ).prefetch_related('section_scores__section')
        
        if responses.count() < 10:
            logger.warning(f"Not enough responses for section feature importance: {responses.count()}")
            return {'positive': {}, 'negative': {}}
        
        # Get section objects
        sections = QuestionnaireSection.objects.filter(name__in=section_names)
        section_dict = {s.name: s for s in sections}
        
        # For each section, train TWO models: one for high scores (positive), one for low scores (negative)
        for section_name in section_names:
            if section_name not in section_dict:
                continue
            
            section = section_dict[section_name]
            
            # ===== POSITIVE MODEL (High scores >= 4.0) =====
            positive_texts = []
            positive_scores = []
            
            for response in responses:
                section_score_obj = response.section_scores.filter(section=section).first()
                if section_score_obj and response.review and response.review.strip():
                    # Only include responses with HIGH scores (>= 4.0) for this SPECIFIC section
                    if section_score_obj.average_score >= 4.0:
                        positive_texts.append(response.review)
                        positive_scores.append(section_score_obj.average_score)
            
            # Train positive model if we have enough data
            if len(positive_texts) >= 10:
                positive_keywords = self._train_section_model(
                    section_name, positive_texts, positive_scores, 'positive'
                )
                if positive_keywords:
                    positive_importance_data[section_name] = positive_keywords
            
            # ===== NEGATIVE MODEL (Low scores < 3.0) =====
            negative_texts = []
            negative_scores = []
            
            for response in responses:
                section_score_obj = response.section_scores.filter(section=section).first()
                if section_score_obj and response.review and response.review.strip():
                    # Only include responses with LOW scores (< 3.0) for this SPECIFIC section
                    if section_score_obj.average_score < 3.0:
                        negative_texts.append(response.review)
                        negative_scores.append(section_score_obj.average_score)
            
            # Train negative model if we have enough data
            if len(negative_texts) >= 10:
                negative_keywords = self._train_section_model(
                    section_name, negative_texts, negative_scores, 'negative'
                )
                if negative_keywords:
                    negative_importance_data[section_name] = negative_keywords
        
        # Store in instance variable for later retrieval
        self.section_feature_importance = {
            'positive': positive_importance_data,
            'negative': negative_importance_data
        }
        
        # Also save to database for persistence
        self._save_section_feature_importance_to_db(positive_importance_data, negative_importance_data)
        
        logger.info(f"Trained feature importance models: {len(positive_importance_data)} positive, {len(negative_importance_data)} negative sections")
        return self.section_feature_importance
    
    def _save_section_feature_importance_to_db(self, positive_data: Dict, negative_data: Dict):
        """Save section feature importance data to database for persistence"""
        from ml_analysis.models import SectionTopicCorrelation
        
        try:
            # Delete old feature importance data
            SectionTopicCorrelation.objects.filter(
                topic_name__contains='Feature Importance'
            ).delete()
            
            # Save positive (strengths) data
            for section_name, importance_data in positive_data.items():
                keywords = importance_data.get('keywords', [])
                importance_scores = importance_data.get('importance_scores', {})
                
                SectionTopicCorrelation.objects.create(
                    section_name=section_name,
                    section_id=hash(f"{section_name}_positive") % 10000,
                    topic_name=f"{section_name} Feature Importance (Positive)",
                    topic_id=hash(f"{section_name}_positive_fi") % 10000,
                    correlation_score=importance_data.get('model_score', 0.0),
                    negative_correlation=False,
                    sample_size=importance_data.get('sample_size', 0),
                    keywords=importance_scores  # Store as dict with word: importance_score
                )
            
            # Save negative (weaknesses) data
            for section_name, importance_data in negative_data.items():
                keywords = importance_data.get('keywords', [])
                importance_scores = importance_data.get('importance_scores', {})
                
                SectionTopicCorrelation.objects.create(
                    section_name=section_name,
                    section_id=hash(f"{section_name}_negative") % 10000,
                    topic_name=f"{section_name} Feature Importance (Negative)",
                    topic_id=hash(f"{section_name}_negative_fi") % 10000,
                    correlation_score=importance_data.get('model_score', 0.0),
                    negative_correlation=True,
                    sample_size=importance_data.get('sample_size', 0),
                    keywords=importance_scores  # Store as dict with word: importance_score
                )
            
            logger.info(f"Saved feature importance data to database: {len(positive_data)} positive, {len(negative_data)} negative sections")
        except Exception as e:
            logger.error(f"Error saving feature importance to database: {e}", exc_info=True)
    
    def _load_section_feature_importance_from_db(self) -> Dict:
        """Load section feature importance data from database"""
        from ml_analysis.models import SectionTopicCorrelation
        
        try:
            positive_data = {}
            negative_data = {}
            
            # Load positive data
            positive_correlations = SectionTopicCorrelation.objects.filter(
                topic_name__contains='Feature Importance (Positive)'
            )
            
            for corr in positive_correlations:
                section_name = corr.section_name
                keywords_dict = corr.keywords if isinstance(corr.keywords, dict) else {}
                
                positive_data[section_name] = {
                    'keywords': list(keywords_dict.keys())[:5],  # Top 5
                    'importance_scores': keywords_dict,
                    'model_score': corr.correlation_score,
                    'sample_size': corr.sample_size
                }
            
            # Load negative data
            negative_correlations = SectionTopicCorrelation.objects.filter(
                topic_name__contains='Feature Importance (Negative)'
            )
            
            for corr in negative_correlations:
                section_name = corr.section_name
                keywords_dict = corr.keywords if isinstance(corr.keywords, dict) else {}
                
                negative_data[section_name] = {
                    'keywords': list(keywords_dict.keys())[:5],  # Top 5
                    'importance_scores': keywords_dict,
                    'model_score': corr.correlation_score,
                    'sample_size': corr.sample_size
                }
            
            if positive_data or negative_data:
                logger.info(f"Loaded feature importance from database: {len(positive_data)} positive, {len(negative_data)} negative sections")
                return {
                    'positive': positive_data,
                    'negative': negative_data
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading feature importance from database: {e}", exc_info=True)
            return {}
    
    def _train_section_model(self, section_name: str, texts: List[str], scores: List[float], label: str, top_n: int = 5) -> Optional[Dict]:
        """
        Helper method to train a Random Forest model for a specific section and extract feature importance.
        
        Args:
            section_name: Name of the section
            texts: List of review texts
            scores: List of section scores
            label: 'positive' or 'negative'
            top_n: Number of top keywords to return
            
        Returns:
            Dict with keywords and importance scores, or None if training fails
        """
        try:
            # Preprocess texts
            preprocessed_texts = []
            for text in texts:
                preprocessed = self.preprocessor.preprocess_text(text)
                cleaned_text = preprocessed.get('cleaned_text_for_vader_bertopic', '')
                if cleaned_text:
                    preprocessed_texts.append(cleaned_text)
            
            if len(preprocessed_texts) < 10:
                return None
            
            # Create TF-IDF features
            tfidf_vectorizer = TfidfVectorizer(
                max_features=200,
                ngram_range=(1, 2),
                min_df=2,
                stop_words='english'
            )
            tfidf_features = tfidf_vectorizer.fit_transform(preprocessed_texts)
            feature_names = list(tfidf_vectorizer.get_feature_names_out())
            
            # Add BERTopic features if available
            # Note: BERTopic transform can be slow and shape issues, so we'll skip it for now
            # and use only TF-IDF features which are more reliable
            bertopic_features = None
            # Temporarily disabled BERTopic features due to shape compatibility issues
            # if BERTOPIC_AVAILABLE and self.topic_analyzer.model:
            #     try:
            #         topics, probs = self.topic_analyzer.model.transform(preprocessed_texts)
            #         if probs.shape[0] == len(preprocessed_texts):
            #             from scipy.sparse import csr_matrix
            #             bertopic_features = csr_matrix(probs)
            #     except Exception as e:
            #         logger.debug(f"BERTopic features failed: {e}")
            #         bertopic_features = None
            
            # Combine features
            if bertopic_features is not None and bertopic_features.shape[0] == tfidf_features.shape[0]:
                from scipy.sparse import hstack
                X = hstack([tfidf_features, bertopic_features])
                # Add topic feature names
                topic_feature_names = [f"topic_{i}" for i in range(bertopic_features.shape[1])]
                all_feature_names = feature_names + topic_feature_names
            else:
                # Use only TF-IDF if BERTopic features are not available or dimensions don't match
                X = tfidf_features
                all_feature_names = feature_names
                if bertopic_features is not None:
                    logger.warning(f"BERTopic features shape mismatch for {section_name} ({label}): TF-IDF={tfidf_features.shape}, BERTopic={bertopic_features.shape}. Using TF-IDF only.")
            
            y = np.array(scores)
            
            # Train Random Forest
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            from sklearn.ensemble import RandomForestRegressor
            rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            
            rf_model.fit(X_train, y_train)
            
            # Calculate evaluation metrics
            y_pred = rf_model.predict(X_test)
            
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))  # np is imported at top of file
            
            # Get feature importance
            feature_importance = rf_model.feature_importances_
            
            # Common words to filter out from Feedback Summary
            common_words_to_filter = {
                'feel', 'company', 'say', 'job', 'ive', 'provided',
                'there', 'work', 'employee', 'time', 'good', 'great',
                'well', 'need', 'make', 'get', 'would', 'could', 'should'
            }
            
            # Get top important features (words/topics that contribute to scores)
            top_indices = feature_importance.argsort()[-top_n*5:][::-1]  # Get more to filter from
            
            important_words = []
            for idx in top_indices:
                if idx < len(all_feature_names):
                    feature_name = all_feature_names[idx]
                    importance = float(feature_importance[idx])
                    # Skip topic features, focus on words
                    if not feature_name.startswith('topic_'):
                        # Filter out common words (case-insensitive)
                        if feature_name.lower() not in common_words_to_filter:
                            important_words.append({
                                'word': feature_name,
                                'importance': importance
                            })
            
            # Sort by importance and take top N
            important_words.sort(key=lambda x: x['importance'], reverse=True)
            top_words = important_words[:top_n]
            
            result = {
                'keywords': [w['word'] for w in top_words],
                'importance_scores': {w['word']: w['importance'] for w in top_words},
                'model_score': float(r2),
                'mae': float(mae),
                'rmse': float(rmse),
                'sample_size': len(texts)
            }
            
            # Log metrics to console/command prompt
            logger.info(f"Trained {label} model for {section_name}:")
            logger.info(f"  - Keywords extracted: {len(top_words)}")
            logger.info(f"  - R² Score: {r2:.4f}")
            logger.info(f"  - MAE (Mean Absolute Error): {mae:.4f}")
            logger.info(f"  - RMSE (Root Mean Squared Error): {rmse:.4f}")
            logger.info(f"  - Training samples: {len(texts)}")
            logger.info(f"  - Test samples: {len(y_test)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error training {label} model for {section_name}: {e}", exc_info=True)
            return None
    
    def train_all_models(self):
        """Train and save all models"""
        results = {}
        
        # Prepare training data (needed for both correlation and topic models)
        texts, target_ratings = self.correlation_analyzer.prepare_training_data()
        
        # Train topic model (BERTopic) on all training texts
        try:
            if len(texts) >= 2:
                topic_result = self.topic_analyzer.train_model(texts)
                results['topic'] = topic_result
            else:
                results['topic'] = {'error': 'Not enough training data for topic modeling'}
        except Exception as e:
            logger.error(f"Topic model training failed: {e}")
            results['topic'] = {'error': str(e)}
        
        # Train correlation model
        try:
            corr_result = self.correlation_analyzer.train_model()
            if 'error' not in corr_result:
                self.correlation_analyzer.save_correlations()
                # Add summary of saved correlations to results
                from ml_analysis.models import SectionTopicCorrelation
                total_correlations = SectionTopicCorrelation.objects.count()
                positive_correlations = SectionTopicCorrelation.objects.filter(correlation_score__gt=0.1).exclude(topic_name__icontains='Feature Importance').count()
                negative_correlations = SectionTopicCorrelation.objects.filter(correlation_score__lt=-0.1).exclude(topic_name__icontains='Feature Importance').count()
                corr_result['correlations_saved'] = {
                    'total': total_correlations,
                    'positive': positive_correlations,
                    'negative': negative_correlations
                }
                logger.info(f"Correlation training complete: {total_correlations} total, {positive_correlations} positive, {negative_correlations} negative")
                results['correlation'] = corr_result
            else:
                results['correlation'] = corr_result
        except Exception as e:
            logger.error(f"Correlation training failed: {e}", exc_info=True)
            results['correlation'] = {'error': str(e)}
        
        # Train section feature importance models (NEW)
        try:
            importance_result = self.train_section_feature_importance()
            results['section_importance'] = {
                'sections_trained': len(importance_result),
                'data': importance_result
            }
        except Exception as e:
            logger.error(f"Section feature importance training failed: {e}")
            results['section_importance'] = {'error': str(e)}
        
        # Save all models
        save_results = self.save_all_models()
        results['model_saves'] = save_results
        
        return results
    
    def get_lacking_features_summary(self) -> Dict:
        """
        Get summary of lacking features and supporting topics
        Returns:
        {
            'overall_rating': {
                'section_name': 'Overall Rating',
                'topics': [{'word': 'word', 'score': score}, ...]
            },
            'sections': {
                'section_name': {
                    'section_name': '...',
                    'topics': [{'word': 'word', 'score': score, 'correlation': corr}, ...],
                    'sample_size': int,
                    'avg_score': float
                }
            }
        }
        """
        from ml_analysis.models import SectionTopicCorrelation
        
        summary = {
            'overall_rating': None,
            'sections': {}
        }
        
        # Get Overall Rating topics (common across all sections)
        overall_rating = SectionTopicCorrelation.objects.filter(
            section_name='Overall Rating',
            topic_name='Overall Rating Topics'
        ).first()
        
        if overall_rating and overall_rating.keywords:
            # Filter stop words from keywords (case-insensitive)
            stop_words_to_filter = {'there', 'There', 'THERE'}
            # Convert keywords dict to list of word-score pairs, filtering stop words
            topics_list = [
                {'word': word, 'score': score}
                for word, score in sorted(overall_rating.keywords.items(), key=lambda x: x[1], reverse=True)
                if word.lower() not in stop_words_to_filter
            ]
            summary['overall_rating'] = {
                'section_name': 'Overall Rating',
                'keywords': {word: score for word, score in sorted(overall_rating.keywords.items(), key=lambda x: x[1], reverse=True) if word.lower() not in stop_words_to_filter},
                'topics': topics_list,
                'description': 'Common topics across all features'
            }
        
        # Get specialized topics for each section
        section_order = [
            'Compensation & Benefits',
            'Work-Life Balance',
            'Culture & Values',
            'Diversity & Inclusion',
            'Career Development',
            'Management & Leadership',
        ]
        
        for section_name in section_order:
            # Get the general topics correlation (from lacking texts)
            correlation = SectionTopicCorrelation.objects.filter(
                section_name=section_name,
                topic_name__contains='General Topics'
            ).first()
            
            if correlation and correlation.keywords:
                # Filter stop words from keywords (case-insensitive)
                stop_words_to_filter = {'there', 'There', 'THERE'}
                # Convert keywords dict to list with correlation, filtering stop words
                topics_list = [
                    {
                        'word': word,
                        'score': score,
                        'correlation': correlation.correlation_score
                    }
                    for word, score in sorted(correlation.keywords.items(), key=lambda x: x[1], reverse=True)
                    if word.lower() not in stop_words_to_filter
                ]
                
                summary['sections'][section_name] = {
                    'section_name': section_name,
                    'topics': topics_list,
                    'correlation': correlation.correlation_score,
                    'sample_size': correlation.sample_size,
                    'avg_score': correlation.correlation_score  # Using correlation as proxy for avg score
                }
        
        return summary
    
    def get_section_insights(self, response: QuestionnaireResponse) -> Dict:
        """Get insights about why certain sections scored low"""
        insights = {}
        
        # Map section names to target columns (reverse mapping)
        section_to_target = {
            'Work-Life Balance': 'work_life_balance',
            'Culture & Values': 'culture_values',
            'Diversity & Inclusion': 'diversity_inclusion',
            'Career Development': 'career_opp',
            'Compensation & Benefits': 'comp_benefits',
            'Management & Leadership': 'senior_mgmt',
        }
        
        # Get ALL section scores (including those not in mapping)
        section_scores = response.section_scores.all()
        
        # Get all sections that should be displayed (the 6 main sections)
        main_sections = ['Compensation & Benefits', 'Work-Life Balance', 'Culture & Values', 
                         'Diversity & Inclusion', 'Career Development', 'Management & Leadership']
        
        # Create insights for all main sections
        for section_name in main_sections:
            # Find the section score if it exists
            section_score = next((s for s in section_scores if s.section.name == section_name), None)
            
            # Map section name to target column for correlation lookup
            target_col = section_to_target.get(section_name)
            if not target_col:
                # Should not happen for main sections, but skip if not in mapping
                continue
            
            # If no score exists, still create insight but mark as no data
            if section_score:
                section_avg = section_score.average_score
            else:
                # Section hasn't been answered yet - create insight with no data
                insights[section_name] = {
                    'score': None,
                    'is_low': False,
                    'negative_topics': [],
                    'recommendations': [],
                    'no_data': True
                }
                continue
            
            # Find correlations for this target column (using the format from _calculate_correlations)
            # Correlation section_name format: "Work Life Balance" (from col.replace('_', ' ').title())
            correlation_section_name = target_col.replace('_', ' ').title()
            
            # Find "lacking" topics for this section
            correlations = SectionTopicCorrelation.objects.filter(
                section_name=correlation_section_name,
                topic_name__icontains='Lacking'
            ).order_by('correlation_score')
            
            # Get keywords from correlation data stored in database
            negative_topics = []
            for correlation in correlations:
                # Get keywords from the database (stored during save_correlations)
                keywords = correlation.keywords if hasattr(correlation, 'keywords') and correlation.keywords else []
                
                negative_topics.append({
                    'topic_name': correlation.topic_name,
                    'correlation': correlation.correlation_score,
                    'keywords': keywords
                })
            
            # If no correlations found in DB, try to get from correlation_data if available (in-memory)
            if not negative_topics and hasattr(self.correlation_analyzer, 'correlation_data'):
                lacking_key = f"lacking_{target_col}"
                if lacking_key in self.correlation_analyzer.correlation_data:
                    data = self.correlation_analyzer.correlation_data[lacking_key]
                    negative_topics.append({
                        'topic_name': data.get('topic_name', f"Lacking {correlation_section_name}"),
                        'correlation': data.get('correlation', 0.0),
                        'keywords': data.get('keywords', [])
                    })
            
            insights[section_name] = {
                'score': section_avg,
                'is_low': section_avg < 3.0,
                'negative_topics': negative_topics,
                'recommendations': self._generate_recommendations(section_name, negative_topics)
            }
        
        return insights
    
    def get_section_importance_analysis(self) -> Optional[Dict]:
        """
        Train Random Forest model to predict overall_rating from section scores
        Returns feature importance showing which sections contribute most to positive/high overall ratings
        
        This model uses all 6 ML-essential sections as features to predict overall rating.
        Only uses responses with high overall ratings (>= 4.0) to identify which sections
        contribute most to positive satisfaction.
        """
        try:
            from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection
            
            logger.info("Starting section importance analysis for positive/high ratings...")
            
            # Get all responses with section scores
            all_responses = QuestionnaireResponse.objects.filter(
                is_complete=True
            ).prefetch_related('section_scores__section')
            
            total_responses = all_responses.count()
            logger.info(f"Found {total_responses} complete responses")
            
            if total_responses < 10:
                logger.warning(f"Not enough responses for analysis: {total_responses} < 10")
                return None
            
            # Filter to only high overall ratings (>= 4.0)
            # First, calculate overall rating for each response
            high_rating_responses = []
            for response in all_responses:
                section_scores_dict = {}
                for section_score in response.section_scores.all():
                    section_scores_dict[section_score.section.name] = section_score.average_score
                
                if not section_scores_dict:
                    continue
                
                overall_rating = float(np.mean(list(section_scores_dict.values())))
                if overall_rating >= 4.0:  # Only high ratings
                    high_rating_responses.append(response)
            
            responses = high_rating_responses
            high_rating_count = len(responses)
            logger.info(f"Filtered to {high_rating_count} responses with overall rating >= 4.0")
            
            if high_rating_count < 10:
                logger.warning(f"Not enough high-rating responses for analysis: {high_rating_count} < 10")
                return None
            
            # Prepare data: section scores as features, overall_rating as target
            section_names = [
                'Compensation & Benefits',
                'Work-Life Balance',
                'Culture & Values',
                'Diversity & Inclusion',
                'Career Development',
                'Management & Leadership'
            ]
            
            X_data = []
            y_data = []
            
            # First pass: collect all section scores to calculate means for missing values
            all_section_scores = {name: [] for name in section_names}
            for response in responses:
                for section_score in response.section_scores.all():
                    if section_score.section.name in all_section_scores:
                        all_section_scores[section_score.section.name].append(section_score.average_score)
            
            # Calculate mean for each section (for filling missing values)
            section_means = {}
            for name, scores in all_section_scores.items():
                if scores:
                    section_means[name] = float(np.mean(scores))
                    logger.debug(f"Section {name}: mean = {section_means[name]:.2f}, count = {len(scores)}")
                else:
                    section_means[name] = 3.0  # Default neutral score
                    logger.warning(f"Section {name}: no data, using default mean = 3.0")
            
            # Second pass: build feature vectors and target values
            for response in responses:
                # Get section scores for this response
                section_scores_dict = {}
                for section_score in response.section_scores.all():
                    section_scores_dict[section_score.section.name] = section_score.average_score
                
                # Calculate overall rating (average of all section scores that exist)
                if not section_scores_dict:
                    continue  # Skip if no section scores
                
                overall_rating = float(np.mean(list(section_scores_dict.values())))
                
                # Create feature vector (section scores in order, fill missing with mean)
                feature_vector = []
                for section_name in section_names:
                    if section_name in section_scores_dict:
                        feature_vector.append(float(section_scores_dict[section_name]))
                    else:
                        # Fill missing section with mean value
                        feature_vector.append(section_means[section_name])
                
                # Validate feature vector
                if len(feature_vector) != len(section_names):
                    logger.warning(f"Invalid feature vector length: {len(feature_vector)} != {len(section_names)}")
                    continue
                
                # Check for NaN or invalid values
                if any(np.isnan(val) or np.isinf(val) for val in feature_vector):
                    logger.warning(f"Invalid values in feature vector: {feature_vector}")
                    continue
                
                if np.isnan(overall_rating) or np.isinf(overall_rating):
                    logger.warning(f"Invalid overall rating: {overall_rating}")
                    continue
                
                X_data.append(feature_vector)
                y_data.append(overall_rating)
            
            logger.info(f"Prepared {len(X_data)} valid data points for training")
            
            if len(X_data) < 10:
                logger.warning(f"Not enough valid data points: {len(X_data)} < 10")
                return None
            
            # Convert to numpy arrays
            X = np.array(X_data, dtype=np.float64)
            y = np.array(y_data, dtype=np.float64)
            
            # Validate arrays
            if X.shape[1] != len(section_names):
                logger.error(f"Feature matrix shape mismatch: {X.shape[1]} != {len(section_names)}")
                return None
            
            logger.info(f"Training Random Forest model on {X.shape[0]} samples with {X.shape[1]} features")
            
            # Train Random Forest model
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=None,
                min_samples_split=2,
                random_state=42,
                n_jobs=-1,
                verbose=0
            )
            
            logger.info("Fitting Random Forest model...")
            model.fit(X_train, y_train)
            logger.info("Model training completed")
            
            # Get feature importance
            feature_importance = model.feature_importances_
            
            # Validate feature importance
            if len(feature_importance) != len(section_names):
                logger.error(f"Feature importance length mismatch: {len(feature_importance)} != {len(section_names)}")
                return None
            
            # Create importance dictionary
            importance_dict = {}
            for i, section_name in enumerate(section_names):
                importance_dict[section_name] = float(feature_importance[i])
                logger.debug(f"{section_name}: importance = {feature_importance[i]:.4f}")
            
            # Sort by importance (descending)
            sorted_importance = sorted(
                importance_dict.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Calculate model performance
            y_pred = model.predict(X_test)
            from sklearn.metrics import r2_score, mean_absolute_error
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            logger.info(f"Model performance: R² = {r2:.4f}, MAE = {mae:.4f}")
            
            result = {
                'feature_importance': dict(sorted_importance),
                'sorted_sections': [item[0] for item in sorted_importance],
                'sorted_importance': [item[1] for item in sorted_importance],
                'model_performance': {
                    'r2_score': float(r2),
                    'mae': float(mae)
                }
            }
            
            logger.info(f"Section importance analysis completed successfully. Top section: {sorted_importance[0][0]} ({sorted_importance[0][1]:.4f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_section_importance_analysis: {e}", exc_info=True)
            return None
    
    def get_section_feature_importance_topics(self, sentiment_label: str, top_n: int = 5) -> List[Dict]:
        """
        Get topics from section feature importance models (trained during pipeline).
        Uses Random Forest feature importance to identify words that contribute to high/low scores.
        
        Args:
            sentiment_label: 'positive' (strengths) or 'negative' (weaknesses)
            top_n: Number of top topics/keywords to return per section
            
        Returns:
            List of topic dictionaries with section, keywords, and frequency
        """
        # Check if feature importance data is available
        if not hasattr(self, 'section_feature_importance') or not self.section_feature_importance:
            logger.warning("Section feature importance data not available. Train models first.")
            return []
        
        # Get the correct data based on sentiment label
        if sentiment_label == 'positive':
            importance_data_dict = self.section_feature_importance.get('positive', {})
        elif sentiment_label == 'negative':
            importance_data_dict = self.section_feature_importance.get('negative', {})
        else:
            logger.warning(f"Unknown sentiment_label: {sentiment_label}")
            return []
        
        if not importance_data_dict:
            logger.warning(f"No {sentiment_label} feature importance data available. Train models first.")
            return []
        
        topics_list = []
        
        for section_name, importance_data in importance_data_dict.items():
            keywords = importance_data.get('keywords', [])[:top_n]
            importance_scores = importance_data.get('importance_scores', {})
            sample_size = importance_data.get('sample_size', 0)
            
            if keywords:
                topics_list.append({
                    'section': section_name,
                    'topic_name': f"{section_name} {sentiment_label.title()} Topics",
                    'keywords': keywords,
                    'keyword_scores': {kw: importance_scores.get(kw, 0.0) for kw in keywords},
                    'frequency': sample_size,
                    'sentiment': sentiment_label
                })
        
        logger.info(f"Retrieved {len(topics_list)} {sentiment_label} section topics from feature importance models")
        return topics_list
    
    def get_sentiment_based_topics(self, sentiment_label: str, top_n: int = 5) -> List[Dict]:
        """
        Extract topics from responses based on section performance scores
        - For 'positive': Get responses with HIGH scores (>= 4.0) for each section (strengths)
        - For 'negative': Get responses with LOW scores (< 3.0) for each section (weaknesses)
        Uses TF-IDF and BERTopic to extract section-specific topics
        
        Args:
            sentiment_label: 'positive' (strengths) or 'negative' (weaknesses)
            top_n: Number of top topics/keywords to return per section
            
        Returns:
            List of topic dictionaries with section, keywords, and frequency
        """
        from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection
        
        try:
            section_names = [
                'Compensation & Benefits',
                'Work-Life Balance',
                'Culture & Values',
                'Diversity & Inclusion',
                'Career Development',
                'Management & Leadership'
            ]
            
            # Get section objects
            sections = QuestionnaireSection.objects.filter(name__in=section_names)
            section_dict = {s.name: s for s in sections}
            
            topics_list = []
            
            # For each section, find responses with high/low scores for that specific section
            for section_name in section_names:
                if section_name not in section_dict:
                    continue
                
                section = section_dict[section_name]
                
                # Filter responses based on sentiment_label
                if sentiment_label == 'positive':
                    # Get responses with HIGH scores (>= 4.0) for this specific section
                    section_scores = SectionScore.objects.filter(
                        section=section,
                        average_score__gte=4.0,
                        response__is_complete=True
                    ).select_related('response').prefetch_related('response__section_scores__section')
                elif sentiment_label == 'negative':
                    # Get responses with LOW scores (< 3.0) for this specific section
                    section_scores = SectionScore.objects.filter(
                        section=section,
                        average_score__lt=3.0,
                        response__is_complete=True
                    ).select_related('response').prefetch_related('response__section_scores__section')
                else:
                    # For neutral, skip or use a different threshold
                    continue
                
                if section_scores.count() < 3:
                    logger.debug(f"Not enough responses for {section_name} ({sentiment_label}): {section_scores.count()}")
                    continue
                
                # Collect review texts for this section's high/low scoring responses
                texts = []
                for section_score in section_scores:
                    response = section_score.response
                    if response.review and response.review.strip():
                        texts.append(response.review)
                
                if len(texts) < 3:
                    continue
                
                # Preprocess texts
                preprocessed_texts = []
                for text in texts:
                    preprocessed = self.preprocessor.preprocess_text(text)
                    cleaned_text = preprocessed.get('cleaned_text_for_vader_bertopic', '')
                    if cleaned_text:
                        preprocessed_texts.append(cleaned_text)
                
                if len(preprocessed_texts) < 3:
                    continue
                
                # Extract topics using TF-IDF
                keywords = []
                try:
                    vectorizer = TfidfVectorizer(
                        max_features=100,
                        ngram_range=(1, 2),
                        min_df=2,  # Word must appear in at least 2 documents
                        stop_words='english'
                    )
                    
                    tfidf_matrix = vectorizer.fit_transform(preprocessed_texts)
                    feature_names = vectorizer.get_feature_names_out()
                    
                    # Get average TF-IDF scores across all documents
                    mean_scores = np.array(tfidf_matrix.mean(axis=0)).flatten()
                    
                    # Get top keywords by TF-IDF score
                    top_indices = mean_scores.argsort()[-top_n*3:][::-1]  # Get more for BERTopic filtering
                    tfidf_keywords = []
                    for idx in top_indices:
                        keyword = feature_names[idx]
                        score = float(mean_scores[idx])
                        tfidf_keywords.append({'word': keyword, 'score': score})
                    
                    # Also try BERTopic if available
                    bertopic_keywords = []
                    if BERTOPIC_AVAILABLE and self.topic_analyzer.model:
                        try:
                            # Use BERTopic to find topics in these texts
                            topics, probs = self.topic_analyzer.model.transform(preprocessed_texts)
                            
                            # Get unique topics
                            unique_topics = set(topics.flatten())
                            for topic_id in unique_topics:
                                if topic_id >= 0:  # Skip outlier topic (-1)
                                    topic_info = self.topic_analyzer.model.get_topic(topic_id)
                                    if topic_info:
                                        # Get top words from this topic
                                        for word, score in topic_info[:top_n]:
                                            bertopic_keywords.append({'word': word, 'score': float(score)})
                        except Exception as e:
                            logger.debug(f"BERTopic extraction failed for {section_name}: {e}")
                    
                    # Combine TF-IDF and BERTopic keywords, prioritizing unique words
                    all_keywords_dict = {}
                    for kw in tfidf_keywords:
                        word = kw['word'].lower()
                        if word not in all_keywords_dict:
                            all_keywords_dict[word] = kw['score']
                        else:
                            # Average the scores if word appears in both
                            all_keywords_dict[word] = (all_keywords_dict[word] + kw['score']) / 2
                    
                    for kw in bertopic_keywords:
                        word = kw['word'].lower()
                        if word not in all_keywords_dict:
                            all_keywords_dict[word] = kw['score']
                        else:
                            # Boost score if word appears in both TF-IDF and BERTopic
                            all_keywords_dict[word] = all_keywords_dict[word] * 1.5
                    
                    # Sort by score and take top N
                    sorted_keywords = sorted(all_keywords_dict.items(), key=lambda x: x[1], reverse=True)
                    keywords = [word for word, score in sorted_keywords[:top_n]]
                    
                except Exception as e:
                    logger.warning(f"Error extracting topics for {section_name} ({sentiment_label}): {e}")
                    continue
                
                if keywords:
                    topics_list.append({
                        'section': section_name,
                        'topic_name': f"{section_name} {sentiment_label.title()} Topics",
                        'keywords': keywords,
                        'frequency': len(texts),
                        'sentiment': sentiment_label
                    })
                    logger.info(f"Extracted {len(keywords)} keywords for {section_name} ({sentiment_label}) from {len(texts)} responses")
            
            logger.info(f"Extracted {len(topics_list)} section topics for {sentiment_label} sentiment")
            return topics_list
            
        except Exception as e:
            logger.error(f"Error in get_sentiment_based_topics: {e}", exc_info=True)
            return []
    
    def _generate_recommendations(self, section_name: str, negative_topics: List[Dict]) -> List[str]:
        """Generate recommendations based on negative topics"""
        recommendations = []
        
        if not negative_topics:
            return recommendations
        
        # Section-specific recommendations
        section_recommendations = {
            'Compensation & Benefits': [
                'Consider reviewing salary structures and benefits packages',
                'Conduct market research on competitive compensation',
                'Implement transparent pay scales and promotion criteria'
            ],
            'Work-Life Balance': [
                'Review workload distribution and deadlines',
                'Implement flexible working arrangements',
                'Encourage proper use of vacation and sick leave'
            ],
            'Work Environment': [
                'Assess workplace safety and comfort',
                'Ensure adequate resources and tools are available',
                'Promote inclusive and positive culture initiatives'
            ],
            'Career Development': [
                'Create clear career progression paths',
                'Provide regular training and skill development opportunities',
                'Implement mentorship programs'
            ],
            'Management & Leadership': [
                'Improve communication channels and frequency',
                'Provide management training and support',
                'Create open feedback mechanisms'
            ]
        }
        
        # Add general recommendations based on topics
        for topic in negative_topics:
            if 'workload' in ' '.join(topic.get('keywords', [])).lower():
                recommendations.append('Address workload concerns and resource allocation')
            elif 'communication' in ' '.join(topic.get('keywords', [])).lower():
                recommendations.append('Improve communication processes and transparency')
            elif 'recognition' in ' '.join(topic.get('keywords', [])).lower():
                recommendations.append('Implement better recognition and reward systems')
        
        # Add section-specific recommendations
        if section_name in section_recommendations:
            recommendations.extend(section_recommendations[section_name][:2])
        
        return list(set(recommendations))  # Remove duplicates
