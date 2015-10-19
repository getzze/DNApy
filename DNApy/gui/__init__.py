# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from . import plasmid_GUI, mixed_base_codons_GUI, genbank_GUI, featurelist_GUI, featureedit_GUI, enzyme_GUI, dnaeditor_GUI, dnaEditorCairo_GUI

from .. import SETTINGS_DIR
GUI_DIR = os.path.dirname(os.path.realpath(__file__))
ICONS_DIR = os.path.join(GUI_DIR, "icon")

logging.getLogger(__name__)
