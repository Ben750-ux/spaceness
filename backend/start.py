"""Point d'entrée avec meilleure gestion d'erreurs pour Render"""
import os
import sys
import uvicorn
from config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    except Exception as e:
        print(f"FATAL: {e}", flush=True)
        sys.exit(1)
