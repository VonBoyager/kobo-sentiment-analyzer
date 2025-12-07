# Generated manually to fix missing updated_at column
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0005_questionnaireresponse_ip_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaireresponse',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Timestamp when record was last updated'),
        ),
    ]

