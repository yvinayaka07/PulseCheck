#!/usr/bin/env bash
# =============================================================================
# PulseCheck – Local CI/CD Pipeline Simulator (Bash)
# Usage: ./run-pipeline.sh
# =============================================================================

set -e

# Visual styling
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN} 🩺 PulseCheck Local CI/CD Pipeline Simulator${NC}"
echo -e "${GREEN}====================================================${NC}"
echo ""

# ── Step 1: Unit & Endpoint Tests ───────────────────────────────────────────
echo -e "${CYAN}[1/3] Running automated unit and integration tests...${NC}"
if [ -d ".venv" ]; then
    .venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing
else
    python3 -m pytest tests/ --cov=app --cov-report=term-missing
fi
echo -e "${GREEN}✅ All tests passed successfully!${NC}"
echo ""

# ── Docker Check ─────────────────────────────────────────────────────────────
echo -e "${GRAY}Checking local containerization environment...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker is not installed or not in system PATH.${NC}"
    echo -e "${YELLOW}Skipping containerization steps. Install Docker to test multi-stage builds locally.${NC}"
    echo ""
    echo -e "${GREEN}====================================================${NC}"
    echo -e "${GREEN} 🎉 Local Pipeline Passed (Tests Only - Docker Skipped)${NC}"
    echo -e "${GREEN}====================================================${NC}"
    exit 0
fi

# Check if daemon is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker daemon is not running.${NC}"
    echo -e "${YELLOW}Skipping containerization steps. Start Docker Desktop to test multi-stage builds locally.${NC}"
    echo ""
    echo -e "${GREEN}====================================================${NC}"
    echo -e "${GREEN} 🎉 Local Pipeline Passed (Tests Only - Daemon Skipped)${NC}"
    echo -e "${GREEN}====================================================${NC}"
    exit 0
fi

echo -e "${GREEN}✅ Docker environment is available and healthy.${NC}"
echo ""

# ── Step 2: Build Container Image ────────────────────────────────────────────
echo -e "${CYAN}[2/3] Building Docker container image (multi-stage)...${NC}"
docker build -t pulsecheck:latest .
echo -e "${GREEN}✅ Docker image built successfully: pulsecheck:latest${NC}"
echo ""

# ── Step 3: Containerized Smoke Test Deployment ──────────────────────────────
echo -e "${CYAN}[3/3] Simulating smoke-test deployment...${NC}"

# Stop and remove existing container if it exists
echo -e "${GRAY}Cleaning up any old smoke-test containers...${NC}"
docker stop pulsecheck_smoke_test >/dev/null 2>&1 || true
docker rm pulsecheck_smoke_test >/dev/null 2>&1 || true

# Run new container
echo -e "${GRAY}Launching containerized service in background...${NC}"
docker run -d --name pulsecheck_smoke_test -p 8000:8000 -e APP_ENV=production pulsecheck:latest >/dev/null

# Wait for application startup
echo -e "${YELLOW}Waiting for service to boot (8 seconds)...${NC}"
sleep 8

# Query application status
echo -e "${GRAY}Sending HTTP probe to container health-check endpoint...${NC}"
if response=$(curl --fail --silent http://localhost:8000/health); then
    # Check if healthy
    if echo "$response" | grep -q '"status":"healthy"'; then
        echo -e "${GREEN}✅ Smoke test passed successfully! Container responds correctly.${NC}"
        echo ""
        echo -e "${GREEN}====================================================${NC}"
        echo -e "${GREEN} 🎉 Local Pipeline Execution Completed Successfully!${NC}"
        echo -e "${GREEN}====================================================${NC}"
        echo ""
        echo -e "${GRAY}Response Payload:${NC}"
        echo "$response" | python3 -m json.tool || echo "$response"
    else
        echo -e "${RED}❌ Smoke test failed! Status not healthy.${NC}"
        echo "$response"
        exit 1
    fi
else
    echo -e "${RED}❌ Smoke test failed! Could not reach container or check failed.${NC}"
    echo ""
    echo -e "${YELLOW}Retrieving container logs for debugging:${NC}"
    docker logs pulsecheck_smoke_test
    docker stop pulsecheck_smoke_test >/dev/null 2>&1 || true
    docker rm pulsecheck_smoke_test >/dev/null 2>&1 || true
    exit 1
fi

# Clean up container
echo ""
echo -e "${GRAY}Cleaning up smoke-test container...${NC}"
docker stop pulsecheck_smoke_test >/dev/null
docker rm pulsecheck_smoke_test >/dev/null
echo -e "${GREEN}Cleanup complete. Project is healthy. 🚀${NC}"
