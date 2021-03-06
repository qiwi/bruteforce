# Generated by Django 3.0.8 on 2020-07-08 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_auto_20200706_1519"),
    ]

    operations = [
        migrations.AddField(
            model_name="hash",
            name="ip",
            field=models.GenericIPAddressField(default="0.0.0.0"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="bruteconfig",
            name="max_length",
            field=models.PositiveSmallIntegerField(verbose_name="Максимальная длина"),
        ),
        migrations.AlterField(
            model_name="bruteconfig",
            name="min_length",
            field=models.PositiveSmallIntegerField(verbose_name="Минимальная длина"),
        ),
    ]
