#
# Script to poll for CVE links, to make the actual link visible
# once they have showed up upstream.
#

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from pgweb.security.models import SecurityPatch
from pgweb.mailqueue.util import send_simple_mail

import requests


class Command(BaseCommand):
    help = 'Update CVE links'

    def handle(self, *args, **options):
        with transaction.atomic():
            newly_visible = []
            for s in SecurityPatch.objects.filter(cve_visible=False):
                r = requests.get(s.cvelink, timeout=10)
                if r.status_code == 200:
                    # RedHat have started requiring both a HTML page and a JSON api call to view
                    # CVEs. Dumb dumb dumb, but what can we do...
                    r = requests.get('https://access.redhat.com/api/redhat_node/CVE-{}.json'.format(s.cve))
                    if r.status_code == 200:
                        newly_visible.append(s.cve)
                        s.cve_visible = True
                        s.save()
            if newly_visible:
                send_simple_mail(settings.NOTIFICATION_FROM,
                                 settings.NOTIFICATION_EMAIL,
                                 "CVE entries made public",
                                 """The following CVE entries are now public upstream,
and have been made visible on the website.

{0}
""".format("\n".join(newly_visible)))
