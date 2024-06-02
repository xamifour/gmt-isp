from django.core.management import BaseCommand

from . import tasks


class Command(BaseCommand):
    help = "Expire accounts and send messages"

    def handle(self, *args, **options):  # pragma: no cover
        tasks.expire_account()
        self.stdout.write("accounts was expired")
