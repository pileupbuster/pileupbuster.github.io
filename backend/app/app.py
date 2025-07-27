from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import uvicorn
import logging
from datetime import datetime


def generate_status_html_optimized(frontend_url: str, timestamp: str, system_status: dict, frequency_data: dict = None, split_data: dict = None) -> str:
    """
    Generate ultra-clean HTML status page without screenshots
    
    Args:
        frontend_url: URL to link back to frontend
        timestamp: Timestamp of page generation
        system_status: System status information from database
        frequency_data: Current frequency information (optional)
        split_data: Current split information (optional)
        
    Returns:
        HTML content as string
    """
    is_active = system_status.get('active', False)
    status_class = 'active' if is_active else 'inactive'
    status_text = 'ACTIVE' if is_active else 'INACTIVE'
    status_color = '#28a745' if is_active else '#dc3545'
    
    # Build frequency and split information for status banner (only when system is active)
    frequency_info = ""
    if is_active and frequency_data and frequency_data.get('frequency'):
        frequency_info = f"<br><small>Frequency: {frequency_data['frequency']}</small>"
    
    split_info = ""
    if is_active and split_data and split_data.get('split'):
        split_info = f"<br><small>Split: {split_data['split']}</small>"

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Status</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background-color: #ffffff;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #e2e8f0;
        }}
        .header-logo {{
            max-height: 80px;
            max-width: 300px;
            height: auto;
            width: auto;
        }}
        .status-banner {{
            background-color: {status_color};
            color: white;
            padding: 30px 20px;
            text-align: center;
            font-size: 1.8rem;
            font-weight: bold;
            margin: 0;
        }}
        .content {{
            padding: 40px 30px;
            text-align: center;
        }}
        .description-section {{
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: 1px solid #cbd5e0;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .description-section h2 {{
            margin: 0 0 15px 0;
            color: #2d3748;
            font-size: 1.4rem;
            font-weight: 600;
        }}
        .description-section p {{
            margin: 0 0 20px 0;
            color: #4a5568;
            font-size: 1rem;
            line-height: 1.6;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }}
        .features {{
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .feature {{
            background-color: #ffffff;
            color: #4a5568;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .link-container {{
            margin: 0;
        }}
        .frontend-link {{
            display: inline-block;
            background: linear-gradient(135deg, {status_color} 0%, {status_color}dd 100%);
            color: white;
            text-decoration: none;
            padding: 20px 40px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1.3rem;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        }}
        .frontend-link:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        }}
        .timestamp {{
            margin-top: 20px;
            text-align: center;
            font-size: 0.85rem;
            color: #718096;
            opacity: 0.8;
        }}
        @media (max-width: 768px) {{
            .container {{
                margin: 10px;
                border-radius: 8px;
            }}
            .header {{
                padding: 20px;
            }}
            .header-logo {{
                max-height: 60px;
                max-width: 250px;
            }}
            .status-banner {{
                padding: 25px 15px;
                font-size: 1.5rem;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .description-section {{
                padding: 25px 20px;
                margin-bottom: 25px;
            }}
            .description-section h2 {{
                font-size: 1.2rem;
            }}
            .description-section p {{
                font-size: 0.95rem;
            }}
            .features {{
                gap: 10px;
            }}
            .feature {{
                font-size: 0.85rem;
                padding: 6px 12px;
            }}
            .frontend-link {{
                padding: 18px 30px;
                font-size: 1.1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="/static/logo.png" alt="Pileup Buster Logo" class="header-logo" onerror="this.style.display='none';">
        </div>
        
        <div class="status-banner {status_class}">
            System Status: {status_text}{frequency_info}{split_info}
        </div>
        
        <div class="content">
            <div class="description-section">
                <h2>🚀 What is Pileup Buster?</h2>
                <p>Pileup Buster is a modern web application by EI6LF/EI6JGB to help people bust the pileup when we are on air. It's simple to use, and requires no registration. In fact, the only thing you need to enter, is your callsign!</p>
                <div class="features">
                    <span class="feature">📻 Real-time Queue</span>
                    <span class="feature">🌍 Works on any device</span>
                    <span class="feature">⚡ View the current queue live</span>
                </div>
            </div>
            <div class="link-container">
                <a href="{frontend_url}" class="frontend-link" target="_blank">
                    🚀 Visit Pileup Buster ({status_text})
                </a>
            </div>
            <div class="timestamp">Last updated: {timestamp}</div>
        </div>
    </div>
</body>
</html>
"""
    return html_template


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
    
    # Mount static files (logo, etc.)
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Add the status endpoint at root level
    @app.get('/status', response_class=HTMLResponse)
    async def get_status_page():
        """Get static HTML status page with current system status"""
        from app.database import queue_db
        
        try:
            # Get frontend URL from environment variable
            frontend_url = os.getenv('FRONTEND_URL', 'https://pileupbuster.com')
            
            # Get system status from database
            system_status = queue_db.get_system_status()
            
            # Get frequency information
            frequency_data = None
            try:
                frequency_data = queue_db.get_frequency()
            except Exception:
                pass  # No frequency is fine
            
            # Get split information
            split_data = None
            try:
                split_data = queue_db.get_split()
            except Exception:
                pass  # No split is fine
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # Generate HTML page with system status
            html_content = generate_status_html_optimized(frontend_url, timestamp, system_status, frequency_data, split_data)
            
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
    from app.routes.events import events_router
    from app.routes.websocket import websocket_router
    
    app.include_router(queue_router, prefix="/api/queue", tags=["queue"])
    app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
    app.include_router(public_router, prefix="/api/public", tags=["public"])
    app.include_router(events_router, prefix="/api/events", tags=["events"])
    app.include_router(websocket_router, prefix="/api", tags=["websocket"])
    
    # Initialize logger integration service based on database settings
    from app.services.logger_integration import logger_service
    from app.database import queue_db
    
    try:
        logger_settings = queue_db.get_logger_integration()
        if logger_settings.get('enabled', False):
            logger_service.enable()
            logging.info("Logger integration initialized and enabled")
        else:
            logging.info("Logger integration initialized but disabled")
    except Exception as e:
        logging.warning(f"Failed to initialize logger integration: {e}")
    
    return app

app = create_app()

def main():
    """Entry point for the application script"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()