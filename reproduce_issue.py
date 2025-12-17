import os
import sys
import django
from django.conf import settings
from django.utils import timezone
from django.db.models import Case, When, IntegerField
from django.db.models.functions import ExtractYear, ExtractMonth

# Add the sentiment_analyzer directory to sys.path so we can import modules from it
sys.path.append(os.path.join(os.getcwd(), 'sentiment_analyzer'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_analyzer.settings')
django.setup()

from frontend.models import QuestionnaireResponse

def test_response_creation():
    print("Testing QuestionnaireResponse creation...")
    
    # Create a response without specifying submitted_at
    try:
        response = QuestionnaireResponse.objects.create(
            review="Test review for date checking",
            is_complete=True
        )
        
        print(f"Response created. ID: {response.id}")
        print(f"submitted_at: {response.submitted_at}")
        
        if response.submitted_at:
            print("SUCCESS: submitted_at was automatically set.")
        else:
            print("FAILURE: submitted_at is None.")
            
    except Exception as e:
        print(f"Error creating response: {e}")
        return

    # Test Quarter Calculation Logic
    print("\nTesting Quarter Calculation...")
    
    try:
        qs = QuestionnaireResponse.objects.filter(id=response.id).annotate(
            year=ExtractYear('submitted_at'),
            month=ExtractMonth('submitted_at'),
            quarter=Case(
                When(month__lte=3, then=1),
                When(month__lte=6, then=2),
                When(month__lte=9, then=3),
                default=4,
                output_field=IntegerField()
            )
        )
        
        annotated_response = qs.first()
        if annotated_response:
            print(f"Year: {annotated_response.year}")
            print(f"Month: {annotated_response.month}")
            print(f"Quarter: {annotated_response.quarter}")
            print(f"Key: {annotated_response.year}-Q{annotated_response.quarter}")
            
            # Additional check: what if month is None? (shouldn't be if submitted_at is set)
            if annotated_response.month is None:
                 print("WARNING: Month is None, which suggests something weird with date extraction.")
        else:
            print("Could not retrieve annotated response.")

    except Exception as e:
        print(f"Error in annotation: {e}")

if __name__ == "__main__":
    test_response_creation()