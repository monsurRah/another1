#!/bin/bash

# Test execution script
set -euo pipefail

echo "Running tests for SRE Microservice..."

# Install test dependencies
pip install -r requirements.txt

# Run unit tests with coverage
python -m pytest src/tests/ -v --cov=src/app --cov-report=html --cov-report=term

echo "Tests completed successfully!"