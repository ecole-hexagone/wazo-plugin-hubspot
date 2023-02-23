#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 École Hexagone (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import setup
from setuptools import find_packages

setup(
    name='wazo_plugin_hubspot',
    version='0.0.1a0',
    description='Wazo plugin to bring closer Hubspot and Wazo',
    author='École Hexagone',
    author_email='is.hq@ecole-hexagone.com',
    url='https://github.com/ecole-hexagone/wazo-plugin-hubspot',
    
    install_requires=[
        'hubspot-api-client==7.4.0',
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'wazo_plugin_hubspot': ['dird/api.yml', 'ui/templates/*/*/*/*.html'],
    },

    entry_points={
        'wazo_dird.backends': [
            'hubspot = wazo_plugin_hubspot.dird.plugin:HubspotBackend',
        ],
        'wazo_dird.views': [
            'hubspot_backend = wazo_plugin_hubspot.dird.plugin:HubspotView',
        ],
        'wazo_dird_client.commands': [
            'hubspot = wazo_plugin_hubspot.client.plugin:HubspotCommand'
        ],
        'wazo_ui.plugins': [
            'hubspot = wazo_plugin_hubspot.ui.plugin:HubspotUI'
        ],

    }
)
