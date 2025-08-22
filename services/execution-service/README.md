# 🚀 OpsConductor Distributed Execution Service

## 🎯 **Architecture Overview**

This is the distributed Celery worker architecture for OpsConductor, providing:

- **2 Specialized Workers** + **1 Beat Scheduler** + **1 Node-RED Instance**
- **High-Performance Job Execution** with dedicated resource allocation
- **Visual Workflow Designer** with Node-RED integration
- **Automatic Task Distribution** based on queue priorities

---

## 🏗️ **Architecture Components**

### **🔥 Execution Worker** (Heavy Lifting)
```yaml
Role: Job execution powerhouse
Tasks: SSH connections, command execution, file transfers
Resources: 4 CPU cores, 8GB RAM, 8 concurrent tasks
Queue: execution (high priority)
```

### **🛠️ System Worker** (Maintenance)
```yaml
Role: Background system maintenance  
Tasks: Cleanup, health checks, discovery, metrics
Resources: 2 CPU cores, 4GB RAM, 4 concurrent tasks
Queue: system (normal priority)
```

### **⏰ System Scheduler** (Beat)
```yaml
Role: Periodic task coordinator
Tasks: Schedules all recurring tasks
Resources: 1 CPU core, 2GB RAM
Manages: Health checks, cleanup, discovery scans
```

### **🎨 Node-RED** (Visual Workflows)
```yaml
Role: Visual workflow designer
Interface: Drag-and-drop workflow creation
Access: http://localhost:8080
Custom Nodes: OpsConductor integration nodes
```

---

## 🚀 **Quick Start**

### **1. Start All Workers**
```bash
cd /home/enabledrm/services/execution-service
./start-distributed-workers.sh
```

### **2. Verify Status**
```bash
docker-compose -f docker-compose.workers.yml ps
```

### **3. Access Node-RED**
```bash
open http://localhost:8080
```

---

## 📊 **Monitoring & Management**

### **📋 View Worker Logs**
```bash
# All workers
docker-compose -f docker-compose.workers.yml logs -f

# Specific worker
docker-compose -f docker-compose.workers.yml logs -f execution-worker
docker-compose -f docker-compose.workers.yml logs -f system-worker
docker-compose -f docker-compose.workers.yml logs -f system-scheduler
```

### **🔧 Worker Management**
```bash
# Restart specific worker
docker-compose -f docker-compose.workers.yml restart execution-worker

# Scale execution workers for high load
docker-compose -f docker-compose.workers.yml up -d --scale execution-worker=3

# Stop all workers
docker-compose -f docker-compose.workers.yml down
```

### **📈 Celery Monitoring**
```bash
# Check worker status
docker exec execution-worker celery -A app.celery_app inspect ping
docker exec system-worker celery -A app.celery_app inspect ping

# View active tasks
docker exec execution-worker celery -A app.celery_app inspect active

# View queue stats
docker exec execution-worker celery -A app.celery_app inspect stats
```

---

## 🎯 **Task Distribution**

### **🔥 Execution Queue (High Priority)**
```python
Tasks routed here:
├── execute_job_task()              # Main job execution
├── execute_single_target_task()    # Single target execution  
├── retry_failed_execution()        # Retry failed jobs
├── upload_execution_artifacts()    # Upload results to storage
└── check_execution_timeouts()      # Monitor execution timeouts
```

### **🛠️ System Queue (Normal Priority)**  
```python
Tasks routed here:
├── cleanup_old_executions()        # Database cleanup
├── collect_system_metrics()        # Performance monitoring
├── compress_large_outputs()        # Storage optimization
├── auto_discovery_scan()           # Network discovery
├── validate_discovered_targets()   # Target validation
├── check_all_services_health()     # Health monitoring
└── generate_health_report()        # System health reports
```

---

## 🔄 **Scheduled Tasks (Beat)**

### **⏰ Automatic Schedules**
```yaml
Health Checks: Every 5 minutes
Database Cleanup: Every hour  
System Metrics: Every 10 minutes
Network Discovery: Every 30 minutes
Timeout Checks: Every 2 minutes
```

### **📝 Custom Schedules**
Edit `app/celery_app.py` to add custom periodic tasks:
```python
app.conf.beat_schedule = {
    'your-custom-task': {
        'task': 'app.tasks.your_tasks.your_function',
        'schedule': 3600.0,  # Every hour
        'options': {'queue': 'system'}
    },
}
```

---

