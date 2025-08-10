#!/bin/bash

# Build script for SRE microservice
set -euo pipefail

echo "Building SRE Microservice..."

# Build Docker image
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VERSION=$(git describe --tags --always --dirty) \
  --build-arg VCS_REF=$(git rev-parse HEAD) \
  -t sre-microservice:latest .

echo "Build completed successfully!"

# Run security scan with Trivy if available
if command -v trivy &> /dev/null; then
    echo "Running security scan..."
    trivy image sre-microservice:latest
fi