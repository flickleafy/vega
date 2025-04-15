"""
List processing utilities for the rootspace component.

This module re-exports list processing functions from the vega_common library
to maintain backward compatibility while reducing code duplication.
"""
from vega_common.utils.list_process import list_average, remove_first_add_last, safe_get, create_sliding_window

# These functions are now imported directly from vega_common.utils.list_process
# Keeping this file for backward compatibility
