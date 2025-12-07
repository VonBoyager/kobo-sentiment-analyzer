from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from frontend.models import (
    QuestionnaireResponse, QuestionResponse, SectionScore,
    SpecialQuestionnaire, SpecialQuestionnaireResponse,
    SpecialQuestionResponse, SpecialSectionScore
)
from ml_analysis.models import (
    SentimentAnalysis, TopicAnalysis, SectionTopicCorrelation,
    TrainingData, UserFeedback, MLModel
)


class Command(BaseCommand):
    help = 'Clear all user accounts and related data for a fresh start'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '⚠️  WARNING: This will delete ALL user accounts and ALL data!'
            ))
            self.stdout.write(self.style.WARNING(
                'This includes:'
            ))
            self.stdout.write('  - All user accounts')
            self.stdout.write('  - All questionnaire responses')
            self.stdout.write('  - All sentiment analyses')
            self.stdout.write('  - All topic analyses')
            self.stdout.write('  - All correlations')
            self.stdout.write('  - All training data')
            self.stdout.write('  - All ML models')
            self.stdout.write('  - All special questionnaires')
            
            confirm = input('\nType "YES" to confirm: ')
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Count before deletion
        user_count = User.objects.count()
        response_count = QuestionnaireResponse.objects.count()
        sentiment_count = SentimentAnalysis.objects.count()
        topic_count = TopicAnalysis.objects.count()
        correlation_count = SectionTopicCorrelation.objects.count()
        training_count = TrainingData.objects.count()
        model_count = MLModel.objects.count()
        special_q_count = SpecialQuestionnaire.objects.count()

        self.stdout.write(self.style.WARNING('Deleting all data...'))

        # Delete in order to respect foreign key constraints
        # Delete ML analysis data first
        SectionTopicCorrelation.objects.all().delete()
        TopicAnalysis.objects.all().delete()
        SentimentAnalysis.objects.all().delete()
        UserFeedback.objects.all().delete()
        TrainingData.objects.all().delete()
        MLModel.objects.all().delete()

        # Delete special questionnaire data
        SpecialQuestionResponse.objects.all().delete()
        SpecialSectionScore.objects.all().delete()
        SpecialQuestionnaireResponse.objects.all().delete()
        SpecialQuestionnaire.objects.all().delete()

        # Delete regular questionnaire data
        QuestionResponse.objects.all().delete()
        SectionScore.objects.all().delete()
        QuestionnaireResponse.objects.all().delete()

        # Delete all users (except superusers if you want to keep them)
        # Uncomment the next line if you want to keep superusers
        # User.objects.filter(is_superuser=False).delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Successfully cleared all data:'
        ))
        self.stdout.write(f'  - Deleted {user_count} user(s)')
        self.stdout.write(f'  - Deleted {response_count} questionnaire response(s)')
        self.stdout.write(f'  - Deleted {sentiment_count} sentiment analysis(es)')
        self.stdout.write(f'  - Deleted {topic_count} topic analysis(es)')
        self.stdout.write(f'  - Deleted {correlation_count} correlation(s)')
        self.stdout.write(f'  - Deleted {training_count} training data entry(ies)')
        self.stdout.write(f'  - Deleted {model_count} ML model(s)')
        self.stdout.write(f'  - Deleted {special_q_count} special questionnaire(s)')
        self.stdout.write(self.style.SUCCESS(
            '\n✨ Database is now clean and ready for a fresh start!'
        ))

