"""
Management command to update review dates from CSV file
"""
from django.core.management.base import BaseCommand
from frontend.models import QuestionnaireResponse
import pandas as pd
from django.utils import timezone
from datetime import datetime
from django.db import transaction

class Command(BaseCommand):
    help = 'Update review dates from CSV file based on UID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='../../employee_feedback_dataset.csv',
            help='Path to the CSV file'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Read CSV
        self.stdout.write(f'Reading CSV file: {csv_file}')
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV: {e}'))
            return
        
        if 'uid' not in df.columns or 'review_date' not in df.columns:
            self.stdout.write(self.style.ERROR('CSV must contain uid and review_date columns'))
            return
        
        # Create mapping of uid to review_date
        uid_to_date = {}
        for _, row in df.iterrows():
            uid = str(row['uid']).strip()
            review_date_str = str(row['review_date']).strip() if pd.notna(row['review_date']) else None
            
            if review_date_str:
                # Try parsing the date
                date_formats = [
                    '%Y-%m-%d',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(review_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    try:
                        parsed_date = pd.to_datetime(review_date_str).to_pydatetime()
                    except:
                        continue
                
                if parsed_date:
                    uid_to_date[uid] = timezone.make_aware(parsed_date)
        
        self.stdout.write(f'Found {len(uid_to_date)} dates in CSV')
        
        # Update responses
        updated_count = 0
        with transaction.atomic():
            # Get all responses
            responses = QuestionnaireResponse.objects.all()
            
            for response in responses:
                # Try to match by UID stored in review or other field
                # Since we don't have UID stored directly, we'll need to match by order
                # Or we can store UID in a custom field
                # For now, let's try to match by the order in CSV
                pass
        
        # Match responses by order (assuming they were loaded in CSV order)
        # Get responses ordered by ID (creation order)
        responses = QuestionnaireResponse.objects.filter(is_complete=True).order_by('id')
        
        self.stdout.write(f'Found {len(responses)} responses in database')
        self.stdout.write(f'Updating responses with dates from CSV...')
        
        updated = 0
        skipped = 0
        
        with transaction.atomic():
            for idx, response in enumerate(responses):
                if idx < len(df):
                    row = df.iloc[idx]
                    uid = str(row['uid']).strip()
                    
                    if uid in uid_to_date:
                        old_date = response.submitted_at
                        response.submitted_at = uid_to_date[uid]
                        response.save(update_fields=['submitted_at'])
                        updated += 1
                        
                        if updated <= 5:  # Show first few updates
                            self.stdout.write(f'  Updated response {response.id}: {old_date} -> {uid_to_date[uid]}')
                        
                        if updated % 500 == 0:
                            self.stdout.write(f'Updated {updated} responses...')
                    else:
                        skipped += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully updated {updated} responses with review dates from CSV'
        ))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'Skipped {skipped} responses (no date in CSV)'))

