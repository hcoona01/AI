"""Pytest test harness configuration ensuring isolated local storage backend for fast testing."""

import os
import pytest

# Enforce local storage backend during automated pytest runs to ensure CPU & time budget
os.environ["STORE_BACKEND"] = "local"

