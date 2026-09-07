#!/bin/bash

echo "🚀 Starting all Port-Forwards and Services for Demo..."

# ניקוי פורטים תפוסים מריצות קודמות למניעת שגיאות
killall kubectl 2>/dev/null
pkill ngrok 2>/dev/null

# פונקציה לסגירה נקייה של כל התהליכים בלחיצה על Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Shutting down all port-forwards and tunnels..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# 1. Monitoring & Observability
kubectl port-forward --address 127.0.0.1 svc/prometheus-stack-grafana 3000:80 -n monitoring >/dev/null 2>&1 &
kubectl port-forward --address 127.0.0.1 svc/prometheus-stack-kube-prom-prometheus 9090:9090 -n monitoring >/dev/null 2>&1 &
kubectl port-forward --address 127.0.0.1 svc/prometheus-stack-kube-prom-alertmanager 9093:9093 -n monitoring >/dev/null 2>&1 &

# 2. CI/CD & Pipeline
kubectl port-forward --address 127.0.0.1 svc/jenkins 8888:8080 -n jenkins >/dev/null 2>&1 &

# 3. Application (Frontend + Backend API)
kubectl port-forward --address 127.0.0.1 svc/frontend 8081:8080 -n devops-app >/dev/null 2>&1 &
kubectl port-forward --address 127.0.0.1 deploy/backend 5001:5001 -n devops-app >/dev/null 2>&1 &

# 4. Ngrok Webhook Tunnel
ngrok http 8888 >/dev/null 2>&1 &

sleep 2

echo "========================================================="
echo "✅ ALL SYSTEMS ONLINE AND ACCESSIBLE:"
echo "========================================================="
echo "📊 Grafana:        http://127.0.0.1:3000"
echo "🔥 Prometheus:     http://127.0.0.1:9090"
echo "🚨 Alertmanager:   http://127.0.0.1:9093"
echo "🏗️  Jenkins:        http://127.0.0.1:8888"
echo "🎮 Frontend App:   http://127.0.0.1:8081"
echo "⚙️  Backend API:    http://127.0.0.1:5001"
echo "🌐 Ngrok (Jenkins): https://tipped-acre-supremacy.ngrok-free.dev"
echo "========================================================="
echo "Press [Ctrl + C] anytime to stop all services cleanly."

wait