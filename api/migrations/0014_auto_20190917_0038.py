# Generated by Django 2.1.5 on 2019-09-17 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_pedcountreading_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedcountreading',
            name='value',
            field=models.IntegerField(),
        ),
    ]