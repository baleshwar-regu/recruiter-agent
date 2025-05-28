import sys
import os
import logging

if os.getenv("RENDER", "false").lower() != "true":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# 1. Configure the root logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# 2. Silence noisy httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)

import uvicorn

from config import APPLICATION_PORT

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=APPLICATION_PORT,
        reload=True,
        reload_excludes=[".venv/*", "__pycache__/*", ".mypy_cache/*"],
    )
