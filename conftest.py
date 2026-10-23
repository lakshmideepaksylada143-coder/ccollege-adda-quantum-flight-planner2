import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUBPROJECT = os.path.join(ROOT, "quantum-flight-optimizer")

if SUBPROJECT not in sys.path:
    sys.path.insert(0, SUBPROJECT)
