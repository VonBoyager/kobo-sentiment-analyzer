from django.core.management.base import BaseCommand
from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection
import random


class Command(BaseCommand):
    help = 'Populate missing section scores for existing questionnaire responses with random values (1-5)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate all section scores even if they already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        # Get all ML-essential sections
        ml_sections = QuestionnaireSection.objects.filter(
            name__in=[
                'Compensation & Benefits',
                'Work-Life Balance',
                'Culture & Values',
                'Diversity & Inclusion',
                'Career Development',
                'Management & Leadership'
            ]
        )
        
        if not ml_sections.exists():
            self.stdout.write(self.style.ERROR('No ML-essential sections found. Please run populate_questionnaire first.'))
            return
        
        self.stdout.write(f'Found {ml_sections.count()} ML-essential sections')
        
        # Get all complete responses
        responses = QuestionnaireResponse.objects.filter(is_complete=True)
        total_responses = responses.count()
        
        self.stdout.write(f'Processing {total_responses} complete responses...')
        
        missing_count = 0
        created_count = 0
        responses_processed = 0
        
        for response in responses:
            responses_processed += 1
            if responses_processed % 500 == 0:
                self.stdout.write(f'Processed {responses_processed}/{total_responses} responses...')
            
            # Get existing section scores for this response
            existing_sections = set(
                response.section_scores.values_list('section__name', flat=True)
            )
            
            # Check which sections are missing
            for section in ml_sections:
                if section.name not in existing_sections or force:
                    # If forcing and section exists, delete it first
                    if force and section.name in existing_sections:
                        SectionScore.objects.filter(
                            response=response,
                            section=section
                        ).delete()
                    
                    # Generate random score between 1.0 and 5.0
                    random_score = round(random.uniform(1.0, 5.0), 2)
                    
                    # Create the missing section score
                    SectionScore.objects.create(
                        response=response,
                        section=section,
                        average_score=random_score,
                        total_questions=3  # Assuming 3 questions per section
                    )
                    missing_count += 1
                    created_count += 1
                    
                    if created_count <= 10:  # Show first 10 for debugging
                        action = 'Regenerated' if force and section.name in existing_sections else 'Created'
                        self.stdout.write(
                            f'  {action} {section.name} score ({random_score:.2f}) for response {response.id}'
                        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} missing section scores across {missing_count} responses'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('All responses already have all required section scores.'))
