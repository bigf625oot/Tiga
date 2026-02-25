#!/bin/bash
set -e

# Configuration
NAMESPACE="tiga-system"
SERVICE="tiga-agent-service"

echo "Initiating Rollback..."

# 1. Identify Current Green (Active) and Blue (Inactive)
CURRENT_SELECTOR=$(kubectl get service $SERVICE -n $NAMESPACE -o jsonpath="{.spec.selector.release}")

if [ "$CURRENT_SELECTOR" == "tiga-agent-green" ]; then
  TARGET="tiga-agent-blue"
else
  TARGET="tiga-agent-green"
fi

echo "Rolling back traffic to: $TARGET"

# 2. Verify Target Health
TARGET_POD=$(kubectl get pods -n $NAMESPACE -l app=tiga-agent,release=$TARGET -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n $NAMESPACE $TARGET_POD -- curl -s http://localhost:8000/health | grep "ok"

if [ $? -ne 0 ]; then
  echo "Target version is unhealthy! Cannot rollback automatically. Manual intervention required."
  exit 1
fi

# 3. Switch Traffic
kubectl patch service $SERVICE -n $NAMESPACE -p "{\"spec\":{\"selector\":{\"release\":\"$TARGET\"}}}"

echo "Rollback Successful! Traffic is now served by $TARGET."
