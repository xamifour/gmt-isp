from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from openwisp_utils.base import (
    FallbackModelMixin,
    KeyField,
    TimeStampedEditableModel,
    UUIDModel,
)
from openwisp_utils.fields import FallbackPositiveIntegerField


class Shelf(FallbackModelMixin, TimeStampedEditableModel):
    TYPES = (
        ('HORROR', 'HORROR'),
        ('FANTASY', 'FANTASY'),
        ('FACTUAL', 'FACTUAL'),
        ('Mystery', 'Mystery'),
        ('Historical Fiction', 'Historical Fiction'),
        ('Literary Fiction', 'Literary Fiction'),
        ('Romance', 'Romance'),
        ('Science Fiction', 'Science Fiction'),
        ('Short Stories', 'Short Stories'),
        ('Thrillers', 'Thrillers'),
        ('Biographies', 'Biographies'),
    )
    name = models.CharField(_('name'), max_length=64)
    books_type = models.CharField(
        _("Type of book"), choices=TYPES, null=True, blank=True, max_length=50
    )
    books_count = FallbackPositiveIntegerField(
        blank=True,
        null=True,
        fallback=21,
        verbose_name=_("Number of books"),
    )
    locked = models.BooleanField(_("Is locked"), default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        verbose_name=_("Owner of shelf"),
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        _("Create at"), null=True, blank=True, auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

    def clean(self):
        if self.name == "Intentional_Test_Fail":
            raise ValidationError('Intentional_Test_Fail')
        return self


class Book(TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)
    author = models.CharField(_('author'), max_length=64)
    shelf = models.ForeignKey('testing_app.Shelf', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False


class Project(UUIDModel):
    name = models.CharField(max_length=64, null=True, blank=True)
    key = KeyField(unique=True, db_index=True, help_text=_('unique project key'))

    def __str__(self):
        return self.name


class Operator(models.Model):
    first_name = models.CharField(max_length=30, default='test')
    last_name = models.CharField(max_length=30, default='test')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.first_name