from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import Settings, get_settings
from .dependencies import (
    get_detection_engine,
    get_feature_extractor,
    get_http_client,
    get_mitigation_controller,
    get_settings_dep,
    get_sliding_window_store,
    get_telemetry_client,
)
from .admin import require_admin
from .schemas import (
    BlocklistRequest,
    DetectionVerdict,
    MitigationAction,
    MitigationResult,
    TrafficSample,
)
from .services import (
    DetectionEngine,
    FeatureExtractor,
    MitigationController,
    SlidingWindowStore,
    TelemetryClient,
)
from .services.http_client import UpstreamHTTPClient, create_http_client
from .services.proxy import DDoSProtectionProxy
from .utils.ip import normalize_ip, extract_client_ip
from .dashboard.routes import router as dashboard_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent DDoS Detection & Mitigation")

# Add DDoS protection middleware with ML-based detection (MUST BE FIRST)
from .middleware.ddos_protection import DDoSProtectionMiddleware

app.add_middleware(
    DDoSProtectionMiddleware,
    model_path="models",
    sensitivity_level="medium",
    window_size=60,  # 60 seconds window
    cleanup_interval=300  # Clean old data every 5 minutes
)

# Add SessionMiddleware for dashboard authentication
# Note: In production, use a secure secret key from environment
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-in-production",
    https_only=False,  # Set to True in production
    same_site="lax"
)

