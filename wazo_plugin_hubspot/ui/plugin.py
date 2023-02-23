# Copyright 2023 École Hexagone (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from flask import render_template, redirect, request, url_for, flash
from flask_classful import route

from requests.exceptions import HTTPError


from wazo_ui.helpers.plugin import create_blueprint
from wazo_ui.helpers.form import BaseForm
from wazo_ui.helpers.view import BaseIPBXHelperView
from flask_menu.classy import register_flaskview

from wazo_ui.plugins.dird_source.plugin import dird_source as bp
from flask_babel import lazy_gettext as l_
from wtforms.fields import (
    FormField,
    FieldList,
    StringField,
    HiddenField,
    SubmitField
)
from wtforms.validators import InputRequired


hubspot = create_blueprint('hubspot', __name__)


class HubspotUI(object):

    def load(self, dependencies):
        core = dependencies['flask']
        clients = dependencies['clients']

        HubspotConfigurationView.service = HubspotService(clients['wazo_dird'])
        HubspotConfigurationView.register(hubspot, route_base='/hubspot_configuration')
        register_flaskview(hubspot, HubspotConfigurationView)

        core.register_blueprint(hubspot)

        @bp.route('dird_sources/get/hubspot/<id>', methods=['GET'])
        def hubspot_get(id):
            return redirect("/engine/hubspot_configuration/get/hubspot/{}".format(id))

        @bp.route('dird_sources/new/hubspot', methods=['GET'])
        def hubspot_create():
            return redirect("/engine/hubspot_configuration/new/hubspot")


class ValueColumnsForm(BaseForm):
    key = StringField(validators=[InputRequired()])
    value = StringField(validators=[InputRequired()])


class ColumnsForm(BaseForm):
    value = StringField(validators=[InputRequired()])


class HubspotForm(BaseForm):
    first_matched_columns = FieldList(FormField(ColumnsForm))
    format_columns = FieldList(FormField(ValueColumnsForm))
    searched_columns = FieldList(FormField(ColumnsForm))
    access_token = StringField(l_('Access Token'))


class HubspotSourceForm(BaseForm):
    tenant_uuid = HiddenField()
    backend = HiddenField()
    name = StringField(l_('Name'), validators=[InputRequired()])
    hubspot_config = FormField(HubspotForm)
    submit = SubmitField()


class HubspotConfigurationView(BaseIPBXHelperView):
    form = HubspotSourceForm
    resource = 'hubspot'

    def index(self):
        return redirect(url_for('wazo_engine.dird_source.DirdSourceView:index'))

    @route('/get/<backend>/<id>', methods=['GET'])
    def get(self, backend, id, form=None):
        try:
            resource = self.service.get(backend, id)
        except HTTPError as error:
            self._flash_http_error(error)
            return self._redirect_for('index')

        form = form or self._map_resources_to_form(resource)
        form = self._populate_form(form)

        return render_template(self._get_template(backend=backend),
                               form=form,
                               resource=resource,
                               current_breadcrumbs=self._get_current_breadcrumbs(),
                               listing_urls=self.listing_urls)

    @route('/new/<backend>', methods=['GET'])
    def new(self, backend):
        default = {
            'hubspot_config': {}
        }
        form = self.form(backend=backend, data=default)

        return render_template(self._get_template(backend=backend),
                               form_mode='add',
                               current_breadcrumbs=self._get_current_breadcrumbs(),
                               form=form)

    def post(self):
        form = self.form()
        resources = self._map_form_to_resources_post(form)

        if not form.csrf_token.validate(form):
            self._flash_basic_form_errors(form)
            return self._new(form)

        try:
            self.service.create(resources)
        except HTTPError as error:
            form = self._fill_form_error(form, error)
            self._flash_http_error(error)
            return self._new(form)

        flash('Resource has been created', 'success')
        return self._redirect_for('index')

    def _map_form_to_resources(self, form, form_id=None):
        resource = super()._map_form_to_resources(form, form_id)
        config_name = 'hubspot_config'

        if 'format_columns' in resource[config_name]:
            resource[config_name]['format_columns'] = {option['key']: option['value'] for option in
                                                       resource[config_name]['format_columns']}

        if 'searched_columns' in resource[config_name]:
            resource[config_name]['searched_columns'] = [option['value'] for option in
                                                         resource[config_name]['searched_columns']]

        if 'first_matched_columns' in resource[config_name]:
            resource[config_name]['first_matched_columns'] = [option['value'] for option in
                                                              resource[config_name]['first_matched_columns']]

        return resource

    def _map_resources_to_form(self, resource):
        config_name = 'hubspot_config'

        resource[config_name] = resource

        if 'format_columns' in resource[config_name]:
            resource[config_name]['format_columns'] = [{'key': key, 'value': val} for (key, val) in
                                                       resource[config_name]['format_columns'].items()]

        if 'searched_columns' in resource[config_name]:
            resource[config_name]['searched_columns'] = [{'value': option} for option in
                                                         resource[config_name]['searched_columns']]

        if 'first_matched_columns' in resource[config_name]:
            resource[config_name]['first_matched_columns'] = [{'value': option} for option in
                                                              resource[config_name]['first_matched_columns']]

        form = self.form(data=resource)
        return form

    def _get_template(self, type_=None, backend=None):
        blueprint = request.blueprint.replace('.', '/')

        if not type_:
            return '{blueprint}/form/form_{backend}.html'.format(
                blueprint=blueprint,
                backend=backend
            )
        else:
            return '{blueprint}/{type_}.html'.format(
                blueprint=blueprint,
                type_=type_
            )


class HubspotService:

    def __init__(self, dird_client):
        self._dird = dird_client

    def get(self, backend, source_uuid):
        result = self._dird.backends.get_source(backend, source_uuid)
        result['backend'] = backend
        return result

    def create(self, source_data):
        backend = source_data['backend']
        source_data['hubspot_config']['name'] = source_data['name']

        return self._dird.backends.create_source(backend, source_data['hubspot_config'])

    def update(self, source_data):
        backend = source_data['backend']
        source_data[backend + '_config']['name'] = source_data['name']

        return self._dird.backends.edit_source(backend, source_data['uuid'], source_data['hubspot_config'])

