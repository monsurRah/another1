Welcome to a production-grade microservice featuring comprehensive data analysis capabilities, graceful shutdown mechanisms, and zero-downtime deployment strategies.

## 📋 API Endpoints

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint  
- `GET /metrics` - Prometheus metrics

### Data Processing
- `POST /payload` - Process JSON payload with numeric and text analysis

#### Payload Structure
```json
{
  "numbers": [1, 2, 3, 4, 5],
  "text": "Sample text for analysis"
}
```

#### Response Structure
```json
{
  "numeric_analysis": {
    "minimum": 1.0,
    "maximum": 5.0,
    "mean": 3.0,
    "median": 3.0,
    "standard_deviation": 1.58,
    "count": 5
  },
  "text_analysis": {
    "word_count": 4,
    "character_count": 25,
    "character_count_no_spaces": 21,
    "sentence_count": 1,
    "paragraph_count": 1
  },
  "processing_time_ms": 12.34
}
```

## 🏗️ Architecture & Design Decisions

### Graceful Shutdown Implementation
The service implements a sophisticated graceful shutdown mechanism:
- **Signal Handling**: Captures SIGTERM/SIGINT signals
- **Request Tracking**: Maintains count of active requests
- **Graceful Termination**: Stops accepting new requests while allowing in-flight requests to complete
- **Timeout Protection**: Kubernetes terminationGracePeriodSeconds ensures forced termination if needed

### Asynchronous Processing
- Uses FastAPI's async capabilities for concurrent request handling
- Implements asyncio.gather() for parallel numeric and text analysis
- Optimizes performance through non-blocking I/O operations

### Security Measures
- **Input Validation**: Pydantic models with size limits to prevent DoS attacks
- **Container Security**: Non-root user execution, minimal base images
- **Dependency Scanning**: Automated security scans in CI/CD pipeline

### Zero-Downtime Deployment Strategy
- **Rolling Updates**: maxUnavailable: 0, maxSurge: 1
- **Readiness Probes**: Prevent traffic routing to non-ready pods
- **Liveness Probes**: Automatic restart of unhealthy containers
- **PreStop Hook**: 10-second delay for connection draining

Setup project by cloning repo.
cd sre-microservice-assessment

## 🚀 Quick Start Commands

1. **Install Dependencies:**
   
   pip install -r requirements.txt
   

2. **Run Tests:**
   
   ./scripts/run-tests.sh
   

3. **Build Docker Image:**
   
   ./scripts/build.sh
   

4. 

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Docker
- Docker Compose
- Kubernetes (Minikube/Kind for local testing)
  **Run Locally:**  
   python src/app/main.py
   # or
   docker-compose up
   

5. **Deploy to Kubernetes:**
   
   ./scripts/deploy.sh
   

6. **Run Load Tests:**
   ```bash
   ./scripts/load-test.sh http://localhost:8000


 **Other Consideration:**
 Prometheus Operator + Grafana is recommended to enable colloboration on a central dashboard.
 Full implementation details is out of the scope of the assessment. 

Technology Stack Decisions:
**Python over Go:** Development velocity and operational tooling ecosystem.
Python's syntax and extensive standard library enable faster development cycles, crucial for SRE teams that need to iterate quickly on monitoring and operational tools. Data Analysis Ecosystem**: The `statistics` module provides production-ready implementations of statistical functions, reducing the risk of mathematical errors compared to implementing these from scratch in Go
**FastAPI over alternatives:** Type safety, performance, and modern async support. FastAPI with Pydantic provides compile-time type checking and runtime validation, reducing production errors.

**Bash over Python for scripts:** Universal availability and system integration. Bash is available in all Unix-like environments without additional installation, crucial for CI/CD pipelines and production environments.
**Kubernetes over Nomad:** Industry standard with rich ecosystem. Kubernetes is the de facto standard with 88% market adoption, ensuring better long-term support and team familiarity.