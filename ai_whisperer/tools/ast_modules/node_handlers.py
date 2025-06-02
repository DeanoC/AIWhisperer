"""
AST node type specific handlers
"""

import ast
from typing import Dict, Any, Optional


    def _handle_graceful_degradation(self, feature_name: str, error: Exception) -> None:
        """Enable graceful degradation by disabling failed feature."""
        self._degraded_mode = True
        self._disabled_features.add(feature_name)
        self._warnings.append(f"{feature_name}_failed")
        
        # Add fallback information
        if 'graceful_degradation' not in self._fallback_info:
            self._fallback_info['graceful_degradation'] = True
        
        # Feature-specific fallback setup
        if feature_name == 'metadata':
            self._fallback_info['metadata_extraction_failed'] = True
        elif feature_name == 'comments':
            self._fallback_info['comment_processing_failed'] = True
        elif feature_name == 'optimization':
            self._fallback_info['optimization_failed'] = True
    

