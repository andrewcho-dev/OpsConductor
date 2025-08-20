# MICROSERVICES SEPARATION IMPLEMENTATION PLAN

## 🎯 GOAL: Extract Monitoring Services from Main Application

### CURRENT STATE ANALYSIS:
```
Your current docker-compose.yml contains:
├── Business Services (KEEP)
│   ├── auth-service
│   ├── backend  
│   ├── frontend
│   ├── postgres
│   ├── redis
│   └── nginx
└── Monitoring Services (EXTRACT)
    ├── prometheus ← MOVE OUT
    └── grafana    ← MOVE OUT
```

---

## 📁 PROPOSED FILE STRUCTURE:

```
opsconductor/
├── docker-compose.yml                    # Main business services
├── docker-compose.observability.yml      # Monitoring & logging
├── docker-compose.override.yml           # Development overrides
├── .env                                  # Shared environment
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── datasources/
│   └── loki/
│       └── loki-config.yml
└── logging/
    ├── promtail/
    │   └── promtail-config.yml
    └── filebeat/
        └── filebeat.yml
```

---

## 🔧 IMPLEMENTATION STEPS:

### STEP 1: Create Business Services Only (docker-compose.yml)
```yaml
# docker-compose.yml - BUSINESS SERVICES ONLY
name: opsconductor

services:
  # =============================================================================
  # BUSINESS SERVICES
  # =============================================================================
  auth-service:
    # ... existing config ...
    networks:
      - app-network
      - monitoring-network  # Allow monitoring access

  backend:
    # ... existing config ...
    networks:
      - app-network
      - monitoring-network  # Allow monitoring access

  frontend:
    # ... existing config ...
    networks:
      - app-network

  postgres:
    # ... existing config ...
    networks:
      - app-network

  redis:
    # ... existing config ...
    networks:
      - app-network

  nginx:
    # ... existing config ...
    networks:
      - app-network
    ports:
      - "80:80"
      - "443:443"

networks:
  app-network:
    driver: bridge
  monitoring-network:
    external: true  # Created by observability stack

volumes:
  postgres_data:
  # ... other business volumes ...
```

### STEP 2: Create Observability Services (docker-compose.observability.yml)
```yaml
# docker-compose.observability.yml - MONITORING & LOGGING ONLY
name: opsconductor-observability

services:
  # =============================================================================
  # LOG AGGREGATION
  # =============================================================================
  loki:
    image: grafana/loki:2.9.0
    container_name: observability-loki
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
    networks:
      - monitoring-network
    restart: unless-stopped

  # =============================================================================
  # LOG COLLECTION
  # =============================================================================
  promtail:
    image: grafana/promtail:2.9.0
    container_name: observability-promtail
    volumes:
      # Collect from ALL containers (including business services)
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./logging/promtail/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring-network
    depends_on:
      - loki
    restart: unless-stopped

  # =============================================================================
  # METRICS COLLECTION
  # =============================================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: observability-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - monitoring-network
    ports:
      - "9090:9090"
    restart: unless-stopped

  # =============================================================================
  # VISUALIZATION
  # =============================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: observability-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - monitoring-network
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
      - loki
    restart: unless-stopped

  # =============================================================================
  # ALERTING
  # =============================================================================
  alertmanager:
    image: prom/alertmanager:latest
    container_name: observability-alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    volumes:
      - ./monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    networks:
      - monitoring-network
    ports:
      - "9093:9093"
    restart: unless-stopped

networks:
  monitoring-network:
    driver: bridge

volumes:
  loki_data:
  prometheus_data:
  grafana_data:
  alertmanager_data:
```

---

## 🚀 DEPLOYMENT COMMANDS:

### Start Business Services Only:
```bash
docker-compose up -d
```

### Start Observability Services Only:
```bash
docker-compose -f docker-compose.observability.yml up -d
```

### Start Everything:
```bash
# Create shared network first
docker network create monitoring-network

# Start observability services
docker-compose -f docker-compose.observability.yml up -d

# Start business services
docker-compose up -d
```

### Development (All Together):
```bash
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```

---

## 🔍 DATA COLLECTION STRATEGY:

### How Promtail Collects from Separated Services:
```
┌─────────────────────────────────────────────────────────────────┐
│                    HOST MACHINE                                 │
│                                                                 │
│  /var/lib/docker/containers/                                   │
│  ├── opsconductor-auth-service/                               │
│  ├── opsconductor-backend/                                    │
│  ├── opsconductor-frontend/                                   │
│  └── opsconductor-nginx/                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PROMTAIL CONTAINER                         │   │
│  │                                                         │   │
│  │  Mounts: /var/lib/docker/containers:ro                │   │
│  │  Reads: ALL container logs automatically               │   │
│  │  Filters: By container labels & names                  │   │
│  │  Sends: To Loki in observability stack                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ BENEFITS OF THIS APPROACH:

1. **🔄 Independent Scaling**: Scale business services separately from monitoring
2. **🛡️ Isolation**: Monitoring issues don't affect business services
3. **🔧 Maintenance**: Update monitoring stack without touching business logic
4. **💰 Cost Optimization**: Run monitoring on different hardware/cloud instances
5. **🏗️ True Microservices**: Each concern is properly separated
6. **🚀 Deployment Flexibility**: Deploy business services without monitoring overhead

---

## 🎯 MIGRATION PATH:

### Phase 1: File Separation (This Week)
- Split docker-compose files
- Test both stacks work independently
- Verify log collection across networks

### Phase 2: Network Isolation (Next Week)  
- Implement proper network segmentation
- Add security between networks
- Test cross-network communication

### Phase 3: Host Separation (Future)
- Move observability to dedicated hosts
- Implement remote log shipping
- Add high availability for monitoring
```