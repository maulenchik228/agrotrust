#!/usr/bin/env bash
# Continuous delivery to a local Kubernetes cluster (bonus part of the assignment).
# Builds the image, loads it into Minikube, applies the manifests and waits for the rollout.
#   ./deploy/minikube.sh            (run from the repository root)
set -euo pipefail

IMAGE="agrotrust-metrics:latest"

minikube status >/dev/null 2>&1 || minikube start --driver=docker
docker build -t "$IMAGE" .
minikube image load "$IMAGE"
kubectl apply -f k8s/
kubectl rollout restart deployment/agrotrust-report
kubectl rollout status deployment/agrotrust-report --timeout=180s
kubectl get pods -l app=agrotrust-report -o wide
echo "Report URL:"
minikube service agrotrust-report --url
