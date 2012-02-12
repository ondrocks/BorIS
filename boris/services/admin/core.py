# -*- coding: utf-8 -*-
'''
Created on 27.10.2011

@author: xaralis
'''
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django import forms

from boris.services.models.core import Encounter
from boris.clients.forms import ReadOnlyWidget
from boris.utils.admin import BorisBaseAdmin

def service_list(self, obj):
    return u'<br />'.join([u'<small>%s</small>' % unicode(s) for s in obj.services.all()])
service_list.short_description = _(u'Provedené výkony')
service_list.allow_tags = True

class EncounterInline(admin.TabularInline):
    model = Encounter
    classes = ('collapse closed',)
    fieldsets = (
        (None, {
            'fields': ('performed_on', 'where', 'performed_by_verbose',
                'service_count', 'service_list', 'goto_link'),
        }),
    )
    readonly_fields = ('performed_by_verbose', 'service_count', 'service_list',
        'goto_link')
    extra = 0
    template = 'admin/services/encounter/encounter_inline.html'

    def has_add_permission(self, request, *args, **kwargs):
        return False

    def performed_by_verbose(self, obj):
        return u', '.join([unicode(u) for u in obj.performed_by.all()])
    performed_by_verbose.short_description = _(u'Provedli')

    def goto_link(self, obj):
        if obj.pk:
            return u'<a href="%s"><strong>%s &raquo;</strong></a>' % (obj.get_admin_url(), _(u'Přejít'))
        else:
            return _(u'Detaily kontaktu je možné editovat až po uložení.')
    goto_link.short_description = _(u'Přejít')
    goto_link.allow_tags = True

EncounterInline.service_list = service_list


class EncounterAdmin(BorisBaseAdmin):
    list_display = ('person', 'performed_on', 'where', 'service_list')
    list_filter = ('performed_on', 'where')
    search_fields = ('person__title', 'where__title',
        'performed_by__username', 'performed_by__first_name',
        'performed_by__last_name')
    fieldsets = (
        (None, {'fields': (('person', 'performed_on', 'where'), 'performed_by')}),
    )
    raw_id_fields = ('where', 'person')
    date_hierarchy = 'performed_on'
    autocomplete_lookup_fields = {
        'fk': ['where', 'person']
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        When popup and person_id in GET, use special widget that doesn't need
        to be filled up.
        """
        from boris.clients.models import Person

        request = kwargs.get('request', None)
        if request is not None and request.GET.get('person_id') and db_field.name == 'person':
            pid = request.GET.get('person_id')
            person = Person.objects.get(pk=pid).cast()
            kwargs.pop('request')
            kwargs['widget'] = ReadOnlyWidget(pid,
                '%s %s' % (unicode(person._meta.verbose_name).lower(), person))
            kwargs['initial'] = pid
            return db_field.formfield(**kwargs)
        elif db_field.name == 'performed_by':
            kwargs.pop('request')
            kwargs['widget'] = forms.SelectMultiple(attrs={'style': 'height: 70px;'})
            kwargs['initial'] = (request.user,)
            return db_field.formfield(**kwargs)
        else:
            return super(EncounterAdmin, self).formfield_for_dbfield(db_field, **kwargs)

EncounterAdmin.service_list = service_list

admin.site.register(Encounter, EncounterAdmin)