## 🎨 **Node-RED Integration**

### **🔧 Custom OpsConductor Nodes**
```javascript
Available Nodes:
├── Target Selector      # Select targets by filters
├── Command Executor     # Execute commands via OpsConductor
├── Health Checker       # Check target/service health
└── Audit Logger        # Log workflow events
```

### **🌊 Example Workflow**
```mermaid
graph LR
    A[Timer: Every Hour] --> B[Target Selector: Production Servers]
    B --> C[Health Checker: Test Connectivity]
    C --> D{All Healthy?}
    D -->|Yes| E[Log: System Healthy]
    D -->|No| F[Command Executor: Restart Services]
    F --> G[Audit Logger: Record Actions]
```

---

## 🔧 **Configuration**

### **🌍 Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@execution-db:5432/execution_service

# Redis  
REDIS_URL=redis://redis:6379/0

# Worker Configuration
CELERY_WORKER_CONCURRENCY=8
MAX_CONCURRENT_TARGETS=50
CONNECTION_TIMEOUT=30
COMMAND_TIMEOUT=600

# Discovery
AUTO_DISCOVERY_NETWORKS=["192.168.1.0/24", "10.0.0.0/24"]

# Node-RED
OPSCONDUCTOR_API_URL=http://targets-service:8000
OPSCONDUCTOR_TOKEN=your-api-token
```

### **⚙️ Resource Allocation**
```yaml
execution-worker:
  cpus: 4.0
  memory: 8G
  concurrency: 8

system-worker:
  cpus: 2.0  
  memory: 4G
  concurrency: 4

system-scheduler:
  cpus: 1.0
  memory: 2G
  
node-red:
  cpus: 1.0
  memory: 2G
```

---

## 🧪 **Testing**

### **🔬 Test Worker Connectivity**
```bash
# Test execution worker
docker exec execution-worker celery -A app.celery_app inspect ping

# Test system worker
docker exec system-worker celery -A app.celery_app inspect ping

# Submit test task
docker exec execution-worker python -c "
from app.tasks.system_tasks import collect_system_metrics
result = collect_system_metrics.delay()
print(f'Task ID: {result.id}')
print(f'Result: {result.get()}')"
```

### **🎯 Test Node-RED Integration**
1. Open http://localhost:8080
2. Create a simple flow with an OpsConductor Target Selector
3. Configure it to select targets
4. Deploy and test the flow

---

## 🚨 **Troubleshooting**

### **🔍 Common Issues**

#### **Worker Not Starting**
```bash
# Check logs
docker-compose -f docker-compose.workers.yml logs execution-worker

# Verify database connection
docker exec execution-worker python -c "
from app.database.database import get_db
db = next(get_db())
print('Database connected successfully')"
```

#### **Tasks Not Executing**
```bash
# Check queue status
docker exec execution-worker celery -A app.celery_app inspect reserved

# Check for worker errors
docker-compose -f docker-compose.workers.yml logs -f execution-worker
```

#### **Node-RED Not Accessible**
```bash
# Check Node-RED status
docker-compose -f docker-compose.workers.yml logs node-red

# Verify nginx proxy
curl -f http://localhost:8080/health
```

---

## 🎯 **Performance Optimization**

### **🚀 Scaling Workers**
```bash
# Scale execution workers for high load
docker-compose -f docker-compose.workers.yml up -d --scale execution-worker=3

# Add dedicated discovery worker
docker-compose -f docker-compose.workers.yml up -d --scale system-worker=2
```

### **📊 Monitoring Performance**
```bash
# Worker resource usage
docker stats execution-worker system-worker system-scheduler

# Queue depth monitoring
docker exec execution-worker celery -A app.celery_app inspect stats
```

---

## 🎊 **Success! Your Distributed Architecture is Ready!**

You now have:
- ✅ **2 Specialized Workers** handling different task types
- ✅ **1 Beat Scheduler** managing all periodic tasks  
- ✅ **1 Node-RED Instance** for visual workflow design
- ✅ **Automatic Resource Management** with proper scaling
- ✅ **Health Monitoring** and task timeout handling
- ✅ **Visual Workflow Creation** with custom OpsConductor nodes

**Next Steps:**
1. 🚀 Run `./start-distributed-workers.sh`
2. 🎨 Open Node-RED at http://localhost:8080
3. 🔧 Create your first automation workflow!
4. 📊 Monitor performance and scale as needed

**Happy Automating!** 🎯