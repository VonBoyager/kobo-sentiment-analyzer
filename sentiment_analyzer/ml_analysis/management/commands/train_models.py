from django.core.management.base import BaseCommand
from ml_analysis.services import MLPipeline
from ml_analysis.models import MLModel

class Command(BaseCommand):
    help = 'Train and save all ML models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-retrain',
            action='store_true',
            help='Force retraining even if models exist'
        )
        parser.add_argument(
            '--save-models',
            action='store_true',
            help='Save models to database after training'
        )

    def handle(self, *args, **options):
        force_retrain = options['force_retrain']
        save_models = options['save_models']
        
        # Check if models already exist
        existing_models = MLModel.objects.filter(is_active=True)
        if existing_models.exists() and not force_retrain:
            self.stdout.write(
                self.style.WARNING(
                    f'Found {existing_models.count()} active models. Use --force-retrain to retrain.'
                )
            )
            return
        
        # Initialize pipeline
        pipeline = MLPipeline()
        
        self.stdout.write('Training ML models...')
        
        # Train all models
        results = pipeline.train_all_models()
        
        # Display results
        self.stdout.write('\nTraining Results:')
        for model_type, result in results.items():
            if isinstance(result, dict):
                if 'error' in result:
                    self.stdout.write(
                        self.style.ERROR(f'{model_type}: {result["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'{model_type}: {result}')
                    )
            else:
                self.stdout.write(f'{model_type}: {result}')
        
        # Save models if requested
        if save_models:
            self.stdout.write('\nSaving models to database...')
            save_results = pipeline.save_all_models()
            
            for model_type, result in save_results.items():
                if 'Error' in result:
                    self.stdout.write(
                        self.style.ERROR(f'{model_type}: {result}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'{model_type}: {result}')
                    )
        
        # Show model summary
        active_models = MLModel.objects.filter(is_active=True)
        self.stdout.write(f'\nActive models in database: {active_models.count()}')
        
        for model in active_models:
            self.stdout.write(
                f'  - {model.name} ({model.model_type}) - Accuracy: {model.accuracy or "N/A"}'
            )
        
        self.stdout.write(
            self.style.SUCCESS('\nModel training completed!')
        )
