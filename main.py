"""
Main application entry point for the Zolkin API.
"""
import os
import logging

import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from api import create_app



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Starting Zolkin API...")
load_dotenv()
app = create_app()


origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "https://zolkin.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "Zolkin API",
        "version": "1.0.0"
    }


if __name__ == "__main__": 
    port = int(os.getenv("PORT", "5002"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
