"""
Process listing utilities for the rootspace component.

This module re-exports process listing functions from the vega_common library
to maintain backward compatibility while reducing code duplication.
"""

# Import functions from the new common location
from vega_common.utils.process_utils import get_process_list, similar_string_list

# Re-export for backward compatibility if needed, or remove this file
# if all consumers can be updated directly.

# The original content is removed as the functions are now in vega_common.
# If strict backward compatibility is needed, keep the re-exports:
# __all__ = ['get_process_list', 'similar_string_list']
