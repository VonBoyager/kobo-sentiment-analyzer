from django.core.management.base import BaseCommand
from frontend.models import QuestionnaireResponse, SectionScore, QuestionnaireSection


class Command(BaseCommand):
    help = 'Check which section scores exist for responses'

    def handle(self, *args, **options):
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
        
        ml_section_names = set(ml_sections.values_list('name', flat=True))
        
        # Get all complete responses
        responses = QuestionnaireResponse.objects.filter(is_complete=True)
        
        # Check first 10 and last 10 responses (oldest and newest)
        sample_responses = list(responses[:10]) + list(responses.order_by('submitted_at')[:10])
        
        self.stdout.write(f'Checking first 10 responses out of {responses.count()} total...\n')
        
        for response in sample_responses:
            scores = response.section_scores.all()
            existing_sections = set(scores.values_list('section__name', flat=True))
            missing_sections = ml_section_names - existing_sections
            
            self.stdout.write(f'Response {response.id} (submitted: {response.submitted_at}):')
            self.stdout.write(f'  Has {scores.count()} section scores')
            self.stdout.write(f'  Sections: {sorted(existing_sections)}')
            if missing_sections:
                self.stdout.write(self.style.WARNING(f'  MISSING: {sorted(missing_sections)}'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ Has all ML-essential sections'))
            self.stdout.write('')

