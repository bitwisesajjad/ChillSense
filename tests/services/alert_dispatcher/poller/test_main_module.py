"""Tests for poller package module entrypoint."""

import runpy
from unittest.mock import patch


def test_poller_module_entrypoint_calls_runtime_main():
    """Running poller.__main__ should call runtime.main exactly once."""
    with patch("services.alert_dispatcher.poller.runtime.main") as mock_main:
        runpy.run_module("services.alert_dispatcher.poller.__main__", run_name="__main__")

    mock_main.assert_called_once_with()
