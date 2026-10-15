#!/usr/bin/env python3
"""Fuzentrix builders. Run: python fz.py --help"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))
sys.path.insert(0, HERE)

from fz.cli import main  # noqa: E402

sys.exit(main())
