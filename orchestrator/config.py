"""Run-level tunables for the orchestrator, on top of common/config.py's
env loading. Kept separate because these are pipeline-behavior knobs, not
credentials.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import get

MAX_DEMOS_PER_RUN = int(get("MAX_DEMOS_PER_RUN", "20"))
MAX_PITCHES_PER_RUN = int(get("MAX_PITCHES_PER_RUN", "20"))
MAX_REPLY_CHECKS_PER_RUN = int(get("MAX_REPLY_CHECKS_PER_RUN", "50"))
