#!/bin/bash
set -e

# Configuration
NAMESPACE="tiga-system"
DEPLOYMENT="tiga-agent"
SERVICE="tiga-agent-service"
GREEN_VERSION=$1

if [ -z "$GREEN_VERSION" ]; then
  echo "Usage: ./deploy.sh <version_tag>"
  exit 1
fi

echo "Starting Blue/Green Deployment for version: $GREEN_VERSION"

# 1. Deploy Green Version
echo "Deploying Green version..."
helm upgrade --install tiga-agent-green ./charts/tiga-agent \
  --namespace $NAMESPACE \
  --set image.tag=$GREEN_VERSION \
  --set service.enabled=false \
  --wait

# 2. Run Smoke Tests
echo "Running smoke tests on Green version..."
GREEN_POD=$(kubectl get pods -n $NAMESPACE -l app=tiga-agent,release=tiga-agent-green -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n $NAMESPACE $GREEN_POD -- curl -s http://localhost:8000/health | grep "ok"

if [ $? -ne 0 ]; then
  echo "Smoke tests failed! Rolling back..."
  helm uninstall tiga-agent-green -n $NAMESPACE
  exit 1
fi

# 3. Switch Traffic (Update Service Selector)
echo "Switching traffic to Green version..."
kubectl patch service $SERVICE -n $NAMESPACE -p '{"spec":{"selector":{"release":"tiga-agent-green"}}}'

# 4. Scale Down Blue Version (Optional: Keep for quick rollback)
# echo "Scaling down Blue version..."
# helm uninstall tiga-agent-blue -n $NAMESPACE

echo "Deployment Successful!"
