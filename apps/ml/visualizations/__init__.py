"""
Visualization utilities for data analysis and exploratory workflows.

This module provides reusable plotting functions that are safe to use
in both interactive and headless (CI/server) environments. Select a
non-interactive Matplotlib backend such as ``Agg`` before importing
pyplot when no display is available, and call plot helpers with
``show=False``.
"""

from .data_distribution import plot_numeric_distributions

__all__ = ["plot_numeric_distributions"]
