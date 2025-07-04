#!/usr/bin/env python3
"""
Stage 8: Dashboard Backend
Main FastAPI application for the betting dashboard
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from stage8_backend import Stage8Backend, main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
