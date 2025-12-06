# Automatic Dataset Loading

This document explains the automatic dataset loading feature for the Kobo Sentiment Analyzer.

## Overview

The application automatically loads the `employee_feedback_dataset.csv` file when the Django server starts, if no data exists in the database.

## How It Works

1. **On Server Startup**: The `ml_analysis` app's `AppConfig.ready()` method checks if data needs to be loaded.

2. **Auto-Load Command**: The `auto_load_dataset` management command:
   - Checks if `TrainingData` records already exist
   - If no data exists, finds and loads `employee_feedback_dataset.csv`
   - Creates an admin user if one doesn't exist (for the upload process)

3. **Dataset Location**: The command looks for the CSV file in:
   - `sentiment_analyzer/employee_feedback_dataset.csv`
   - `employee_feedback_dataset.csv` (project root)

## Manual Commands

### Auto-Load Dataset
```bash
python manage.py auto_load_dataset
```

### Force Reload (even if data exists)
```bash
python manage.py auto_load_dataset --force
```

### Load Specific File
```bash
python manage.py load_dataset path/to/your/file.csv
```

## CSV Format Requirements

The CSV file must contain these columns:

| Column | Description |
|--------|-------------|
| uid | Unique identifier |
| review_date | Date of the review |
| free_text_box | Free-text feedback |
| salary_fairness | Score (1-5) |
| compensation_competitiveness | Score (1-5) |
| benefits_adequacy | Score (1-5) |
| workload_balance | Score (1-5) |
| schedule_flexibility | Score (1-5) |
| leave_policies_adequacy | Score (1-5) |
| mission_values_meaningful | Score (1-5) |
| positive_inclusive_culture | Score (1-5) |
| company_values_alignment | Score (1-5) |
| professional_growth_opportunities | Score (1-5) |
| training_skill_development | Score (1-5) |
| clear_career_paths | Score (1-5) |
| manager_communication_clarity | Score (1-5) |
| raising_concerns_comfortability | Score (1-5) |
| manager_support_for_employees | Score (1-5) |

## Sections Mapping

The 18 score columns map to 5 sections:

1. **Compensation & Benefits**: salary_fairness, compensation_competitiveness, benefits_adequacy
2. **Work-Life Balance**: workload_balance, schedule_flexibility, leave_policies_adequacy
3. **Culture & Values**: mission_values_meaningful, positive_inclusive_culture, company_values_alignment
4. **Career Development**: professional_growth_opportunities, training_skill_development, clear_career_paths
5. **Management & Leadership**: manager_communication_clarity, raising_concerns_comfortability, manager_support_for_employees

## Troubleshooting

### Data Not Loading
- Ensure the CSV file is in the correct location
- Check that the CSV has the required columns
- Run with `--force` flag to reload

### Permission Errors
- Ensure the admin user has been created
- Check database permissions

