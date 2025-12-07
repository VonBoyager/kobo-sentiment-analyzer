from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from frontend.models import QuestionnaireResponse, QuestionnaireSection, QuestionnaireQuestion, SectionScore
from ml_analysis.models import TrainingData
from ml_analysis.services import SentimentAnalyzer
import pandas as pd
import os
from django.db import transaction
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Load employee feedback dataset into the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='../employee_feedback_dataset.csv',
            help='Path to the CSV file'
        )
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username/tenant to load data for'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        username = options['username']
        batch_size = options['batch_size']

        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        # Read CSV file
        self.stdout.write(f'Reading CSV file: {csv_file}')
        try:
            # Try reading with error handling for malformed lines
            try:
                df = pd.read_csv(csv_file, engine='python', on_bad_lines='skip')
            except TypeError:
                # Older pandas versions don't have on_bad_lines, use error_bad_lines instead
                try:
                    df = pd.read_csv(csv_file, engine='python', error_bad_lines=False, warn_bad_lines=False)
                except TypeError:
                    # Even older versions - just read normally
                    df = pd.read_csv(csv_file, engine='python')
            
            self.stdout.write(f'Loaded {len(df)} records from CSV')
            
            # Normalize column names (strip whitespace and handle potential BOM)
            df.columns = [c.strip() for c in df.columns]
            
            # Smart column mapping for review_date (handle case differences)
            review_date_col = None
            for col in df.columns:
                if col.lower() == 'review_date':
                    review_date_col = col
                    break
            
            if review_date_col:
                # Standardize the column name
                df.rename(columns={review_date_col: 'review_date'}, inplace=True)
            
            # Check for required columns
            required_cols = ['free_text_box']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.stdout.write(
                    self.style.ERROR(f'Missing required columns: {", ".join(missing_cols)}')
                )
                self.stdout.write(f'Available columns: {", ".join(list(df.columns)[:15])}')
                return
            
            # Check for mandatory review_date column
            if 'review_date' not in df.columns:
                self.stdout.write(
                    self.style.ERROR('❌ ERROR: "review_date" column is missing. This field is required for data upload.')
                )
                self.stdout.write('Please ensure your CSV has a column named "review_date" (case-insensitive).')
                self.stdout.write(f'Found columns: {", ".join(list(df.columns))}')
                return
            
            if len(df) == 0:
                self.stdout.write(
                    self.style.ERROR('CSV file is empty or contains no valid data')
                )
                return
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {e}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            return

        # Get the specified user/tenant
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Loading data for user: {user.username}')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist. Please create the user first.')
            )
            return

        # Initialize sentiment analyzer
        sentiment_analyzer = SentimentAnalyzer()

        # Map CSV columns to questionnaire sections (only ML-essential sections)
        # Updated to match actual CSV column names from employee_feedback_dataset.csv
        section_mapping = {
            'Compensation & Benefits': ['salary_fairness', 'compensation_competitiveness', 'benefits_adequacy'],
            'Work-Life Balance': ['workload_balance', 'schedule_flexibility', 'leave_policies_adequacy'],
            'Culture & Values': ['mission_values_meaningful', 'positive_inclusive_culture', 'Company_acts_ethically', 'encouragement_of_innovation'],
            'Diversity & Inclusion': ['positive_inclusive_culture', 'colleague_respect_support', 'team_collaboration_effectiveness', 'constructive_conflict_management'],
            'Career Development': ['professional_growth_opportunities', 'training_skill_development', 'clear_career_paths'],
            'Management & Leadership': ['manager_communication_clarity', 'raising_concerns_comfortability', 'manager_support_for_employees']
        }

        # Process data in batches
        total_processed = 0
        total_created = 0

        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i + batch_size]
            self.stdout.write(f'Processing batch {i//batch_size + 1}: records {i+1} to {min(i+batch_size, len(df))}')

            with transaction.atomic():
                for _, row in batch_df.iterrows():
                    try:
                        # Parse review_date
                        submitted_at = timezone.now()
                        if 'review_date' in row and pd.notna(row['review_date']):
                            try:
                                # Try parsing various date formats
                                review_date_str = str(row['review_date']).strip()
                                if review_date_str:
                                    # Try common date formats
                                    date_formats = [
                                        '%Y-%m-%d',
                                        '%Y-%m-%d %H:%M:%S',
                                        '%Y/%m/%d',
                                        '%m/%d/%Y',
                                        '%d/%m/%Y',
                                        '%d-%m-%Y',
                                        '%m-%d-%Y',
                                        '%Y-%m-%dT%H:%M:%S',
                                        '%Y-%m-%dT%H:%M:%S.%f',
                                        '%B %d, %Y',  # e.g. January 1, 2024
                                        '%b %d, %Y',  # e.g. Jan 1, 2024
                                    ]
                                    
                                    parsed_date = None
                                    for fmt in date_formats:
                                        try:
                                            parsed_date = datetime.strptime(review_date_str, fmt)
                                            break
                                        except ValueError:
                                            continue
                                    
                                    if parsed_date:
                                        # Convert to timezone-aware datetime
                                        if timezone.is_naive(parsed_date):
                                            submitted_at = timezone.make_aware(parsed_date)
                                        else:
                                            submitted_at = parsed_date
                                    else:
                                        # Try pandas to_datetime as fallback
                                        try:
                                            parsed_date = pd.to_datetime(review_date_str)
                                            if pd.notna(parsed_date):
                                                py_date = parsed_date.to_pydatetime()
                                                if timezone.is_naive(py_date):
                                                    submitted_at = timezone.make_aware(py_date)
                                                else:
                                                    submitted_at = py_date
                                            else:
                                                raise ValueError("Pandas returned NaT")
                                        except Exception as parse_err:
                                            # STRICT VALIDATION: If a date is provided but cannot be parsed, fail the row
                                            # rather than defaulting to now(), which corrupts trend data.
                                            self.stdout.write(
                                                self.style.ERROR(f'❌ CRITICAL: Could not parse date "{review_date_str}" for row {row.get("uid", "unknown")}. Error: {str(parse_err)}')
                                            )
                                            continue # Skip this row instead of saving with wrong date
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'❌ Error parsing review_date for row {row.get("uid", "unknown")}: {e}')
                                )
                                continue # Skip this row
                        else:
                             # No review_date provided at all - this should have been caught by early check
                             # but if it slipped through, we treat as error if we want strict enforcement
                             self.stdout.write(
                                self.style.ERROR(f'❌ Missing review_date for row {row.get("uid", "unknown")}')
                             )
                             continue
                        
                        # Create questionnaire response with parsed date
                        response = QuestionnaireResponse.objects.create(
                            user=user,
                            review=row['free_text_box'] if pd.notna(row['free_text_box']) else '',
                            is_complete=True,
                            submitted_at=submitted_at
                        )

                        # Calculate section scores
                        for section_name, columns in section_mapping.items():
                            # Get section scores for this section
                            section_scores = []
                            for col in columns:
                                if col in row and pd.notna(row[col]):
                                    section_scores.append(row[col])
                            
                            if section_scores:
                                # Calculate average score
                                avg_score = sum(section_scores) / len(section_scores)
                                
                                # Get or create section
                                section, _ = QuestionnaireSection.objects.get_or_create(
                                    name=section_name,
                                    defaults={'description': f'{section_name} questions', 'order': 0}
                                )
                                
                                # Create section score
                                SectionScore.objects.create(
                                    response=response,
                                    section=section,
                                    average_score=avg_score,
                                    total_questions=len(section_scores)
                                )

                        # Analyze sentiment using VADER
                        sentiment_result = None
                        if pd.notna(row['free_text_box']) and row['free_text_box'].strip():
                            sentiment_result = sentiment_analyzer.analyze_text(row['free_text_box'])
                            
                            # Create sentiment analysis
                            from ml_analysis.models import SentimentAnalysis
                            SentimentAnalysis.objects.create(
                                response=response,
                                compound_score=sentiment_result['compound'],
                                positive_score=sentiment_result['pos'],
                                negative_score=sentiment_result['neg'],
                                neutral_score=sentiment_result['neu'],
                                sentiment_label=sentiment_result['sentiment'],
                                confidence=sentiment_result['confidence'],
                                text_length=len(row['free_text_box'])
                            )

                        # Create training data entry
                        TrainingData.objects.create(
                            text=row['free_text_box'] if pd.notna(row['free_text_box']) else '',
                            sentiment_label=sentiment_result['sentiment'] if sentiment_result else 'neutral',
                            section_scores={section_name: sum([row[col] for col in columns if col in row and pd.notna(row[col])]) / len([col for col in columns if col in row and pd.notna(row[col])]) for section_name, columns in section_mapping.items() if any(col in row and pd.notna(row[col]) for col in columns)},
                            source='dataset_import',
                            is_verified=True
                        )

                        total_created += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Error processing row {row.get("uid", "unknown")}: {e}')
                        )
                        continue

            total_processed += len(batch_df)
            self.stdout.write(f'Processed {total_processed}/{len(df)} records')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {total_created} records for user {username}'
            )
        )

        # Display summary statistics
        self.stdout.write('\nDataset Summary:')
        self.stdout.write(f'Total responses: {QuestionnaireResponse.objects.filter(user=user).count()}')
        self.stdout.write(f'Total sentiment analyses: {SentimentAnalysis.objects.filter(response__user=user).count()}')
        self.stdout.write(f'Total training data: {TrainingData.objects.filter(source="dataset_import").count()}')
        
        # Show sentiment distribution
        sentiment_counts = {}
        for analysis in SentimentAnalysis.objects.filter(response__user=user):
            sentiment = analysis.sentiment_label
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        self.stdout.write('\nSentiment Distribution:')
        for sentiment, count in sentiment_counts.items():
            self.stdout.write(f'  {sentiment}: {count}')

        # Show section score statistics
        self.stdout.write('\nSection Score Statistics:')
        for section_name in section_mapping.keys():
            scores = SectionScore.objects.filter(
                section__name=section_name,
                response__user=user
            ).values_list('average_score', flat=True)
            
            if scores:
                avg_score = sum(scores) / len(scores)
                self.stdout.write(f'  {section_name}: {avg_score:.2f} (n={len(scores)})')
