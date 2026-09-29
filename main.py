"""Convenience entry point for the Panchayat Agromet API."""

from agromet.main import app


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
