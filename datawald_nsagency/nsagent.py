#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from .nsagency import NSAgency


class NSAgent(NSAgency):
    def __init__(self, logger, **setting):
        NSAgency.__init__(self, logger, **setting)
