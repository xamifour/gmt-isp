# Generated by Django 4.2 on 2024-02-15 05:02

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import openwisp_utils.base
import openwisp_utils.fields
import openwisp_utils.utils
import re
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=64, null=True)),
                (
                    "key",
                    openwisp_utils.fields.KeyField(
                        db_index=True,
                        default=openwisp_utils.utils.get_random_key,
                        help_text="unique project key",
                        max_length=64,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^[^\\s/\\.]+$"),
                                code="invalid",
                                message="This value must not contain spaces, dots or slashes.",
                            )
                        ],
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Shelf",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "books_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("HORROR", "HORROR"),
                            ("FANTASY", "FANTASY"),
                            ("FACTUAL", "FACTUAL"),
                            ("Mystery", "Mystery"),
                            ("Historical Fiction", "Historical Fiction"),
                            ("Literary Fiction", "Literary Fiction"),
                            ("Romance", "Romance"),
                            ("Science Fiction", "Science Fiction"),
                            ("Short Stories", "Short Stories"),
                            ("Thrillers", "Thrillers"),
                            ("Biographies", "Biographies"),
                        ],
                        max_length=50,
                        null=True,
                        verbose_name="Type of book",
                    ),
                ),
                (
                    "books_count",
                    openwisp_utils.fields.FallbackPositiveIntegerField(
                        blank=True,
                        fallback=21,
                        null=True,
                        verbose_name="Number of books",
                    ),
                ),
                ("locked", models.BooleanField(default=True, verbose_name="Is locked")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, null=True, verbose_name="Create at"
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Owner of shelf",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(openwisp_utils.base.FallbackModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="Operator",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_name", models.CharField(default="test", max_length=30)),
                ("last_name", models.CharField(default="test", max_length=30)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="testing_app.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="name")),
                ("author", models.CharField(max_length=64, verbose_name="author")),
                (
                    "shelf",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="testing_app.shelf",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]