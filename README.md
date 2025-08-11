# SRE Microservice Assessment

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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker
- Docker Compose
- Kubernetes (Minikube/Kind for local testing)

### Setup
1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd sre-microservice-assessment
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Tests:**
   ```bash
   ./scripts/run-tests.sh
   ```

4. **Build Docker Image:**
   ```bash
   ./scripts/build.sh
   ```

## 🛠️ Local Development

### Run Locally
```bash
# Direct Python execution
python src/app/main.py

# Using Docker Compose
docker-compose up
```

### Deploy to Kubernetes
```bash
./scripts/deploy.sh
```

### Load Testing
```bash
./scripts/load-test.sh http://localhost:8000
```

## 📊 Monitoring & Observability

### Prometheus Integration
The service exposes metrics at `/metrics` endpoint including:
- HTTP request rates and response times
- Error counts and types
- Custom business metrics

### Grafana Dashboard
Prometheus Operator + Grafana is recommended to enable collaboration on a central dashboard. Full implementation details are beyond the scope of this assessment.

## 🔧 Technology Stack

### Core Decisions

**Python over Go**
- **Development Velocity**: Python's syntax and extensive standard library enable faster development cycles, crucial for SRE teams that need to iterate quickly on monitoring and operational tools
- **Data Analysis Ecosystem**: The `statistics` module provides production-ready implementations of statistical functions, reducing the risk of mathematical errors compared to implementing these from scratch in Go

**FastAPI over Alternatives**
- **Type Safety**: FastAPI with Pydantic provides compile-time type checking and runtime validation, reducing production errors
- **Performance**: Modern async support with high throughput capabilities
- **Developer Experience**: Automatic API documentation and validation

**Bash over Python for Scripts**
- **Universal Availability**: Bash is available in all Unix-like environments without additional installation, crucial for CI/CD pipelines and production environments
- **System Integration**: Native integration with system utilities and commands

**Kubernetes over Nomad**
- **Industry Standard**: Kubernetes is the de facto standard with 88% market adoption, ensuring better long-term support and team familiarity
- **Rich Ecosystem**: Extensive tooling and community support

## 📁 Project Structure

```
sre-microservice-assessment/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # Main FastAPI application
│   └── tests/
│       ├── __init__.py
│       └── test_main.py         # Comprehensive test suite
├── k8s/
│   ├── namespace.yaml           # Kubernetes namespace
│   ├── deployment.yaml          # Application deployment
│   ├── service.yaml            # LoadBalancer service
│   ├── hpa.yaml               # Horizontal Pod Autoscaler
│   └── ingress.yaml           # Ingress configuration
├── scripts/
│   ├── build.sh               # Docker build script
│   ├── run-tests.sh          # Test execution script
│   ├── deploy.sh             # Kubernetes deployment script
│   └── load-test.sh          # Load testing with analysis
├── docs/
├── Dockerfile                 # Multi-stage production Dockerfile
├── docker-compose.yml         # Local development setup
├── nginx.conf                # Load balancer configuration
├── Jenkinsfile               # Complete CI/CD pipeline
├── requirements.txt          # Python dependencies
├── README.md                # Comprehensive documentation


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions and support, please open an issue in the repository or contact the SRE team.