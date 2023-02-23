# Copyright 2023 École Hexagone (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_dird_client.commands.helpers.base_source_command import SourceCommand


class HubspotCommand(SourceCommand):

    resource = 'backends/hubspot/sources'
