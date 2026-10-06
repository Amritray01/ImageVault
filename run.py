import uvicorn
import os

if __name__ == "__main__":
    from app.config import settings
    host = os.getenv("HOST", settings.HOST)
    port = int(os.getenv("PORT", settings.PORT))
    print("==================================================")
    print("   ImageVault — Storage & Compression Service     ")
    print("==================================================")
    print(f"Starting FastAPI server on {host}:{port}...")
    print(f"Web Interface : http://localhost:{port}")
    print(f"API Swagger   : http://localhost:{port}/docs")
    print("==================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
