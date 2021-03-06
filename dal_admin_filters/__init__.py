# -*- encoding: utf-8 -*-
from dal import autocomplete
from django import forms
from django.contrib.admin.filters import SimpleListFilter
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Media, MEDIA_TYPES
from django.apps import apps
from dal import autocomplete


class AutocompleteFilter(SimpleListFilter):
    template = "dal_admin_filters/autocomplete-filter.html"
    title = ''
    field_name = ''
    autocomplete_url = ''
    autocomplete_model = ''
    query_attr_name = ''
    is_placeholder_title = False
    widget_attrs = {}

    class Media:
        css = {
            'all': (
                'autocomplete_light/vendor/select2/dist/css/select2.css',
                'autocomplete_light/select2.css',
                'dal_admin_filters/css/autocomplete-fix.css'
            )
        }
        js = (
            'autocomplete_light/jquery.init.js',
            'autocomplete_light/autocomplete.init.js',
            'autocomplete_light/vendor/select2/dist/js/select2.full.js',
            'autocomplete_light/select2.js',
            'dal_admin_filters/js/querystring.js',
        )

    def __init__(self, request, params, model, model_admin):
        if self.parameter_name:
            raise AttributeError(
                'Rename attribute `parameter_name` to '
                '`field_name` for {}'.format(self.__class__)
            )
        self.parameter_name = self.query_attr_name or '{}__id__exact'.format(self.field_name)
        super(AutocompleteFilter, self).__init__(request, params, model, model_admin)

        self._add_media(model_admin)

        if self.autocomplete_model:
            queryset = apps.get_model(*self.autocomplete_model.split('.', 1))._meta.default_manager.all()
        else:
            queryset = getattr(model, self.field_name).get_queryset()
        field = forms.ModelChoiceField(
            queryset=queryset,
            widget=autocomplete.ModelSelect2(
                url=self.autocomplete_url,
            )
        )

        attrs = self.widget_attrs.copy()
        attrs['id'] = 'id-%s-dal-filter' % self.field_name
        if self.is_placeholder_title:
            attrs['data-placeholder'] = self.title
        self.rendered_widget = field.widget.render(
            name=self.parameter_name,
            value=self.used_parameters.get(self.parameter_name, ''),
            attrs=attrs
        )

    def _add_media(self, model_admin):

        if not hasattr(model_admin, 'Media'):
            raise ImproperlyConfigured('Add empty Media class to %s. Sorry about this bug.' % model_admin)

        def _get_media(obj):
            return Media(media=getattr(obj, 'Media', None))

        media = _get_media(model_admin) + _get_media(AutocompleteFilter) + _get_media(self)

        for name in MEDIA_TYPES:
            setattr(model_admin.Media, name, getattr(media, "_" + name))

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})
        else:
            return queryset
