"""
Subprocess execution utilities for the userspace component.

This module re-exports the run_cmd function from the vega_common library
to maintain backward compatibility while reducing code duplication.
"""
# Import the centralized function from the common library
# Complexity: O(1) for import
from vega_common.utils.sub_process import run_cmd

# The run_cmd function is now available for import from this module,
# preserving compatibility for modules that import from here.
# The original duplicated implementation has been removed.

# Note: The clean_output function was specific to the old implementation's
# Popen usage and is no longer needed as run_cmd handles output directly.
