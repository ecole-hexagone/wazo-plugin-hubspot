# Copyright 2023 École Hexagone (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import xmlrpc.client as xmlrpclib
import logging

from wazo_dird import BaseSourcePlugin, make_result_class
from wazo_dird.helpers import BaseBackendView

from . import http

from itertools import chain

from hubspot import HubSpot
from hubspot.crm.contacts import PublicObjectSearchRequest, ApiException

import phonenumbers

logger = logging.getLogger(__name__)


class HubspotView(BaseBackendView):

    backend = 'hubspot'
    list_resource = http.HubspotList
    item_resource = http.HubspotItem


class HubspotBackend(BaseSourcePlugin):

    HUBSPOT_FIELD_ID = 'hs_object_id'
    HUBSPOT_FIELD_FIRSTNAME = 'firstname'
    HUBSPOT_FIELD_LASTNAME = 'lastname'
    HUBSPOT_FIELD_NAME = 'name'
    HUBSPOT_FIELD_PHONE = 'phone'
    HUBSPOT_FIELD_MOBILE = 'mobilephone'
    HUBSPOT_FIELD_EMAIL = 'email'
    HUBSPOT_FIELD_COUNTRY = 'country'

    HUBSPOT_CONTACT_FIELDS = [
        HUBSPOT_FIELD_ID,
        HUBSPOT_FIELD_FIRSTNAME,
        HUBSPOT_FIELD_LASTNAME,
        HUBSPOT_FIELD_PHONE,
        HUBSPOT_FIELD_MOBILE,
        HUBSPOT_FIELD_EMAIL,
        HUBSPOT_FIELD_COUNTRY,
    ]

    HUBSPOT_COMPANY_FIELDS = [
        HUBSPOT_FIELD_ID,
        HUBSPOT_FIELD_NAME,
        HUBSPOT_FIELD_PHONE,
        HUBSPOT_FIELD_COUNTRY,
    ]

    def load(self, dependencies):
        """
        The load function is responsible for setting up the source and acquiring
        any resources necessary.
        """
        config = dependencies['config']

        self.name = config['name']

        logger.info('Starting Hubspot client')
        self.api_client = HubSpot(access_token=config['access_token'])

        unique_column = self.HUBSPOT_FIELD_ID

        format_columns = dependencies['config'].get(self.FORMAT_COLUMNS, {})
        if 'reverse' not in format_columns:
            logger.info(
                'no "reverse" column has been configured on %s will use "firstname", "lastname" and "name"',
                self.name
            )
            format_columns['reverse'] = '{firstname} {lastname} {name}'

        self._first_matched_columns = config.get(self.FIRST_MATCHED_COLUMNS, [])
        if not self._first_matched_columns:
            logger.info(
                'no "first_matched_columns" configured on "%s" no results will be matched',
                self.name,
            )


        self._SourceResult = make_result_class(
            'hubspot',
            self.name,
            unique_column,
            format_columns,
        )

    def unload(self):
        """
        The unload method is used to release any resources that are under the
        responsibility of this instance.
        """

    def search(self, term, args=None):
        """
        The search method should return a list of dict containing the search
        results.
        The results should include the columns that are expected by the display.
        When columns from the source do not match the columns from the display,
        the `format_columns` dictionary can be used by the administrator
        to add or modify columns.
        If the backend has a `unique_column` configuration, a new column will be
        added with a `__unique_id` header containing the unique key.
        """
        logger.debug("search term=%s", term)

        contact_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_FIRSTNAME,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_LASTNAME,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_PHONE,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_MOBILE,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                # {
                #     "filters": [
                #         {
                #             "value": "*" + term + "*",
                #             "propertyName": "hs_searchable_calculated_phone_number",
                #             "operator": "CONTAINS_TOKEN"
                #         }
                #     ]
                # },
                # {
                #     "filters": [
                #         {
                #             "value": "*" + term + "*",
                #             "propertyName": "hs_searchable_calculated_mobile_number",
                #             "operator": "CONTAINS_TOKEN"
                #         }
                #     ]
                # },
            ],
            properties=self.HUBSPOT_CONTACT_FIELDS,
            limit=10
        )

        company_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_NAME,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "value": "*" + term + "*",
                            "propertyName": self.HUBSPOT_FIELD_PHONE,
                            "operator": "CONTAINS_TOKEN"
                        }
                    ]
                },
                # {
                #     "filters": [
                #         {
                #             "value": "*" + term + "*",
                #             "propertyName": "hs_searchable_calculated_phone_number",
                #             "operator": "CONTAINS_TOKEN"
                #         }
                #     ]
                # },
            ],
            properties=self.HUBSPOT_COMPANY_FIELDS,
            limit=10
        )

        try:
            contacts_res = self.api_client.crm.contacts.search_api.do_search(
                public_object_search_request=contact_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)

        try:
            companies_res = self.api_client.crm.companies.search_api.do_search(
                public_object_search_request=company_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)

        return chain(
            (self._source_result_from_content(contact) for contact in contacts_res.results),
            (self._source_result_from_content(company) for company in companies_res.results),
        )

    def first_match(self, term, args=None):
        """
        The first_match method should return a dict containing the first matched
        result.
        The results should include the columns that are expected by the display.
        When columns from the source do not match the columns from the display,
        the `format_columns` dictionary can be used by the administrator
        to add or modify columns.
        If the backend has a `unique_column` configuration, a new column will be
        added with a `__unique_id` header containing the unique key.
        """
        intnum = phonenumbers.parse(term, None)
        intnum = phonenumbers.format_number(intnum, phonenumbers.PhoneNumberFormat.E164)

        contact_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "value": intnum,
                            "propertyName": self.HUBSPOT_FIELD_PHONE,
                            "operator": "EQ"
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "value": intnum,
                            "propertyName": self.HUBSPOT_FIELD_MOBILE,
                            "operator": "EQ"
                        }
                    ]
                },
                # {
                #     "filters": [
                #         {
                #             "value": intnum,
                #             "propertyName": "hs_searchable_calculated_phone_number",
                #             "operator": "EQ"
                #         }
                #     ]
                # },
                # {
                #     "filters": [
                #         {
                #             "value": intnum,
                #             "propertyName": "hs_searchable_calculated_mobile_number",
                #             "operator": "EQ"
                #         },
                #     ]
                # },
            ],
            properties=self.HUBSPOT_CONTACT_FIELDS,
            limit=1
        )

        company_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "value": intnum,
                            "propertyName": self.HUBSPOT_FIELD_PHONE,
                            "operator": "EQ"
                        }
                    ]
                },
                # {
                #     "filters": [
                #         {
                #             "value": intnum,
                #             "propertyName": "hs_searchable_calculated_phone_number",
                #             "operator": "EQ"
                #         }
                #     ]
                # },
            ],
            properties=self.HUBSPOT_COMPANY_FIELDS,
            limit=1
        )

        try:
            contacts_res =  self.api_client.crm.contacts.search_api.do_search(
                public_object_search_request=contact_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)

        try:
            companies_res =  self.api_client.crm.companies.search_api.do_search(
                public_object_search_request=company_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)
        
        results = chain(
            (self._source_result_from_content(contact) for contact in contacts_res.results),
            (self._source_result_from_content(company) for company in companies_res.results),
        )

        return results[0] if 0 < len(results) else None

    def list(self, uids, args):
        """
        Returns a list of results based on the unique column for this backend.
        This function is not mandatory as some backends make it harder than
        others to query for specific ids. If a backend does not provide the list
        function, it will not be possible to set a favourite from this backend.
        Results returned from list should be formatted in the same way than
        results from search. Meaning that the `__unique_id` column should be
        added and display columns should be present.
        """
        
        contact_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "values": uids,
                            "propertyName": self.HUBSPOT_FIELD_ID,
                            "operator": "IN"
                        }
                    ]
                },
            ],
            properties=self.HUBSPOT_CONTACT_FIELDS,
        )

        company_public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {
                            "values": uids,
                            "propertyName": self.HUBSPOT_FIELD_ID,
                            "operator": "IN"
                        }
                    ]
                },
            ],
            properties=self.HUBSPOT_COMPANY_FIELDS,
        )

        try:
            contacts_res =  self.api_client.crm.contacts.search_api.do_search(
                public_object_search_request=contact_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)

        try:
            companies_res =  self.api_client.crm.companies.search_api.do_search(
                public_object_search_request=company_public_object_search_request
            )
        except ApiException as e:
            logger.error("Exception when calling search_api->do_search: %s\n" % e)
        
        return chain(
            (self._source_result_from_content(contact) for contact in contacts_res.results), 
            (self._source_result_from_content(company) for company in companies_res.results),
        )

    def _source_result_from_content(self, content):
        try:
            for phone_property in [self.HUBSPOT_FIELD_PHONE, self.HUBSPOT_FIELD_MOBILE]:
                if phone_property in content.properties and content.properties[phone_property]:
                    parsed_phone = phonenumbers.parse(content.properties[phone_property], None)
                    content.properties[phone_property] = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            
        except phonenumbers.NumberParseException as e:
            logger.warn("Exception when trying to parse phone number: %s\n" % e)

        return self._SourceResult(content.properties)
