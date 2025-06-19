"""Tests for fabric_run_pattern tool implementation.

This module tests the complete fabric_run_pattern tool functionality,
including error handling, SSE response parsing, and API integration.

The tests have been split across multiple files:
- test_fabric_run_pattern_basic.py - Basic execution tests
- test_fabric_run_pattern_error_handling.py - Error handling tests
- test_fabric_run_pattern_streaming.py - Streaming functionality tests
- test_fabric_run_pattern_validation.py - Input and parameter validation tests
- test_fabric_run_pattern_advanced.py - Advanced features

This file imports all the test classes to maintain backward compatibility.
"""

# Import all test classes to maintain backward compatibility
from tests.unit.test_fabric_run_pattern_advanced import (
    TestFabricRunPatternCoverageTargets,
    TestFabricRunPatternModelInference,
    TestFabricRunPatternRequestConstruction,
    TestFabricRunPatternUnexpectedSSETypes,
    TestFabricRunPatternVariablesAndAttachments,
)
from tests.unit.test_fabric_run_pattern_base import TestFabricRunPatternFixtureBase
from tests.unit.test_fabric_run_pattern_basic import TestFabricRunPatternBasicExecution
from tests.unit.test_fabric_run_pattern_error_handling import (
    TestFabricRunPatternErrorHandling,
)
from tests.unit.test_fabric_run_pattern_streaming import TestFabricRunPatternStreaming
from tests.unit.test_fabric_run_pattern_validation import (
    TestFabricRunPatternInputValidation,
    TestFabricRunPatternParameterValidation,
)

# Ensure all test classes are available for pytest discovery
__all__ = [
    "TestFabricRunPatternFixtureBase",
    "TestFabricRunPatternBasicExecution",
    "TestFabricRunPatternErrorHandling",
    "TestFabricRunPatternStreaming",
    "TestFabricRunPatternInputValidation",
    "TestFabricRunPatternParameterValidation",
    "TestFabricRunPatternRequestConstruction",
    "TestFabricRunPatternModelInference",
    "TestFabricRunPatternVariablesAndAttachments",
    "TestFabricRunPatternUnexpectedSSETypes",
    "TestFabricRunPatternCoverageTargets",
]
