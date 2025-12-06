"""
Text preprocessing utilities extracted from notebook
Handles cleaning, tokenization, stop word removal, and lemmatization
"""
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging

logger = logging.getLogger(__name__)

# Download NLTK data if needed
def _ensure_nltk_data():
    """Ensure all required NLTK data is downloaded"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
    
    try:
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        nltk.download('omw-1.4', quiet=True)

# Initialize NLTK data on module import
_ensure_nltk_data()

# Initialize stop words and lemmatizer
_stop_words = set(stopwords.words('english'))
# Add custom stop words - convert to lowercase for case-insensitive matching
_stop_words.add('there')
_stop_words.add('ive')
_stop_words.add('im')
_stop_words.add('feel')
_lemmatizer = WordNetLemmatizer()


class TextPreprocessor:
    """Text preprocessing pipeline from notebook"""
    
    @staticmethod
    def clean_text_initial(text: str) -> str:
        """
        Initial text cleaning: lowercase, remove special characters and numbers
        """
        if not text or not isinstance(text, str):
            return ""
        
        text = str(text).lower()
        # Remove special characters (keep only letters and spaces)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        return text
    
    @staticmethod
    def tokenize_text(text: str) -> list:
        """Tokenize text into words"""
        if not text:
            return []
        return word_tokenize(text)
    
    @staticmethod
    def remove_stopwords(tokens: list) -> list:
        """Remove stop words from tokens (case-insensitive)"""
        # Convert stop words to lowercase set for case-insensitive matching
        stop_words_lower = {word.lower() for word in _stop_words}
        return [word for word in tokens if word.lower() not in stop_words_lower]
    
    @staticmethod
    def lemmatize_tokens(tokens: list) -> list:
        """Lemmatize tokens to their base form"""
        return [_lemmatizer.lemmatize(word) for word in tokens]
    
    @classmethod
    def preprocess_text(cls, text: str) -> dict:
        """
        Complete preprocessing pipeline
        Returns dict with:
        - cleaned_text_for_vader_bertopic: string for VADER/BERTopic
        - cleaned_tokens_for_tfidf: list of tokens for TF-IDF
        """
        if not text:
            return {
                'cleaned_text_for_vader_bertopic': '',
                'cleaned_tokens_for_tfidf': []
            }
        
        # Step 1: Initial cleaning
        cleaned = cls.clean_text_initial(text)
        
        # Step 2: Tokenization
        tokens = cls.tokenize_text(cleaned)
        
        # Step 3: Remove stop words
        filtered_tokens = cls.remove_stopwords(tokens)
        
        # Step 4: Lemmatization
        lemmatized_tokens = cls.lemmatize_tokens(filtered_tokens)
        
        # Step 5: Create final outputs
        cleaned_text = ' '.join(lemmatized_tokens)
        
        return {
            'cleaned_text_for_vader_bertopic': cleaned_text,
            'cleaned_tokens_for_tfidf': lemmatized_tokens
        }

