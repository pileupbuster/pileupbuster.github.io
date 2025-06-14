from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import os
import uvicorn
import logging
from datetime import datetime

def create_app():
    # Load environment variables
    load_dotenv()
    
    # Create FastAPI app
    app = FastAPI(
        title="Pileup Buster API",
        description="Ham radio callsign queue management system",
        version="1.0.0",
        swagger_ui_parameters={
            "tryItOutEnabled": True,
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "filter": True
        }
    )
    
    # Enable CORS for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configuration (stored as app state)
    app.state.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.state.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pileup_buster')
    
    # Add the status endpoint at root level
    @app.get('/status', response_class=HTMLResponse)
    async def get_status_page():
        """Get static HTML status page with screenshot of frontend"""
        from app.services.screenshot import capture_screenshot, generate_status_html
        
        try:
            # Get frontend URL from environment variable
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            
            # Capture screenshot
            screenshot_b64 = capture_screenshot(frontend_url)
            
            if not screenshot_b64:
                raise HTTPException(
                    status_code=500, 
                    detail='Failed to capture screenshot'
                )
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Generate HTML page
            html_content = generate_status_html(screenshot_b64, frontend_url, timestamp)
            
            return HTMLResponse(content=html_content, status_code=200)
            
        except Exception as e:
            logging.error(f"Failed to generate status page: {e}")
            # Return a simple error page
            error_html = f"""
            <!DOCTYPE html>
            <html><head><title>Status Page Error</title></head>
            <body><h1>Status Page Unavailable</h1>
            <p>Unable to generate status page: {str(e)}</p>
            </body></html>
            """
            return HTMLResponse(content=error_html, status_code=500)
    
    # Include routers
    from app.routes.queue import queue_router
    from app.routes.admin import admin_router
    from app.routes.public import public_router
    
    app.include_router(queue_router, prefix="/api/queue", tags=["queue"])
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
    app.include_router(public_router, prefix="/api/public", tags=["public"])
    
    return app

app = create_app()

def main():
    """Entry point for the application script"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()