from django.core.management.base import BaseCommand
from frontend.models import QuestionnaireSection, QuestionnaireQuestion

class Command(BaseCommand):
    help = 'Populate the questionnaire with sections and questions'

    def handle(self, *args, **options):
        # Clear existing data
        QuestionnaireQuestion.objects.all().delete()
        QuestionnaireSection.objects.all().delete()
        
        # Define sections and questions
        # These sections match exactly what the ML model expects (see ml_analysis/services.py)
        sections_data = [
            {
                'name': 'Compensation & Benefits',
                'description': 'Questions about salary, compensation, and benefits',
                'questions': [
                    'Salaries are fair compared to the work required.',
                    'Compensation is competitive with similar jobs in the industry.',
                    'Benefits (health, insurance, retirement, etc.) meet employee needs.'
                ]
            },
            {
                'name': 'Work-Life Balance',
                'description': 'Questions about work-life balance and flexibility',
                'questions': [
                    'Workload allows employees to maintain a healthy work-life balance.',
                    'Work schedules are flexible when needed.',
                    'Leave policies (vacation, sick, parental, etc.) are adequate.'
                ]
            },
            {
                'name': 'Culture & Values',
                'description': 'Questions about company culture and values',
                'questions': [
                    'The company\'s mission and values are meaningful and well-communicated.',
                    'The organization promotes a positive and inclusive culture.',
                    'Company values align with employee values and expectations.'
                ]
            },
            {
                'name': 'Diversity & Inclusion',
                'description': 'Questions about diversity and inclusion in the workplace',
                'questions': [
                    'The company promotes diversity in hiring and promotion.',
                    'All employees feel included and valued regardless of background.',
                    'The workplace environment is respectful and welcoming to all.'
                ]
            },
            {
                'name': 'Career Development',
                'description': 'Questions about professional growth and development',
                'questions': [
                    'Opportunities for professional growth are available.',
                    'Training and skill development are supported by the company.',
                    'Career progression paths are clear.'
                ]
            },
            {
                'name': 'Management & Leadership',
                'description': 'Questions about management and leadership quality',
                'questions': [
                    'Managers communicate clearly and effectively.',
                    'Managers provide sufficient support for employees to succeed.',
                    'Employees feel comfortable raising concerns to management.'
                ]
            }
        ]
        
        # Create sections and questions
        for section_data in sections_data:
            section = QuestionnaireSection.objects.create(
                name=section_data['name'],
                description=section_data['description'],
                order=len(QuestionnaireSection.objects.all()) + 1
            )
            
            for i, question_text in enumerate(section_data['questions'], 1):
                QuestionnaireQuestion.objects.create(
                    section=section,
                    text=question_text,
                    order=i
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(sections_data)} sections with questions')
        )