# Mount static files for dashboard
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include dashboard router
app.include_router(dashboard_router)


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize app on startup."""
    logger.info("Application startup event")
    
    try:
        logger.info("🔧 Initializing DDoS Protection System...")
        
        from .config import get_settings
        from .services.http_client import UpstreamHTTPClient
        from .services.storage import SlidingWindowStore
        from .services.feature_extractor import FeatureExtractor
        from .services.detector import DetectionEngine
        from .services.mitigation import MitigationController
        from .services.telemetry import TelemetryClient
        
        settings = get_settings()
        
        # Initialize sliding window store first (needed by feature extractor)
        logger.info("  📊 Creating sliding window store...")
        app.state.sliding_window_store = SlidingWindowStore(window_seconds=60)
        
        # Initialize feature extractor with the store
        logger.info("  🔍 Creating feature extractor...")
        app.state.feature_extractor = FeatureExtractor(store=app.state.sliding_window_store)
        
        # Initialize detection engine
        logger.info("  🤖 Creating detection engine...")
        app.state.detection_engine = DetectionEngine()
        
        # Initialize mitigation controller
        logger.info("  🛡️  Creating mitigation controller...")
        app.state.mitigation_controller = MitigationController(
            request_rate_limit=100,  # Allow 100 requests per sliding window
            sliding_window_seconds=60  # Per 60-second window
        )
        
        # Initialize HTTP client
        logger.info("  🌐 Creating HTTP client...")
        app.state.http_client = UpstreamHTTPClient(
            base_url=str(settings.upstream_base_url or "http://httpbin.org")
        )
        
        # Initialize telemetry
        logger.info("  📈 Creating telemetry client...")
        app.state.telemetry_client = TelemetryClient()
        
        logger.info("✅ All DDoS protection services initialized successfully!")
        logger.info("🛡️  FULL DDoS DETECTION ENABLED")
        
    except Exception as e:
        logger.warning(f"⚠️  Full initialization failed: {e}, falling back to demo mode...")
        
        # Fallback: minimal services
        try:
            from .services.http_client import UpstreamHTTPClient
            app.state.http_client = UpstreamHTTPClient(base_url="http://httpbin.org")
            logger.info("✅ Fallback HTTP client created - Dashboard will work")
        except:
            logger.error("❌ Failed to create even minimal services")
            
        app.state.sliding_window_store = None
        app.state.feature_extractor = None
        app.state.detection_engine = None
        app.state.mitigation_controller = None
        app.state.telemetry_client = None


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Application shutdown event")


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/admin/state")
async def admin_state(
    store: SlidingWindowStore = Depends(get_sliding_window_store),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    settings: Settings = Depends(get_settings_dep),
    _admin: None = Depends(require_admin),
) -> Dict[str, object]:
    snapshot = await store.snapshot()
    return {
        "window_seconds": settings.sliding_window_seconds,
        "request_rate_limit": settings.request_rate_limit,
        "unique_ip_count": snapshot.unique_ip_count,
        "global_request_rate": snapshot.global_request_rate,
        "global_event_count": snapshot.global_event_count,
        "blocklist_ips": list(sorted(detection_engine.blocklist_ips)),
    }


@app.post("/admin/blocklist", status_code=201)
async def add_blocklist(
    request_body: BlocklistRequest,
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    _admin: None = Depends(require_admin),
) -> Dict[str, object]:
    normalized = normalize_ip(request_body.ip)
    if normalized is None:
        raise HTTPException(status_code=400, detail="Invalid IP address")
    detection_engine.add_to_blocklist(normalized)
    return {"ip": normalized, "message": request_body.reason or "added"}


@app.delete("/admin/blocklist/{ip}")
async def remove_blocklist(
    ip: str,
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    _admin: None = Depends(require_admin),
) -> Dict[str, object]:
    normalized = normalize_ip(ip)
    if normalized is None:
        raise HTTPException(status_code=400, detail="Invalid IP address")
    detection_engine.remove_from_blocklist(normalized)
    return {"ip": normalized, "removed": True}


@app.get("/telemetry/events")
async def telemetry_events(
    telemetry_client: TelemetryClient = Depends(get_telemetry_client),
    _admin: None = Depends(require_admin),
) -> Dict[str, object]:
    events = await telemetry_client.recent_events()
    return {"events": events}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_request(
    full_path: str,
    request: Request,
    feature_extractor: FeatureExtractor = Depends(get_feature_extractor),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    mitigation_controller: MitigationController = Depends(get_mitigation_controller),
    telemetry_client: TelemetryClient = Depends(get_telemetry_client),
    http_client: UpstreamHTTPClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings_dep),
) -> Response:
    logger.debug("Processing request: %s %s", request.method, full_path)
    import time
    from .services.metrics import (
        requests_total, requests_blocked_total, requests_allowed_total,
        request_duration_seconds, active_blocked_ips, blocked_ips_total
    )
    
    start_time = time.time()
    try:
        # Extract client IP using the new helper
        normalized_ip = extract_client_ip(
            request, 
            trusted_proxies=settings.proxy_cidrs,
            honor_xff=settings.honor_x_forwarded_for
        )
        if normalized_ip is None:
            raise HTTPException(status_code=400, detail="Unable to determine client IP")

        # Get request body and headers
        body = await request.body()
        headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"

        # Create traffic sample for analysis
        sample = TrafficSample(
            client_ip=normalized_ip,
            method=request.method,
            path=path,
            headers=headers,
            content_length=len(body),
        )
        
        # Check if all services are available for full detection
        if (feature_extractor is not None and detection_engine is not None and 
            mitigation_controller is not None and telemetry_client is not None):
            # Full DDoS detection and mitigation
            logger.debug(f"🔍 Analyzing request from {normalized_ip}")
            features = await feature_extractor.compute_features(sample)
            verdict: DetectionVerdict = await detection_engine.evaluate(sample, features)
            mitigation: MitigationResult = await mitigation_controller.apply(normalized_ip, verdict)
            await telemetry_client.record(sample, verdict, mitigation)

            if not mitigation.allowed:
                logger.warning(f"🛑 Blocking request from {normalized_ip}: {verdict.reason}")
                # Record blocked metrics
                requests_blocked_total.labels(reason=verdict.reason).inc()
                blocked_ips_total.labels(reason=verdict.reason).inc()
                active_blocked_ips.set(len(detection_engine.blocklist_ips) if detection_engine else 0)
                
                duration = time.time() - start_time
                request_duration_seconds.labels(status='blocked').observe(duration)
                
                if verdict.action == MitigationAction.RATE_LIMIT:
                    return JSONResponse(status_code=429, content={"detail": "Rate limit applied"})
                if verdict.action == MitigationAction.BLOCK:
                    return JSONResponse(status_code=403, content={"detail": "Access blocked"})
                if verdict.action == MitigationAction.CHALLENGE:
                    return JSONResponse(status_code=403, content={"detail": "Challenge required"})
                return JSONResponse(status_code=403, content={"detail": "Request denied"})
            else:
                logger.debug(f"✅ Request from {normalized_ip} allowed")
                # Record allowed metrics
                requests_allowed_total.labels(risk_level=verdict.severity).inc()
        else:
            # Demo mode - allow all requests
            logger.debug(f"📋 Demo mode: allowing request from {normalized_ip}")

        # Forward request if allowed
        upstream_response = await http_client.forward(
            method=request.method,
            path=path,
            headers=headers,
            content=body if body else None,
        )

        # Record total request metrics
        requests_total.labels(status='allowed', method=request.method).inc()
        duration = time.time() - start_time
        request_duration_seconds.labels(status='allowed').observe(duration)

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers={k: v for k, v in upstream_response.headers.items()},
            media_type=upstream_response.headers.get("content-type"),
        )

    except HTTPException:
        logger.debug("HTTP exception during request processing", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error processing request"}
        )
