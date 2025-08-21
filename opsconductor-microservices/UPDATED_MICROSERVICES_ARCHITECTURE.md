# OpsConductor Complete Microservices Architecture

## 🏗️ **Updated Architecture Overview**

Based on the existing services, here's the complete microservice architecture plan:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Auth Service  │  │  User Service   │  │ Universal Targets│  │ Job Management  │
│   (EXISTING)    │  │   (EXISTING)    │  │    Service      │  │    Service      │
│   Port: 3000    │  │   Port: 3002    │  │   Port: 3001    │  │   Port: 8001    │
│                 │  │                 │  │                 │  │                 │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │   Auth DB   │ │  │ │   User DB   │ │  │ │ Targets DB  │ │  │ │   Jobs DB   │ │
│ │ Port: 5433  │ │  │ │ Port: 5434  │ │  │ │ Port: 5435  │ │  │ │ Port: 5432  │ │
│ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │                     │
         └─────────────────────┼─────────────────────┼─────────────────────┘
                               │                     │
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Job Execution   │  │ Job Scheduling  │  │ Audit & Events  │  │   Frontend      │
│    Service      │  │    Service      │  │    Service      │  │   (EXISTING)    │
│   Port: 8002    │  │   Port: 8003    │  │   Port: 8004    │  │   Port: 3000    │
│                 │  │                 │  │                 │  │                 │
│ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
│ │Executions DB│ │  │ │Schedules DB │ │  │ │  Events DB  │ │  │ │   Static    │ │
│ │ Port: 5436  │ │  │ │ Port: 5437  │ │  │ │ Port: 5438  │ │  │ │   Files     │ │
│ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │                     │
         └─────────────────────┼─────────────────────┼─────────────────────┘
                               │                     │
                    ┌─────────────────┐    ┌─────────────────┐
                    │  API Gateway    │    │ Message Broker  │
                    │   (Nginx)       │    │   RabbitMQ      │
                    │   Port: 80/443  │    │   Port: 5672    │
                    └─────────────────┘    └─────────────────┘
                               │
                    ┌─────────────────┐
                    │     Redis       │
                    │   Port: 6379    │
                    └─────────────────┘
