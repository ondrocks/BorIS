'''
Created on 2.10.2011

@author: xaralis
'''
import anyjson

from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template.context import RequestContext
from django.template.loader import render_to_string

from boris.services.models.core import get_model_for_class_name, Service, \
    Encounter


class HandleForm(object):
    def get_context(self, request, encounter_id, service_cls, object_id):
        try:
            cls = get_model_for_class_name(service_cls)
        except ValueError:
            raise Http404

        encounter = get_object_or_404(Encounter, pk=encounter_id)
        ctx = {
            'encounter': encounter,
            'cls': service_cls,
            'service': cls,
            'is_edit': object_id is not None
        }
        kwargs = {}

        if ctx['is_edit']:
            obj = get_object_or_404(cls, pk=object_id)
            ctx.update({
                'obj': obj,
                'action_link': reverse('services_handle_form_change', kwargs={
                    'encounter_id': encounter_id, 'service_cls': service_cls, 'object_id': object_id
                })
            })
            kwargs['instance'] = obj
        else:
            ctx.update({
                'action_link': reverse('services_handle_form_add', kwargs={
                    'encounter_id': encounter_id, 'service_cls': service_cls
                })
            })

        if request.method == 'POST':
            form = cls.form()(encounter, request.POST, **kwargs)
        else:
            form = cls.form()(encounter, **kwargs)
        ctx.update({'form': form})
        return ctx

    def __call__(self, request, encounter_id, service_cls, object_id=None):
        ctx = self.get_context(request, encounter_id, service_cls, object_id)

        if request.method == 'POST':
            form = ctx['form']
            if form.is_valid():
                form.save()
                resp = {'ok': True}
            else:
                resp = {
                    'ok': False,
                    'content': render_to_string(form.template_list, ctx,
                        context_instance=RequestContext(request))
                }
            return HttpResponse(anyjson.dumps(resp), content_type='application/json')
        else:
            return render(request, ctx['form'].template_list, ctx)

handle_form = HandleForm()


def services_list(request, encounter_id):
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    services_done = Service.objects.filter(encounter=encounter_id)
    return render(request, 'services/list.html', {'encounter': encounter,
        'services_done': services_done})


def drop_service(request, service_id):
    try:
        service = Service.objects.select_subclasses().filter(pk=service_id)[0]
        service.delete()
        return HttpResponse('OK')
    except IndexError:
        raise Http404

