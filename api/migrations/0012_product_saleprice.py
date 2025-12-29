# Generated migration for adding salePrice field to Product model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_invoice_khqrcodestring_invoice_khqrdeeplink_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='salePrice',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
