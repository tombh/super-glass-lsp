from pathlib import Path
from single_source import get_version

# TODO: Doesn't actually work when published
__version__ = get_version(__name__, Path(__file__).parent.parent)
