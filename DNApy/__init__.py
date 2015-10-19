# -*- coding: utf-8 -*-
__title__ = 'DNApy'
__version__ = '0.1'
__license__ = 'GPL3'

from __future__ import absolute_import
import logging

from .base_class import DNApyBaseClass, DNApyBaseDrawingClass

logging.getLogger(__name__).addHandler(logging.NullHandler())
