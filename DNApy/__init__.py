# -*- coding: utf-8 -*-
__title__ = 'DNApy'
__version__ = '0.1'
__license__ = 'GPL3'

from __future__ import absolute_import
import logging

from .base_class import DNApyBaseClass, DNApyBaseDrawingClass

DEFAULT_SETTINGS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "defaults")
SETTINGS_DIR = DEFAULT_SETTINGS_DIR

logging.getLogger(__name__).addHandler(logging.NullHandler())
