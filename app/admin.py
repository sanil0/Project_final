from fastapi import Depends
from .dependencies import get_admin_api_key

def require_admin(api_key: str = Depends(get_admin_api_key)) -> None:
    """Dependency to require admin access.
    
    Args:
        api_key: API key from get_admin_api_key dependency
        
    Returns:
        None if access is granted
    """
    return None