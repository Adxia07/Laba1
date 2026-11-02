from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

U_LIMIT = 1.0

@dataclass(frozen=True)
class Task:
    name: str
    hardness: str
    C: float
    D: float
    T: float