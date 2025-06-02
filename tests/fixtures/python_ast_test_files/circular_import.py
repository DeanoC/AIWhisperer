# File with circular import scenario
import sys
if 'module_a' not in sys.modules:
    import module_a