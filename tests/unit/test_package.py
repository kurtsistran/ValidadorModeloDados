"""Smoke test for the initial package layout."""

import data_model_auditor


def test_package_imports() -> None:
    """The distribution package exposes its version."""
    assert data_model_auditor.__version__ == "0.1.0"
