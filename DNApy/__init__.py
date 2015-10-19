# -*- coding: utf-8 -*-
from __future__ import absolute_import

__title__ = 'DNApy'
__version__ = '0.1'
__license__ = 'GPL3'

import logging
import os

from .base_class import DNApyBaseClass, DNApyBaseDrawingClass

DEFAULT_SETTINGS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "defaults")
SETTINGS_DIR = DEFAULT_SETTINGS_DIR

GUI_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "gui")
ICONS_DIR = os.path.join(GUI_DIR, "icon")

logging.getLogger(__name__).addHandler(logging.NullHandler())
