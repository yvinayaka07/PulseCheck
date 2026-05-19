"""
PulseCheck - FastAPI Application Entry Point
Exposes health-monitoring endpoints with structured logging.
"""

from typing import Any
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.health import settings, get_logger, build_health_report

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A lightweight health-monitoring microservice that exposes real-time "
        "system metrics and external connectivity checks."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup / Shutdown events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} "
        f"[env={settings.APP_ENV}] on {settings.HOST}:{settings.PORT}"
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info(f"{settings.APP_NAME} is shutting down.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


from fastapi.responses import HTMLResponse, JSONResponse

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PulseCheck 🩺 - Observability Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080a10;
            --card-bg: rgba(15, 23, 42, 0.6);
            --card-border: rgba(255, 255, 255, 0.06);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.12);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.03) 0%, transparent 40%);
        }

        header {
            padding: 2rem 1.5rem;
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .pulse-dot {
            width: 12px;
            height: 12px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 12px var(--success);
            animation: pulse-ring 2s infinite;
        }

        @keyframes pulse-ring {
            0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .version-badge {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .btn-docs {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            color: var(--text-main);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-docs:hover {
            background: var(--primary-glow);
            border-color: var(--primary);
            box-shadow: 0 0 15px var(--primary-glow);
        }

        main {
            flex-grow: 1;
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 0 1.5rem 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 1rem;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.4);
        }

        .card:hover {
            border-color: rgba(255,255,255,0.12);
            transform: translateY(-4px);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, transparent, var(--card-glow, transparent), transparent);
        }

        .card-cpu { --card-glow: var(--primary); }
        .card-mem { --card-glow: var(--primary); }
        .card-disk { --card-glow: var(--primary); }
        .card-api { --card-glow: var(--success); }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .card-title {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .card-icon {
            font-size: 1.25rem;
        }

        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: baseline;
            gap: 0.25rem;
        }

        .metric-unit {
            font-size: 1rem;
            color: var(--text-muted);
            font-weight: 400;
        }

        .progress-track {
            height: 6px;
            background: rgba(255,255,255,0.04);
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }

        .progress-bar {
            height: 100%;
            border-radius: 999px;
            width: 0%;
            background: linear-gradient(90deg, var(--primary), #a5b4fc);
        }

        .metric-footer {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }

        .api-badge {
            background: var(--success-glow);
            border: 1px solid rgba(16, 185, 129, 0.2);
            color: var(--success);
            padding: 0.4rem 0.8rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 0 15px var(--success-glow);
        }

        .api-badge.unreachable {
            background: rgba(239, 68, 68, 0.08);
            border-color: rgba(239, 68, 68, 0.2);
            color: var(--danger);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
        }

        .api-badge.unreachable .badge-dot {
            background-color: var(--danger);
            box-shadow: 0 0 8px var(--danger);
        }

        .badge-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
        }

        .console-container {
            background: rgba(8, 10, 15, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.6);
        }

        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            padding-bottom: 0.5rem;
        }

        .console-title {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .console-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background-color: var(--primary);
        }

        .console-logs {
            height: 120px;
            overflow-y: auto;
            font-size: 0.75rem;
            line-height: 1.5;
            color: #34d399;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .log-line {
            display: flex;
            gap: 0.5rem;
        }

        .log-timestamp { color: var(--text-muted); }
        .log-level-info { color: #60a5fa; }
        .log-level-error { color: var(--danger); }

        footer {
            text-align: center;
            padding: 2rem 1.5rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            border-top: 1px solid var(--card-border);
            margin-top: 2rem;
            background: rgba(10, 15, 25, 0.4);
        }

        footer a {
            color: var(--primary);
            text-decoration: none;
        }

        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-group">
            <div class="pulse-dot"></div>
            <h1>PulseCheck</h1>
            <span class="version-badge">v1.0.0</span>
        </div>
        <a href="/docs" class="btn-docs" target="_blank">
            <span>Interactive Docs (Swagger)</span> ↗
        </a>
    </header>

    <main>
        <div class="metrics-grid">
            <div class="card card-cpu">
                <div class="card-header">
                    <span class="card-title">CPU Utilization</span>
                    <span class="card-icon">🧠</span>
                </div>
                <div>
                    <div class="metric-value">
                        <span id="cpu-val">-</span>
                        <span class="metric-unit">%</span>
                    </div>
                    <div class="progress-track">
                        <div id="cpu-bar" class="progress-bar"></div>
                    </div>
                    <div class="metric-footer">
                        <span>Load: Live</span>
                        <span>0% - 100%</span>
                    </div>
                </div>
            </div>

            <div class="card card-mem">
                <div class="card-header">
                    <span class="card-title">Memory Allocation</span>
                    <span class="card-icon">💾</span>
                </div>
                <div>
                    <div class="metric-value">
                        <span id="mem-val">-</span>
                        <span class="metric-unit">%</span>
                    </div>
                    <div class="progress-track">
                        <div id="mem-bar" class="progress-bar"></div>
                    </div>
                    <div class="metric-footer">
                        <span>Type: Virtual</span>
                        <span>0% - 100%</span>
                    </div>
                </div>
            </div>

            <div class="card card-disk">
                <div class="card-header">
                    <span class="card-title">Disk Storage</span>
                    <span class="card-icon">📁</span>
                </div>
                <div>
                    <div class="metric-value">
                        <span id="disk-val">-</span>
                        <span class="metric-unit">%</span>
                    </div>
                    <div class="progress-track">
                        <div id="disk-bar" class="progress-bar"></div>
                    </div>
                    <div class="metric-footer">
                        <span>Partition: Root</span>
                        <span>0% - 100%</span>
                    </div>
                </div>
            </div>

            <div class="card card-api">
                <div class="card-header">
                    <span class="card-title">GitHub API Connectivity</span>
                    <span class="card-icon">🌐</span>
                </div>
                <div>
                    <div style="margin-bottom: 1.5rem;">
                        <span id="api-badge" class="api-badge">
                            <span class="badge-dot"></span>
                            <span id="api-val">Checking...</span>
                        </span>
                    </div>
                    <div class="metric-footer">
                        <span>Target: api.github.com</span>
                        <span>Method: GET</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="console-container">
            <div class="console-header">
                <div class="console-title">
                    <div class="console-dot"></div>
                    <span>Service Console Logs (Live Observability)</span>
                </div>
                <div id="last-update" style="font-size: 0.7rem; color: var(--text-muted)">Last updated: -</div>
            </div>
            <div id="logs" class="console-logs">
                <div class="log-line">
                    <span class="log-timestamp">[SYSTEM INITIALIZING]</span>
                    <span class="log-level-info">[INFO]</span>
                    <span>Observability dashboard listening for health metrics...</span>
                </div>
            </div>
        </div>
    </main>

    <footer>
        <p>PulseCheck microservice © 2026. Check raw JSON at <a href="/health" target="_blank">/health</a>.</p>
    </footer>

    <script>
        const cpuVal = document.getElementById('cpu-val');
        const cpuBar = document.getElementById('cpu-bar');
        const memVal = document.getElementById('mem-val');
        const memBar = document.getElementById('mem-bar');
        const diskVal = document.getElementById('disk-val');
        const diskBar = document.getElementById('disk-bar');
        const apiVal = document.getElementById('api-val');
        const apiBadge = document.getElementById('api-badge');
        const lastUpdate = document.getElementById('last-update');
        const logsContainer = document.getElementById('logs');

        function appendLog(level, message) {
            const now = new Date().toISOString().split('T')[1].slice(0, 8);
            const line = document.createElement('div');
            line.className = 'log-line';
            line.innerHTML = `
                <span class="log-timestamp">[${now}]</span>
                <span class="log-level-${level.toLowerCase()}">[${level.toUpperCase()}]</span>
                <span>${message}</span>
            `;
            logsContainer.appendChild(line);
            logsContainer.scrollTop = logsContainer.scrollHeight;
            
            while (logsContainer.children.length > 8) {
                logsContainer.removeChild(logsContainer.firstChild);
            }
        }

        async function fetchMetrics() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                cpuVal.innerText = data.cpu_usage_percent;
                cpuBar.style.width = `${data.cpu_usage_percent}%`;
                setBarColor(cpuBar, data.cpu_usage_percent);

                memVal.innerText = data.memory_usage_percent;
                memBar.style.width = `${data.memory_usage_percent}%`;
                setBarColor(memBar, data.memory_usage_percent);

                diskVal.innerText = data.disk_usage_percent;
                diskBar.style.width = `${data.disk_usage_percent}%`;
                setBarColor(diskBar, data.disk_usage_percent);

                if (data.external_api_status === 'reachable') {
                    apiVal.innerText = 'REACHABLE';
                    apiBadge.className = 'api-badge';
                    appendLog('info', `GET /health 200 OK | CPU: ${data.cpu_usage_percent}% | GitHub API: reachable`);
                } else {
                    apiVal.innerText = 'UNREACHABLE';
                    apiBadge.className = 'api-badge unreachable';
                    appendLog('error', `GET /health 200 OK | CPU: ${data.cpu_usage_percent}% | GitHub API: unreachable`);
                }

                lastUpdate.innerText = `Last updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
            } catch (err) {
                appendLog('error', `Failed to poll health check: ${err.message}`);
            }
        }

        function setBarColor(barElement, value) {
            if (value > 85) {
                barElement.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
            } else if (value > 60) {
                barElement.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
            } else {
                barElement.style.background = 'linear-gradient(90deg, #10b981, #34d399)';
            }
        }

        fetchMetrics();
        setInterval(fetchMetrics, 3000);
    </script>
</body>
</html>
"""

@app.get(
    "/",
    summary="Root endpoint",
    response_description="Interactive Observability Dashboard or Service Identity JSON",
    tags=["General"],
)
async def root(request: Request) -> Any:
    """
    Renders the live PulseCheck observability dashboard for browsers,
    or returns service identity for API queries.
    """
    logger.info("GET / called")
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(content=DASHBOARD_HTML)
    return JSONResponse(
        content={
            "service": settings.APP_NAME,
            "status": "running",
        }
    )


@app.get(
    "/health",
    summary="Health check endpoint",
    response_description="System metrics and external API reachability",
    tags=["Health"],
)
async def health_check() -> JSONResponse:
    """
    Returns a comprehensive health report including:
    - Overall service status
    - ISO-8601 UTC timestamp
    - CPU, memory, and disk usage percentages
    - External API reachability (https://api.github.com)
    """
    logger.info("GET /health called")
    try:
        report = build_health_report()
        return JSONResponse(content=report)
    except Exception as exc:
        logger.error(f"Health check failed with unexpected error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while collecting health metrics.",
        )



# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
