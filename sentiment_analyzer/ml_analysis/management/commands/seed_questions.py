from django.core.management.base import BaseCommand
from frontend.models import QuestionnaireSection, QuestionnaireQuestion, QuestionResponse

class Command(BaseCommand):
    help = 'Seeds the database with standard questionnaire questions based on CSV columns'

    def handle(self, *args, **options):
        self.stdout.write('Seeding questionnaire questions based on CSV columns...')

        # Structure matches Upload.tsx columns and load_dataset.py sections
        structure = {
            "Compensation & Benefits": [
                "I believe my salary is fair.",
                "Our compensation is competitive.",
                "Our benefits are adequate for my needs.",
                "We are fairly rewarded for our efforts."
            ],
            "Work-Life Balance": [
                "I have a manageable workload.",
                "I have flexibility in my schedule.",
                "Our leave policies are adequate."
            ],
            "Work Environment & Resources": [
                "My workplace is safe and comfortable.",
                "I have the tools and resources I need."
            ],
            "Culture & Values": [
                "The company's mission is meaningful to me.",
                "The company acts ethically.",
                "Innovation is encouraged."
            ],
            "Diversity & Inclusion": [
                "We have a positive and inclusive culture.",
                "I feel respected by my colleagues.",
                "My team collaborates effectively.",
                "Conflicts are managed constructively."
            ],
            "Career Development": [
                "There are opportunities for professional growth.",
                "The training I receive is valuable.",
                "There is a clear path for career advancement.",
                "My role aligns with my skills."
            ],
            "Management & Leadership": [
                "My manager communicates clearly.",
                "My manager supports me.",
                "I am comfortable raising concerns."
            ],
            "Job Security & Stability": [
                "I feel my job is secure.",
                "I believe the company is financially stable."
            ],
            "Role Clarity & Communication": [
                "My job responsibilities are clear.",
                "I have autonomy in my role.",
                "My contributions are acknowledged.",
                "Performance evaluations are fair.",
                "Changes are communicated openly."
            ]
        }

        section_order = 1
        for section_name, questions in structure.items():
            # Get or create section
            section, created = QuestionnaireSection.objects.get_or_create(
                name=section_name,
                defaults={'order': section_order, 'description': f'Questions related to {section_name}'}
            )
            
            # Ensure order is correct
            if section.order != section_order:
                section.order = section_order
                section.save()
            
            if created:
                self.stdout.write(f'Created section: {section_name}')
            else:
                self.stdout.write(f'Updated section: {section_name}')

            question_order = 1
            for q_text in questions:
                # Handle duplicates first
                existing_questions = QuestionnaireQuestion.objects.filter(section=section, text=q_text)
                if existing_questions.count() > 1:
                    self.stdout.write(f'Found {existing_questions.count()} duplicates for "{q_text}". Merging...')
                    primary = existing_questions.first()
                    for duplicate in existing_questions[1:]:
                        # Reassign any responses to the primary question
                        QuestionResponse.objects.filter(question=duplicate).update(question=primary)
                        duplicate.delete()
                    question = primary
                elif existing_questions.exists():
                    question = existing_questions.first()
                else:
                    # Check if question exists in another section (moved)
                    existing_q = QuestionnaireQuestion.objects.filter(text=q_text).first()
                    if existing_q and existing_q.section != section:
                        self.stdout.write(f'Moving question "{q_text}" from {existing_q.section.name} to {section_name}')
                        existing_q.section = section
                        existing_q.order = question_order
                        existing_q.save()
                        question = existing_q
                    else:
                        question = QuestionnaireQuestion.objects.create(
                            section=section,
                            text=q_text,
                            order=question_order
                        )
                
                # Ensure order is correct
                if question.order != question_order:
                    question.order = question_order
                    question.save()
                    
                question_order += 1
            
            section_order += 1
            
        # Clean up empty sections (e.g. if we emptied "Team & Collaboration")
        for section in QuestionnaireSection.objects.all():
            if section.questions.count() == 0:
                self.stdout.write(f'Deleting empty section: {section.name}')
                section.delete()

        self.stdout.write(self.style.SUCCESS('Successfully seeded questionnaire questions matching CSV structure'))