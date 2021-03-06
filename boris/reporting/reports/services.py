# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import loader
from django.template.context import RequestContext

from boris.reporting.core import BaseReport
from boris.services.models import service_list, Encounter


class ServiceReport(BaseReport):
    title = u'Shrnutí výkonů'
    description = u'Statistiky jednotlivých výkonů splňujících zadaná kritéria.'
    contenttype_office = 'application/vnd.ms-word; charset=utf-8'

    def __init__(self, date_from=None, date_to=None, towns=None, person=None):
        enc_filtering = (
            ('performed_on__gte', date_from),
            ('performed_on__lte', date_to),
            ('where__in', towns),
            ('person', person),
        )
        enc_filtering = [(f[0], f[1]) for f in enc_filtering if f[1]]
        filtering = [('encounter__%s' % f[0], f[1]) for f in enc_filtering]

        self.enc_filtering = dict(enc_filtering)
        self.filtering = dict(filtering)
        self.date_from = date_from
        self.date_to = date_to
        self.towns = towns
        self.person = person

    def get_filename(self):
        return 'souhrn_vykonu.doc'

    def _get_service_stats(self):
        return [
            service.get_stats(self.filtering) for service in service_list(self.person, diseases_last=True)
            if service.service.include_in_reports
        ]

    def get_stats(self):
        encounters = Encounter.objects.filter(**self.enc_filtering)
        all_enc_count = encounters.count()
        direct_enc_count = encounters.filter(is_by_phone=False).count()
        encounter_stats = (u'Počet kontaktů (z toho přímých)', '%i (%i)' % (
            all_enc_count, direct_enc_count))
        return [(None, (encounter_stats,))] + self._get_service_stats()

    def render(self, request, display_type):
        return loader.render_to_string(
            self.get_template(display_type),
            {
                'stats': self.get_stats(),
                'person': self.person,
                'date_from': self.filtering.get('encounter__performed_on__gte'),
                'date_to': self.filtering.get('encounter__performed_on__lte'),
                'towns': self.towns,
            },
            context_instance=RequestContext(request)
        )
