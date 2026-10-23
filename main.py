import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUBPROJECT = os.path.join(ROOT, "quantum-flight-optimizer")

if SUBPROJECT not in sys.path:
    sys.path.insert(0, SUBPROJECT)

from main import run_benchmark  # noqa: E402


if __name__ == "__main__":
    run_benchmark()
