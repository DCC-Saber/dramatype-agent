"""Shared test configuration.

Set DRAMATYPE_AGENT_MODE=rule_based BEFORE any app modules are imported,
so the Settings singleton is created in rule_based mode for all tests.
"""

import os
os.environ["DRAMATYPE_AGENT_MODE"] = "rule_based"
