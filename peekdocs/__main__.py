"""Allow running peekdocs as a module: python -m peekdocs"""
import sys
from peekdocs.cli import main

sys.exit(main())
