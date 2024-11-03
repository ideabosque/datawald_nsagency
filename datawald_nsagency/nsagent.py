#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from .nsagency import NSAgency


def deploy() -> list:
    return [
        {
            "service": "DataWald",
            "class": "NSAgent",
            "functions": {
                "retrieve_entities_from_source": {
                    "is_static": False,
                    "label": "nsagency",
                    "mutation": [],
                    "query": [],
                    "type": "Event",
                    "support_methods": [],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "datawald_agency",
                    "disabled_in_resources": True,  # Ignore adding to resource list.
                },
                "insert_update_entities_to_target": {
                    "is_static": False,
                    "label": "nsagency",
                    "mutation": [],
                    "query": [],
                    "type": "Event",
                    "support_methods": [],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "datawald_agency",
                    "disabled_in_resources": True,  # Ignore adding to resource list.
                },
                "update_sync_task": {
                    "is_static": False,
                    "label": "nsagency",
                    "mutation": [],
                    "query": [],
                    "type": "Event",
                    "support_methods": [],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "datawald_agency",
                    "disabled_in_resources": True,  # Ignore adding to resource list.
                },
            },
        }
    ]


class NSAgent(NSAgency):
    def __init__(self, logger, **setting):
        NSAgency.__init__(self, logger, **setting)
