from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from frontend.models import QuestionnaireSection, QuestionnaireQuestion, SpecialQuestionnaire
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Populate the database with the special employee satisfaction questionnaire'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expires-days',
            type=int,
            default=30,
            help='Number of days until the questionnaire expires (default: 30)'
        )
        parser.add_argument(
            '--max-responses',
            type=int,
            default=1,
            help='Maximum number of responses allowed (default: 1)'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username of the admin creating the questionnaire (default: admin)'
        )

    def handle(self, *args, **options):
        expires_days = options['expires_days']
        max_responses = options['max_responses']
        admin_username = options['admin_username']
        
        # Get or create admin user
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Admin user "{admin_username}" not found. Please create it first.')
            )
            return
        
        # Clear existing questionnaire data
        self.stdout.write('Clearing existing questionnaire data...')
        QuestionnaireQuestion.objects.all().delete()
        QuestionnaireSection.objects.all().delete()
        
        # Define the questionnaire sections and questions
        # These sections match exactly what the ML model expects (see ml_analysis/services.py)
        questionnaire_data = [
            {
                'section': 'Compensation & Benefits',
                'description': 'Questions about salary, compensation, and employee benefits',
                'questions': [
                    'Salaries are fair compared to the work required.',
                    'Compensation is competitive with similar jobs in the industry.',
                    'Benefits (health, insurance, retirement, etc.) meet employee needs.'
                ]
            },
            {
                'section': 'Work-Life Balance',
                'description': 'Questions about work-life balance and flexibility',
                'questions': [
                    'Workload allows employees to maintain a healthy work-life balance.',
                    'Work schedules are flexible when needed.',
                    'Leave policies (vacation, sick, parental, etc.) are adequate.'
                ]
            },
            {
                'section': 'Culture & Values',
                'description': 'Questions about company culture and values',
                'questions': [
                    'The company\'s mission and values are meaningful and well-communicated.',
                    'The organization promotes a positive and inclusive culture.',
                    'Company values align with employee values and expectations.'
                ]
            },
            {
                'section': 'Diversity & Inclusion',
                'description': 'Questions about diversity and inclusion in the workplace',
                'questions': [
                    'The company promotes diversity in hiring and promotion.',
                    'All employees feel included and valued regardless of background.',
                    'The workplace environment is respectful and welcoming to all.'
                ]
            },
            {
                'section': 'Career Development',
                'description': 'Questions about professional growth and development',
                'questions': [
                    'Opportunities for professional growth are available.',
                    'Training and skill development are supported by the company.',
                    'Career progression paths are clear.'
                ]
            },
            {
                'section': 'Management & Leadership',
                'description': 'Questions about management and leadership effectiveness',
                'questions': [
                    'Managers communicate clearly and effectively.',
                    'Managers provide sufficient support for employees to succeed.',
                    'Employees feel comfortable raising concerns to management.'
                ]
            }
        ]
        
        # Create sections and questions
        self.stdout.write('Creating questionnaire sections and questions...')
        for order, section_data in enumerate(questionnaire_data, 1):
            section = QuestionnaireSection.objects.create(
                name=section_data['section'],
                description=section_data['description'],
                order=order
            )
            
            for question_order, question_text in enumerate(section_data['questions'], 1):
                QuestionnaireQuestion.objects.create(
                    section=section,
                    text=question_text,
                    order=question_order
                )
            
            self.stdout.write(f'  Created section: {section.name} with {len(section_data["questions"])} questions')
        
        # Create special questionnaire
        expires_at = timezone.now() + timedelta(days=expires_days)
        special_questionnaire = SpecialQuestionnaire.objects.create(
            title="Employee Satisfaction Survey",
            description="""Instructions
Please rate each statement based on your level of agreement using the scale below:
1 – Strongly Disagree
2 – Disagree
3 – Neutral
4 – Agree
5 – Strongly Agree

This questionnaire covers 10 key areas of employee satisfaction and will help us understand your experience at our organization.""",
            expires_at=expires_at,
            max_responses=max_responses,
            created_by=admin_user
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created special questionnaire:\n'
                f'  Title: {special_questionnaire.title}\n'
                f'  Unique URL: {special_questionnaire.unique_url}\n'
                f'  Expires: {special_questionnaire.expires_at}\n'
                f'  Max Responses: {special_questionnaire.max_responses}\n'
                f'  Total Sections: {QuestionnaireSection.objects.count()}\n'
                f'  Total Questions: {QuestionnaireQuestion.objects.count()}'
            )
        )
        
        self.stdout.write(
            self.style.WARNING(
                f'IMPORTANT: Share this URL with your employees: '
                f'http://localhost:8000{special_questionnaire.unique_url}'
            )
        )



