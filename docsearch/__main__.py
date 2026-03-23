"""Allow running docsearch as a module: python -m docsearch"""
import sys
from docsearch.cli import main

sys.exit(main())
