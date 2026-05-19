# PulseCheck 🩺

> A production-grade, highly-optimized health-monitoring microservice and real-time observability dashboard built with **FastAPI**, **Docker**, and **AWS ECS Fargate**. Designed as a high-fidelity showcase for DevOps screening.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-multi--stage-blue?logo=docker)](https://www.docker.com/)

---

## ⚡ 60-Second Quick Evaluation Guide (For the Hiring Team)
To make your evaluation as seamless as possible, here is how you can review and run this entire project in under a minute:

### 1. Run the Local CI/CD Pipeline Simulator (Tests + Build + Coverage)
This script runs the unit tests, prints a code coverage table, checks Docker, builds the image, runs a background container, and tests it.
* **On Windows (PowerShell)**:
  ```powershell
  Set-ExecutionPolicy Bypass -Scope Process
  .\run-pipeline.ps1
  ```
* **On macOS/Linux (Bash)**:
  ```bash
  chmod +x run-pipeline.sh
  ./run-pipeline.sh
  ```

### 2. Launch the Application Locally
Run this single command to start the FastAPI server with hot-reloading:
```powershell
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*(If on macOS/Linux, run `.venv/bin/uvicorn app.main:app --reload`)*

### 3. Open the Observing Features
Once the server is running, open your web browser to check:
* 🩺 **Live Observability Dashboard**: [http://localhost:8000/](http://localhost:8000/)  
  *(A gorgeous real-time glassmorphic UI tracking CPU/Memory/Disk and API status with active terminal logs!)*
* 📄 **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 📊 **Raw JSON Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🌟 Screening Rubric Mapping
Here is how the project addresses every requirement in the screening prompt:

| Requirement Phase | Feature Implemented | Codebase Location |
|---|---|---|
| **Phase 1: Application** | Lightweight **FastAPI** service capturing live system resource usage (`psutil`) and GitHub API connectivity with automated retries. | [app/health.py](file:///c:/Users/user/Desktop/pulsecheck/app/health.py) |
| **Phase 1: Containerization** | **Multi-stage, production-ready Dockerfile** separating dependencies from the final minimal runtime image. Runs under a secure **non-root user**. | [Dockerfile](file:///c:/Users/user/Desktop/pulsecheck/Dockerfile) |
| **Phase 2: CI/CD Pipeline** | Fully defined **GitHub Actions CI/CD pipeline** running automated unit tests with coverage, building Docker image, and executing a containerized smoke-test. | [.github/workflows/ci.yml](file:///c:/Users/user/Desktop/pulsecheck/.github/workflows/ci.yml) |
| **Phase 3: IaC** | **AWS CloudFormation template** provisioning the Serverless compute infrastructure: ECS Fargate, Task Definitions, CloudWatch logging, VPC Security Groups, and IAM roles. | [infrastructure/cloudformation.yml](file:///c:/Users/user/Desktop/pulsecheck/infrastructure/cloudformation.yml) |
| **Option B: Local Showcase** | Dedicated shell scripts (`.sh` & `.ps1`) simulating the entire pipeline locally, reporting test results and Docker builds. | [run-pipeline.ps1](file:///c:/Users/user/Desktop/pulsecheck/run-pipeline.ps1) & [run-pipeline.sh](file:///c:/Users/user/Desktop/pulsecheck/run-pipeline.sh) |
| **Going the Extra Mile 🚀** | **Content-negotiated frontend Dashboard**: Returns a gorgeous observational dashboard to browsers (`text/html`), but maintains raw JSON status response to CLI tools (`application/json`). | [app/main.py](file:///c:/Users/user/Desktop/pulsecheck/app/main.py) |

---

## 📁 Flat & Clean Repository Directory
The internal codebase has been aggressively flattened to eliminate redundant boilerplate files (like `config.py` or package files) to make it highly readable and clean:

```
pulsecheck/
│
├── app/
│   ├── main.py              # FastAPI app, content-negotiated dashboard, entrypoint
│   ├── health.py            # Metrics logic, retry HTTP session, Settings & Logger
│   └── requirements.txt     # Python dependencies
│
├── tests/
│   └── test_health.py       # pytest test suite (21 assertions)
│
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD automation pipeline
│
├── infrastructure/
│   └── cloudformation.yml   # AWS CloudFormation IaC (ECS Fargate Serverless)
│
├── Dockerfile               # Production multi-stage container
├── docker-compose.yml       # Local container orchestrator
├── run-pipeline.ps1         # Windows PowerShell Local Pipeline Simulator
├── run-pipeline.sh          # UNIX/Linux Local Pipeline Simulator
└── README.md                # Evaluator Quick-Start & Spec documentation
```

---

## 🛠️ Deep Dive: Local Pipeline Simulator
The simulator executes three critical CI/CD stages locally:
1. **Unit & Integration Tests**: Runs pytest and prints a complete coverage matrix showing which lines are tested.
2. **Multi-Stage Docker Build**: Compiles the secure production-grade container image.
3. **Background Smoke Test**: Launches the built container in the background, waits for boot, probes the `/health` endpoint to verify a `200 OK` JSON response, outputs the payload, and safely stops and removes the container.

---

## 📦 Local Container Commands

### Build the Image Manually
```bash
docker build -t pulsecheck:latest .
```

### Run via Docker Compose
```bash
docker compose up --build
```
The application will map port `8000` to your host machine automatically.

---

## 🧪 Testing Suite Spec
Our automated testing suite covers:
- Service root identity & Content Negotiation checks.
- System metrics validation (CPU, Memory, Disk boundaries).
- Mocking external API responses (unreachable, timeout, HTTP 403, and retry-handling).

To run the tests manually:
```bash
python -m pytest tests/ --cov=app -v
```

---

## ☁️ AWS Cloud Computing Choice (ECS Fargate)
For a lightweight microservice, **AWS ECS Fargate (Serverless CaaS)** represents the most optimized compute tier:
- **No Server Management**: No virtual servers (EC2) or Kubernetes nodes (EKS) to manage, patch, or pay for while idle.
- **Granular Billing**: Billed strictly per-second based on the exact allocated CPU and memory (set to `0.25 vCPU` and `0.5 GB RAM` in the CloudFormation template).
- **Inherent Security**: Run inside private subnets in your custom VPC with strict Security Groups.

---

## 📝 Example Health JSON Payload
Querying `/health` returns the following payload:
```json
{
  "status": "healthy",
  "timestamp": "2026-05-19T13:48:35.123456+00:00",
  "cpu_usage_percent": 12.5,
  "memory_usage_percent": 64.2,
  "disk_usage_percent": 48.9,
  "external_api_status": "reachable"
}
```

---

## License
MIT © 2026 PulseCheck Contributors. All rights reserved.
