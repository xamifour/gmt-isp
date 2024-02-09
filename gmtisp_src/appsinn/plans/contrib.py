import logging

from django.apps import apps
from django.conf import settings
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.utils import translation

from plans.signals import user_language

email_logger = logging.getLogger("emails")


def send_template_email(recipients, title_template, body_template, context, language):
    """Sends e-mail using templating system"""

    send_emails = getattr(settings, "SEND_PLANS_EMAILS", True)
    if not send_emails:
        return

    site_name = getattr(settings, "SITE_NAME", "Please define settings.SITE_NAME")
    domain = getattr(settings, "SITE_URL", None)

    if domain is None:
        try:
            Site = apps.get_model("sites", "Site")
            current_site = Site.objects.get_current()
            site_name = current_site.name
            domain = current_site.domain
        except LookupError:
            pass

    context.update(
        {"site_name": site_name, "site_domain": domain, "site": current_site}
    )

    if language is not None:
        translation.activate(language)

    mail_title_template = loader.get_template(title_template)
    mail_body_template = loader.get_template(body_template)
    title = mail_title_template.render(context).strip()
    body = mail_body_template.render(context)
    try:
        mail_body_template_html = loader.get_template(
            body_template.replace(".txt", ".html")
        )
        html_body = mail_body_template_html.render(context)
    except TemplateDoesNotExist:
        html_body = None

    try:
        email_from = getattr(settings, "DEFAULT_FROM_EMAIL")
    except AttributeError:
        raise ImproperlyConfigured(
            "DEFAULT_FROM_EMAIL setting needed for sending e-mails"
        )

    mail.send_mail(title, body, email_from, recipients, html_message=html_body)

    if language is not None:
        translation.deactivate()

    email_logger.info(
        "Email (%s) sent to %s\nTitle: %s\n%s\n\n" % (language, recipients, title, body)
    )


def get_user_language(user):
    """Simple helper that will fire django signal in order
    to get User language possibly given by other part of application.
    :param user:
    :return: string or None
    """
    return_value = {}
    user_language.send(sender=user, user=user, return_value=return_value)
    return return_value.get("language")