```

---

## 📋 **Complete Service Inventory**

### **✅ EXISTING SERVICES (Already Built & Working)**

#### 1. **Auth Service** (Port 3000)
- **Status**: ✅ **COMPLETE & WORKING**
- **Database**: `auth_db` (Port 5433)
- **Responsibility**: JWT authentication, token management
- **Location**: `/home/enabledrm/auth-service/`

#### 2. **User Service** (Port 3002)  
- **Status**: ✅ **COMPLETE & WORKING**
- **Database**: `user_db` (Port 5434)
- **Responsibility**: User management, profiles, permissions
- **Location**: `/home/enabledrm/user-service/`

#### 3. **Frontend Application** (Port 3000)
- **Status**: ✅ **COMPLETE & WORKING**
- **Technology**: React + Material-UI
- **Responsibility**: User interface, dashboard, job management UI
- **Location**: `/home/enabledrm/frontend/`

#### 4. **Legacy Backend** (Port 8000)
- **Status**: ✅ **WORKING** (Contains targets functionality)
- **Database**: `opsconductor` (Port 5432)
- **Contains**: Universal Targets API, Job execution logic
- **Location**: `/home/enabledrm/backend/`

---

### **🔄 SERVICES TO EXTRACT/CREATE**

#### 5. **Universal Targets Service** (Port 3001)
- **Status**: 🔄 **TO BE EXTRACTED** from legacy backend
- **Database**: `targets_db` (Port 5435)
- **Responsibility**: Target management, connection methods, health checks
- **Source**: Extract from `/home/enabledrm/backend/app/api/v3/targets.py`

#### 6. **Job Management Service** (Port 8001)
- **Status**: 🔄 **TO BE CREATED** 
- **Database**: `job_management` (Port 5432)
- **Responsibility**: Job definitions, lifecycle, validation
- **Source**: Extract from legacy backend

#### 7. **Job Execution Service** (Port 8002)
- **Status**: 🔄 **TO BE CREATED**
- **Database**: `job_execution` (Port 5436)
- **Responsibility**: Job execution engine, SSH/WinRM connections
- **Source**: Extract from legacy backend

#### 8. **Job Scheduling Service** (Port 8003)
- **Status**: 🔄 **TO BE CREATED**
- **Database**: `job_scheduling` (Port 5437)
- **Responsibility**: Cron scheduling, recurring jobs
- **Source**: Extract from legacy backend

#### 9. **Audit & Events Service** (Port 8004)
- **Status**: 🔄 **TO BE CREATED**
- **Database**: `audit_events` (Port 5438)
- **Responsibility**: Event logging, audit trails, monitoring
- **Source**: Extract from legacy backend

---

## 🎯 **Complete Development Workplan**

### **Phase 1: Infrastructure & Shared Libraries** (Week 1)

#### **1.1 Update Shared Libraries**
- ✅ **DONE**: Basic shared models and event system
- 🔄 **TODO**: Add authentication integration with existing auth service
- 🔄 **TODO**: Add user service client integration
- 🔄 **TODO**: Update event schemas for existing services

#### **1.2 Update Docker Compose**
- 🔄 **TODO**: Integrate existing services (auth, user, frontend)
- 🔄 **TODO**: Add new service databases
- 🔄 **TODO**: Configure service discovery
- 🔄 **TODO**: Update nginx configuration

#### **1.3 Message Broker Setup**
- 🔄 **TODO**: Configure RabbitMQ for all services
- 🔄 **TODO**: Set up event routing between existing and new services
- 🔄 **TODO**: Create event schemas for cross-service communication

---

### **Phase 2: Extract Universal Targets Service** (Week 2)

#### **2.1 Create Targets Microservice**
- 🔄 **TODO**: Extract target models from backend
- 🔄 **TODO**: Create independent targets database
- 🔄 **TODO**: Migrate target API endpoints
- 🔄 **TODO**: Implement target health checks
- 🔄 **TODO**: Add connection method management

#### **2.2 Data Migration**
- 🔄 **TODO**: Create migration scripts for target data
- 🔄 **TODO**: Update frontend to use new targets service
- 🔄 **TODO**: Update auth integration
- 🔄 **TODO**: Test target CRUD operations

#### **2.3 Integration Testing**
- 🔄 **TODO**: Test with existing auth service
- 🔄 **TODO**: Test with existing user service
- 🔄 **TODO**: Test frontend integration
- 🔄 **TODO**: Verify connection testing functionality

---

### **Phase 3: Create Job Management Service** (Week 3)

#### **3.1 Job Management Service**
- ✅ **DONE**: Basic service structure
- 🔄 **TODO**: Integrate with existing auth service
- 🔄 **TODO**: Integrate with targets service
- 🔄 **TODO**: Integrate with user service
- 🔄 **TODO**: Extract job models from backend

#### **3.2 Job Lifecycle Management**
- 🔄 **TODO**: Job CRUD operations
- 🔄 **TODO**: Job validation with targets service
- 🔄 **TODO**: Job permissions with user service
- 🔄 **TODO**: Job audit events

#### **3.3 Frontend Integration**
- 🔄 **TODO**: Update frontend job service calls
- 🔄 **TODO**: Update job creation workflows
- 🔄 **TODO**: Update job management UI
- 🔄 **TODO**: Test job operations end-to-end

---

### **Phase 4: Create Job Execution Service** (Week 4)

#### **4.1 Execution Engine**
- ✅ **DONE**: Basic execution service structure
- 🔄 **TODO**: Integrate with job management service
- 🔄 **TODO**: Integrate with targets service for connections
- 🔄 **TODO**: Extract execution logic from backend
- 🔄 **TODO**: Implement Celery workers

#### **4.2 Connection Management**
- 🔄 **TODO**: SSH connection handling
- 🔄 **TODO**: WinRM connection handling
- 🔄 **TODO**: Connection pooling
- 🔄 **TODO**: Safety checks and validation

#### **4.3 Execution Monitoring**
- 🔄 **TODO**: Real-time execution tracking
- 🔄 **TODO**: Result aggregation
- 🔄 **TODO**: Error handling and retries
- 🔄 **TODO**: Integration with audit service

---

### **Phase 5: Create Job Scheduling Service** (Week 5)

#### **5.1 Scheduling Engine**
- 🔄 **TODO**: Cron expression parsing
- 🔄 **TODO**: Recurring job management
- 🔄 **TODO**: Schedule lifecycle management
- 🔄 **TODO**: Timezone support

#### **5.2 Job Triggering**
- 🔄 **TODO**: Integration with job management service
- 🔄 **TODO**: Integration with job execution service
- 🔄 **TODO**: Schedule monitoring and alerting
- 🔄 **TODO**: Schedule history tracking

---

### **Phase 6: Create Audit & Events Service** (Week 6)

#### **6.1 Event Collection**
- 🔄 **TODO**: Centralized event logging
- 🔄 **TODO**: Event aggregation from all services
- 🔄 **TODO**: Event filtering and querying
- 🔄 **TODO**: Event retention policies

#### **6.2 Audit Trails**
- 🔄 **TODO**: User action auditing
- 🔄 **TODO**: System event auditing
- 🔄 **TODO**: Compliance reporting
- 🔄 **TODO**: Audit data export

#### **6.3 Monitoring & Metrics**
- 🔄 **TODO**: System health monitoring
- 🔄 **TODO**: Performance metrics collection
- 🔄 **TODO**: Alert generation
- 🔄 **TODO**: Dashboard integration

---

### **Phase 7: API Gateway & Integration** (Week 7)

#### **7.1 API Gateway Setup**
- 🔄 **TODO**: Configure Nginx for all services
- 🔄 **TODO**: Set up SSL termination
- 🔄 **TODO**: Configure load balancing
- 🔄 **TODO**: Set up rate limiting

#### **7.2 Service Discovery**
- 🔄 **TODO**: Health check endpoints
- 🔄 **TODO**: Service registration
- 🔄 **TODO**: Circuit breaker patterns
- 🔄 **TODO**: Retry logic

#### **7.3 Security Integration**
- 🔄 **TODO**: JWT validation across all services
- 🔄 **TODO**: Service-to-service authentication
- 🔄 **TODO**: CORS configuration
- 🔄 **TODO**: Security headers

---

### **Phase 8: Migration & Testing** (Week 8)

#### **8.1 Data Migration**
- 🔄 **TODO**: Migrate job data from legacy backend
- 🔄 **TODO**: Migrate execution history
- 🔄 **TODO**: Migrate schedule data
- 🔄 **TODO**: Verify data integrity

#### **8.2 Integration Testing**
- 🔄 **TODO**: End-to-end workflow testing
- 🔄 **TODO**: Performance testing
- 🔄 **TODO**: Load testing
- 🔄 **TODO**: Security testing

#### **8.3 Frontend Updates**
- 🔄 **TODO**: Update all API calls to use new services
- 🔄 **TODO**: Update authentication flows
- 🔄 **TODO**: Update error handling
- 🔄 **TODO**: Update real-time features

---

## 🔧 **Service Integration Matrix**

| Service | Auth | User | Targets | Jobs | Execution | Scheduling | Audit | Frontend |
|---------|------|------|---------|------|-----------|------------|-------|----------|
| **Auth** | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **User** | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Targets** | ✅ | ✅ | - | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Jobs** | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ |
| **Execution** | ✅ | ✅ | ✅ | ✅ | - | ❌ | ✅ | ✅ |
| **Scheduling** | ✅ | ✅ | ❌ | ✅ | ✅ | - | ✅ | ✅ |
| **Audit** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| **Frontend** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |

**Legend**: ✅ = Direct Integration Required, ❌ = No Direct Integration

---

## 🚀 **Immediate Next Steps**

### **Priority 1: Update Shared Libraries**
```bash
cd /home/enabledrm/opsconductor-microservices/shared-libs
# Add auth service integration
# Add user service integration  
# Update event schemas
```

### **Priority 2: Extract Universal Targets Service**
```bash
cd /home/enabledrm/opsconductor-microservices
# Create universal-targets-service
# Extract from /home/enabledrm/backend/app/api/v3/targets.py
# Create independent database
# Update docker-compose.yml
```

### **Priority 3: Update Docker Compose**
```bash
cd /home/enabledrm/opsconductor-microservices
# Integrate existing services
# Add new service definitions
# Configure service discovery
# Update nginx configuration
```

---

## 📊 **Database Port Allocation**

| Service | Database | Port | Status |
|---------|----------|------|--------|
| Auth Service | `auth_db` | 5433 | ✅ Existing |
| User Service | `user_db` | 5434 | ✅ Existing |
| Universal Targets | `targets_db` | 5435 | 🔄 To Create |
| Job Management | `job_management` | 5432 | 🔄 To Create |
| Job Execution | `job_execution` | 5436 | 🔄 To Create |
| Job Scheduling | `job_scheduling` | 5437 | 🔄 To Create |
| Audit & Events | `audit_events` | 5438 | 🔄 To Create |

---

## 🎯 **Success Criteria**

### **Technical Goals**
- ✅ All services independently deployable
- ✅ No shared databases between services
- ✅ Event-driven communication implemented
- ✅ Existing functionality preserved
- ✅ Performance maintained or improved

### **Business Goals**
- ✅ Zero downtime migration
- ✅ All existing features working
- ✅ Improved scalability
- ✅ Better fault isolation
- ✅ Enhanced monitoring capabilities

---

This updated plan properly accounts for the existing Auth Service, User Service, and Frontend, while creating a logical progression to extract the Universal Targets service and build the remaining job-related microservices. The plan maintains backward compatibility and ensures a smooth migration path.

**Ready to proceed with Phase 1: Infrastructure & Shared Libraries updates?**