# Generated by Django 5.0.7 on 2024-07-18 02:14

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gmtisp_billing", "0002_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Payment",
        ),
    ]