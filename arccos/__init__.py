"""Arccos on-course data analysis layer.

Reads CSV artifacts produced by chrisdecali/golf-reports pull_arccos.py
(default location: ~/golf-data/) and exposes them as typed pandas
DataFrames ready for analysis.
"""
from arccos.loader import ArccosData, load_arccos

__all__ = ["ArccosData", "load_arccos"]
