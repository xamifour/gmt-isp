# Generated by Django 4.2 on 2024-02-15 04:35

from django.db import migrations
import openwisp_radius.base.models
import private_storage.fields
import private_storage.storage.files


class Migration(migrations.Migration):
    dependencies = [
        ("openwisp_radius", "0004_alter_radiusbatch_csvfile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="radiusbatch",
            name="csvfile",
            field=private_storage.fields.PrivateFileField(
                blank=True,
                help_text="The csv file containing the user details to be uploaded",
                null=True,
                storage=private_storage.storage.files.PrivateFileSystemStorage(
                    base_url="/api/v1/radius/organization/",
                    location="/Users/ka/Desktop/dev/pystuff/django/v0/gmt_isp/gmtisp_src/gmtisp/media/private",
                ),
                upload_to=openwisp_radius.base.models._get_csv_file_location,
                verbose_name="CSV",
            ),
        ),
    ]