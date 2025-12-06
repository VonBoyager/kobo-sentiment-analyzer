"""
Auto-load dataset management command.
Automatically loads the employee_feedback_dataset.csv on first run.
"""
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from ml_analysis.models import TrainingData


class Command(BaseCommand):
    help = 'Automatically load the employee feedback dataset if no data exists'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data exists',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        force = options.get('force', False)
        
        # Check if data already exists
        existing_count = TrainingData.objects.count()
        
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.SUCCESS(f'Dataset already loaded ({existing_count} records). Skipping auto-load.')
            )
            return
        
        # Find the dataset file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        dataset_path = os.path.join(base_dir, 'employee_feedback_dataset.csv')
        
        # Also check in the parent directory
        if not os.path.exists(dataset_path):
            parent_dir = os.path.dirname(base_dir)
            dataset_path = os.path.join(parent_dir, 'employee_feedback_dataset.csv')
        
        if not os.path.exists(dataset_path):
            self.stdout.write(
                self.style.WARNING(f'Dataset file not found. Checked paths:')
            )
            self.stdout.write(f'  - {os.path.join(base_dir, "employee_feedback_dataset.csv")}')
            self.stdout.write(f'  - {dataset_path}')
            return
        
        self.stdout.write(self.style.NOTICE(f'Found dataset at: {dataset_path}'))
        
        # Ensure admin user exists for the upload
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Creating admin user for dataset upload...')
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created.'))
        
        # Load the dataset
        self.stdout.write(self.style.NOTICE('Loading dataset...'))
        try:
            call_command('load_dataset', dataset_path, verbosity=1)
            
            # Verify the load
            new_count = TrainingData.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'Dataset loaded successfully! {new_count} records now in database.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading dataset: {str(e)}')
            )

