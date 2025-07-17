"""Authentication module for admin routes"""
import os
import secrets
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials


security = HTTPBasic()


def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verify admin credentials using HTTP Basic Authentication.
    
    Credentials are read from environment variables:
    - ADMIN_USERNAME: The admin username
    - ADMIN_PASSWORD: The admin password
    
    If either environment variable is not set, access is denied.
    """
    # Read credentials from environment variables
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    # If credentials are not configured, deny access
    if not admin_username or not admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication not configured. Please set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Verify provided credentials
    is_correct_username = secrets.compare_digest(credentials.username, admin_username)
    is_correct_password = secrets.compare_digest(credentials.password, admin_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


def verify_admin_credentials_direct(username: str, password: str) -> bool:
    """
    Verify admin credentials directly with username/password strings.
    
    This version is for WebSocket authentication where we don't have HTTPBasicCredentials.
    
    Args:
        username: The username to verify
        password: The password to verify
        
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    # Read credentials from environment variables
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    # If credentials are not configured, deny access
    if not admin_username or not admin_password:
        return False
    
    # Verify provided credentials
    is_correct_username = secrets.compare_digest(username, admin_username)
    is_correct_password = secrets.compare_digest(password, admin_password)
    
    return is_correct_username and is_correct_password