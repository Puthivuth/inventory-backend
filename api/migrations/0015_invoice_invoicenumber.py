# Generated migration for adding invoiceNumber field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_productassociation'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='invoiceNumber',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
