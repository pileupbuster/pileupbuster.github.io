import uvicorn
from app import create_app

app = create_app()

def main():
    """Main entry point for production server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()