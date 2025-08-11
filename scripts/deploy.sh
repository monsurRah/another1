#!/bin/bash

# Deployment script for Kubernetes
set -euo pipefail

NAMESPACE="sre-microservice"

echo "Deploying SRE Microservice to Kubernetes..."

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
kubectl apply -f k8s/

# Wait for deployment to be ready
kubectl rollout status deployment/sre-microservice -n $NAMESPACE --timeout=300s

echo "Deployment completed successfully!"

# Show deployment status
kubectl get pods -n $NAMESPACE -l app=sre-microservice