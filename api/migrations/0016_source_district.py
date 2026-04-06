# Generated migration for adding district field to Source model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_invoice_invoicenumber'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='district',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
