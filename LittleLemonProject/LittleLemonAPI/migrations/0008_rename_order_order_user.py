# Generated by Django 4.0 on 2023-04-30 09:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0007_alter_order_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='order',
            new_name='user',
        ),
    ]
