"""Dashboard routes for Project WARP — traffic monitoring and admin interface."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Configuration
ADMIN_USER = os.getenv("DASHBOARD_USER", "admin")
ADMIN_PASS = os.getenv("DASHBOARD_PASS", "changeme")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

# Templates
try:
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    logger.warning(f"Templates directory not found: {e}")
    templates = None


# ============================================================================
# Dependency Injection
# ============================================================================

def check_auth(request: Request) -> bool:
    """Verify user is authenticated via session."""
    return request.session.get("authenticated") == True


# ============================================================================
# Models
# ============================================================================

class TrafficPoint(BaseModel):
    """Single traffic data point."""
    timestamp: datetime
    requests_total: float
    requests_blocked: float
    blocked_rate: float
    latency_p95: float
    risk_score: float


class DashboardMetrics(BaseModel):
    """Current dashboard metrics."""
    total_requests: int
    total_blocked: int
    block_rate_percent: float
    avg_latency_ms: float
    active_ips: int
    high_risk_ips: int


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve login page."""
    if templates is None:
        return "<h1>Templates not configured</h1>"
    
    error = request.query_params.get("error")
    return templates.TemplateResponse("dashboard_login.html", {
        "request": request,
        "error": error
    })


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission."""
    logger.info(f"Login attempt for user: {username}")
    
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["authenticated"] = True
        request.session["user"] = username
        logger.info(f"Login successful for user: {username}")
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    
    logger.warning(f"Failed login attempt for user: {username}")
    return RedirectResponse(
        url="/dashboard/login?error=Invalid credentials",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    user = request.session.get("user", "unknown")
    request.session.clear()
    logger.info(f"Logout for user: {user}")
    return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_303_SEE_OTHER)


# ============================================================================
# Dashboard Pages
# ============================================================================

@router.get("", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    if not check_auth(request):
        return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_302_FOUND)
    
    if templates is None:
        return "<h1>Dashboard template not found</h1>"
    
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/traffic", response_class=HTMLResponse)
async def traffic_page(request: Request):
    """Traffic analysis page."""
    if not check_auth(request):
        return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_302_FOUND)
    
    if templates is None:
        return "<h1>Dashboard template not found</h1>"
    
    return templates.TemplateResponse("dashboard_traffic.html", {"request": request})


@router.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    """Security monitoring page."""
    if not check_auth(request):
        return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_302_FOUND)
    
    if templates is None:
        return "<h1>Dashboard template not found</h1>"
    
    return templates.TemplateResponse("dashboard_security.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    if not check_auth(request):
        return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_302_FOUND)
    
    if templates is None:
        return "<h1>Dashboard template not found</h1>"
    
    return templates.TemplateResponse("dashboard_settings.html", {"request": request})


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/api/metrics")
async def get_metrics(request: Request) -> DashboardMetrics:
    """Get current metrics snapshot."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # TEMPORARY: Return test data to verify endpoint is working
    return DashboardMetrics(
        total_requests=999,
        total_blocked=888,
        block_rate_percent=88.8,
        avg_latency_ms=45.5,
        active_ips=12,
        high_risk_ips=12
    )


@router.get("/api/traffic")
async def get_traffic(
    request: Request,
    range_minutes: Optional[int] = 60
) -> Dict[str, Any]:
    """Get traffic data from Prometheus."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        import requests
        
        # Query Prometheus for request rate
        query = f'rate(ddos_requests_total[5m])'
        params = {"query": query}
        
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("status") == "success":
            results = []
            for result in data.get("data", {}).get("result", []):
                if result.get("value"):
                    ts, val = result["value"]
                    results.append({
                        "timestamp": datetime.fromtimestamp(int(ts)).isoformat(),
                        "value": float(val)
                    })
            return {"status": "success", "data": results}
        
        return {"status": "error", "data": []}
        
    except Exception as e:
        logger.error(f"Error fetching traffic: {e}")
        return {"status": "error", "data": [], "error": str(e)}


@router.get("/api/blocked-ips")
async def get_blocked_ips(request: Request) -> Dict[str, Any]:
    """Get currently blocked IPs."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from app.services.mitigation import mitigation_controller
        
        blocked_ips = []
        if hasattr(mitigation_controller, 'blocked_ips'):
            for ip, block_info in mitigation_controller.blocked_ips.items():
                blocked_ips.append({
                    "ip": ip,
                    "reason": block_info.get("reason", "unknown"),
                    "blocked_at": block_info.get("timestamp", ""),
                    "duration_minutes": block_info.get("duration", 30)
                })
        
        return {
            "status": "success",
            "total_blocked": len(blocked_ips),
            "ips": blocked_ips[:50]  # Return top 50
        }
    except Exception as e:
        logger.error(f"Error fetching blocked IPs: {e}")
        return {"status": "error", "total_blocked": 0, "ips": []}


@router.get("/api/detection-events")
async def get_detection_events(
    request: Request,
    limit: int = 20
) -> Dict[str, Any]:
    """Get recent detection events."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from app.services.detector import detection_engine
        
        events = []
        if hasattr(detection_engine, 'recent_events'):
            for event in detection_engine.recent_events[-limit:]:
                events.append({
                    "timestamp": event.get("timestamp", ""),
                    "ip": event.get("ip", ""),
                    "risk_score": event.get("risk_score", 0),
                    "detection_type": event.get("detection_type", "unknown"),
                    "action": event.get("action", "none")
                })
        
        return {
            "status": "success",
            "total_events": len(events),
            "events": list(reversed(events))
        }
    except Exception as e:
        logger.error(f"Error fetching detection events: {e}")
        return {"status": "error", "total_events": 0, "events": []}


@router.get("/api/stats")
async def get_stats(request: Request) -> Dict[str, Any]:
    """Get comprehensive statistics."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        metrics = await get_metrics(request)
        blocked_ips = await get_blocked_ips(request)
        events = await get_detection_events(request, limit=100)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics.dict(),
            "blocked_ips": blocked_ips,
            "recent_events": events,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.post("/api/settings")
async def update_settings(
    request: Request
) -> Dict[str, Any]:
    """Update dashboard settings."""
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        # Store settings in session
        request.session["settings"] = data
        logger.info(f"Settings updated by user: {request.session.get('user')}")
        return {"status": "success", "message": "Settings updated"}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def dashboard_health() -> Dict[str, str]:
    """Dashboard health check (no auth required)."""
    return {"status": "ok", "component": "dashboard"}
