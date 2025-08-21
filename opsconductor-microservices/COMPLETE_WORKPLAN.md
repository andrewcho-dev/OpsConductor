# OpsConductor Microservices - Complete Development Workplan

## 🎯 **Project Overview**

Transform the existing OpsConductor platform from a monolithic architecture to a complete microservices architecture while preserving all existing functionality and integrating with already-built services.

### **Current State Analysis**
- ✅ **Auth Service**: Complete & Working (Port 3000)
- ✅ **User Service**: Complete & Working (Port 3002)  
- ✅ **Frontend**: Complete & Working (React + Material-UI)
- 🔄 **Legacy Backend**: Contains targets & job functionality (to be extracted)

### **Target State**
- 8 independent microservices
- Event-driven architecture with RabbitMQ
- Independent databases per service
- API Gateway for unified access
- Complete preservation of existing functionality

---

## 📋 **Complete Service Architecture**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Auth Service  │  │  User Service   │  │ Universal Targets│  │ Job Management  │
│   ✅ EXISTING   │  │   ✅ EXISTING   │  │  🔄 EXTRACT     │  │  🔄 CREATE     │
│   Port: 3000    │  │   Port: 3002    │  │   Port: 3001    │  │   Port: 8001    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Job Execution   │  │ Job Scheduling  │  │ Audit & Events  │  │   Frontend      │
│  🔄 CREATE     │  │  🔄 CREATE     │  │  🔄 CREATE     │  │   ✅ EXISTING   │
│   Port: 8002    │  │   Port: 8003    │  │   Port: 8004    │  │   Port: 3000    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 🗓️ **8-Week Development Timeline**

### **Week 1: Infrastructure & Shared Libraries**
**Goal**: Set up foundation for microservices architecture

#### **Phase 1.1: Update Shared Libraries** (Days 1-2)
- ✅ **DONE**: Basic shared models and event system
- 🔄 **TODO**: Add authentication integration with existing auth service
  - Update `opsconductor_shared/auth/jwt_auth.py`
  - Add `AuthServiceClient` for token validation
  - Create FastAPI dependencies for auth
- 🔄 **TODO**: Add user service client integration
  - Create `UserServiceClient` for user operations
  - Add permission and role checking
  - Add user activity tracking
- 🔄 **TODO**: Add targets service client (for future use)
  - Create `TargetsServiceClient` for target operations
  - Add connection testing capabilities
  - Add target validation methods

#### **Phase 1.2: Update Docker Compose** (Days 3-4)
- 🔄 **TODO**: Integrate existing services
  - Add auth-service, user-service, frontend to compose
  - Configure proper networking between services
  - Set up environment variables
- 🔄 **TODO**: Add new service databases
  - Configure 5 new PostgreSQL instances
  - Set up proper port allocation (5432-5438)
  - Create database initialization scripts
- 🔄 **TODO**: Configure service discovery
  - Set up service-to-service communication
  - Configure health checks for all services
  - Add dependency management

#### **Phase 1.3: Message Broker Setup** (Days 5-7)
- 🔄 **TODO**: Configure RabbitMQ for all services
  - Set up exchanges and queues
  - Configure event routing patterns
  - Add management UI access
- 🔄 **TODO**: Set up event routing between existing and new services
  - Create event schemas for cross-service communication
  - Set up pub/sub patterns
  - Add event persistence and reliability
- 🔄 **TODO**: Create event schemas for cross-service communication
  - Define event types for all services
  - Create event validation schemas
  - Add correlation ID tracking

**Week 1 Deliverables**:
- ✅ Updated shared libraries with auth/user integration
- ✅ Complete docker-compose.yml with all services
- ✅ RabbitMQ setup with event routing
- ✅ Database infrastructure for all services

---

### **Week 2: Extract Universal Targets Service**
**Goal**: Extract targets functionality from legacy backend into independent service

#### **Phase 2.1: Create Targets Microservice** (Days 8-10)
- 🔄 **TODO**: Extract target models from backend
  - Copy `/home/enabledrm/backend/app/models/universal_target_models.py`
  - Update models for independent database
  - Add proper indexes and constraints
- 🔄 **TODO**: Create independent targets database
  - Design database schema for targets service
  - Create migration scripts from legacy data
  - Set up database initialization
- 🔄 **TODO**: Migrate target API endpoints
  - Extract `/home/enabledrm/backend/app/api/v3/targets.py`
  - Update endpoints for microservice architecture
  - Add proper error handling and validation
- 🔄 **TODO**: Implement target health checks
  - Add connection testing functionality
  - Implement health monitoring
  - Add status tracking and reporting

#### **Phase 2.2: Data Migration** (Days 11-12)
- 🔄 **TODO**: Create migration scripts for target data
  - Export data from legacy backend database
  - Transform data for new schema
  - Import data into targets service database
- 🔄 **TODO**: Update frontend to use new targets service
  - Update `/home/enabledrm/frontend/src/services/targetService.js`
  - Update API endpoints in frontend
  - Test all target-related UI functionality
- 🔄 **TODO**: Update auth integration
  - Integrate with existing auth service
  - Add proper JWT validation
  - Test authentication flows

#### **Phase 2.3: Integration Testing** (Days 13-14)
- 🔄 **TODO**: Test with existing auth service
  - Verify JWT token validation
  - Test permission checking
  - Validate user context passing
- 🔄 **TODO**: Test with existing user service
  - Test user permission validation
  - Verify user activity tracking
  - Test role-based access control
- 🔄 **TODO**: Test frontend integration
  - Test all target CRUD operations
  - Verify connection testing functionality
  - Test error handling and user feedback
- 🔄 **TODO**: Verify connection testing functionality
  - Test SSH connections
  - Test WinRM connections
  - Verify credential management

**Week 2 Deliverables**:
- ✅ Universal Targets Service (Port 3001)
- ✅ Independent targets database
- ✅ Data migration from legacy backend
- ✅ Frontend integration complete
- ✅ Full integration with auth/user services

---

### **Week 3: Create Job Management Service**
**Goal**: Create job definition and lifecycle management service

#### **Phase 3.1: Job Management Service** (Days 15-17)
- ✅ **DONE**: Basic service structure
- 🔄 **TODO**: Integrate with existing auth service
  - Add JWT authentication middleware
  - Implement user context extraction
  - Add permission-based access control
- 🔄 **TODO**: Integrate with targets service
  - Add targets service client
  - Implement target validation for jobs
  - Add target health checking
- 🔄 **TODO**: Integrate with user service
  - Add user service client
  - Implement user permission checking
  - Add user activity tracking
- 🔄 **TODO**: Extract job models from backend
  - Copy job-related models from legacy backend
  - Update for independent database
  - Add proper relationships and constraints

#### **Phase 3.2: Job Lifecycle Management** (Days 18-19)
- 🔄 **TODO**: Job CRUD operations
  - Implement job creation with validation
  - Add job update and deletion
  - Implement job listing with filtering
- 🔄 **TODO**: Job validation with targets service
  - Validate target availability
  - Check target compatibility
  - Verify connection methods
- 🔄 **TODO**: Job permissions with user service
  - Implement role-based job access
  - Add job ownership validation
  - Implement permission inheritance
- 🔄 **TODO**: Job audit events
  - Add event publishing for job operations
  - Implement audit trail logging
  - Add change tracking

#### **Phase 3.3: Frontend Integration** (Days 20-21)
- 🔄 **TODO**: Update frontend job service calls
  - Update API endpoints to use job management service
  - Update authentication headers
  - Add error handling for service communication
- 🔄 **TODO**: Update job creation workflows
  - Update job creation forms
  - Add target validation in UI
  - Update job configuration options
- 🔄 **TODO**: Update job management UI
  - Update job listing and filtering
  - Update job details and editing
  - Add job status tracking
- 🔄 **TODO**: Test job operations end-to-end
  - Test complete job creation workflow
  - Test job editing and deletion
  - Verify all UI functionality

**Week 3 Deliverables**:
- ✅ Job Management Service (Port 8001)
- ✅ Complete job CRUD operations
- ✅ Integration with auth, user, and targets services
- ✅ Frontend integration complete
- ✅ Job validation and permission system

---

### **Week 4: Create Job Execution Service**
**Goal**: Create job execution engine with connection management

#### **Phase 4.1: Execution Engine** (Days 22-24)
- ✅ **DONE**: Basic execution service structure
- 🔄 **TODO**: Integrate with job management service
  - Add job management service client
  - Implement job retrieval for execution
  - Add job status updates
- 🔄 **TODO**: Integrate with targets service for connections
  - Add targets service client
  - Implement connection credential retrieval
  - Add connection method selection
- 🔄 **TODO**: Extract execution logic from backend
  - Copy execution logic from legacy backend
  - Update for microservice architecture
  - Add proper error handling
- 🔄 **TODO**: Implement Celery workers
  - Set up Celery configuration
  - Create execution tasks
  - Add task monitoring and management

#### **Phase 4.2: Connection Management** (Days 25-26)
- 🔄 **TODO**: SSH connection handling
  - Implement SSH connection pooling
  - Add SSH command execution
  - Add file transfer capabilities
- 🔄 **TODO**: WinRM connection handling
  - Implement WinRM connection management
  - Add PowerShell command execution
  - Add Windows file operations
- 🔄 **TODO**: Connection pooling
  - Implement connection reuse
  - Add connection timeout handling
  - Add connection health monitoring
- 🔄 **TODO**: Safety checks and validation
  - Implement dangerous command detection
  - Add command validation
  - Add execution sandboxing

#### **Phase 4.3: Execution Monitoring** (Days 27-28)
- 🔄 **TODO**: Real-time execution tracking
  - Implement execution status updates
  - Add progress tracking
  - Add real-time notifications
- 🔄 **TODO**: Result aggregation
  - Implement result collection
  - Add result formatting
  - Add result storage and retrieval
- 🔄 **TODO**: Error handling and retries
  - Implement retry logic
  - Add error classification
  - Add failure recovery
- 🔄 **TODO**: Integration with audit service
  - Add execution event publishing
  - Implement audit trail logging
  - Add performance metrics

**Week 4 Deliverables**:
- ✅ Job Execution Service (Port 8002)
- ✅ Celery workers for async execution
- ✅ SSH/WinRM connection management
- ✅ Real-time execution tracking
- ✅ Integration with job management and targets services

---

### **Week 5: Create Job Scheduling Service**
**Goal**: Create time-based job scheduling and triggering

#### **Phase 5.1: Scheduling Engine** (Days 29-31)
- 🔄 **TODO**: Cron expression parsing
  - Implement cron expression validation
  - Add next execution calculation
  - Add timezone support
- 🔄 **TODO**: Recurring job management
  - Implement recurring schedule types
  - Add schedule lifecycle management
  - Add schedule history tracking
- 🔄 **TODO**: Schedule lifecycle management
  - Implement schedule creation and updates
  - Add schedule activation/deactivation
  - Add schedule deletion and cleanup
- 🔄 **TODO**: Timezone support
  - Add timezone-aware scheduling
  - Implement timezone conversion
  - Add daylight saving time handling

#### **Phase 5.2: Job Triggering** (Days 32-33)
- 🔄 **TODO**: Integration with job management service
  - Add job management service client
  - Implement job retrieval for scheduling
  - Add job validation before execution
- 🔄 **TODO**: Integration with job execution service
  - Add job execution service client
  - Implement job execution triggering
  - Add execution status monitoring
- 🔄 **TODO**: Schedule monitoring and alerting
  - Implement schedule health monitoring
  - Add missed execution detection
  - Add schedule failure alerting
- 🔄 **TODO**: Schedule history tracking
  - Implement execution history logging
  - Add schedule performance metrics
  - Add schedule success/failure tracking

#### **Phase 5.3: Frontend Integration** (Days 34-35)
- 🔄 **TODO**: Update frontend scheduling UI
  - Add schedule creation forms
  - Update schedule management interface
  - Add schedule monitoring dashboard
- 🔄 **TODO**: Add schedule visualization
  - Add schedule calendar view
  - Implement execution timeline
  - Add schedule conflict detection
- 🔄 **TODO**: Test scheduling workflows
  - Test schedule creation and editing
  - Test job execution triggering
  - Verify schedule monitoring

**Week 5 Deliverables**:
- ✅ Job Scheduling Service (Port 8003)
- ✅ Cron and recurring schedule support
- ✅ Integration with job management and execution services
- ✅ Frontend scheduling interface
- ✅ Schedule monitoring and alerting

---

### **Week 6: Create Audit & Events Service**
**Goal**: Create centralized event logging and audit system

#### **Phase 6.1: Event Collection** (Days 36-38)
- 🔄 **TODO**: Centralized event logging
  - Implement event collection from all services
  - Add event validation and processing
  - Add event storage and indexing
- 🔄 **TODO**: Event aggregation from all services
  - Set up event subscribers for all services
  - Implement event correlation
  - Add event deduplication
- 🔄 **TODO**: Event filtering and querying
  - Implement event search and filtering
  - Add event aggregation queries
  - Add event export capabilities
- 🔄 **TODO**: Event retention policies
  - Implement event archiving
  - Add retention policy management
  - Add event cleanup processes

#### **Phase 6.2: Audit Trails** (Days 39-40)
- 🔄 **TODO**: User action auditing
  - Implement user activity tracking
  - Add action correlation with users
  - Add user behavior analysis
- 🔄 **TODO**: System event auditing
  - Implement system event tracking
  - Add system health monitoring
  - Add performance event tracking
- 🔄 **TODO**: Compliance reporting
  - Implement compliance report generation
  - Add audit trail export
  - Add compliance dashboard
- 🔄 **TODO**: Audit data export
  - Implement audit data export
  - Add multiple export formats
  - Add scheduled audit reports

#### **Phase 6.3: Monitoring & Metrics** (Days 41-42)
- 🔄 **TODO**: System health monitoring
  - Implement service health tracking
  - Add system performance monitoring
  - Add resource usage tracking
- 🔄 **TODO**: Performance metrics collection
  - Implement performance metric collection
  - Add metric aggregation and analysis
  - Add performance alerting
- 🔄 **TODO**: Alert generation
  - Implement alert rule engine
  - Add alert notification system
  - Add alert escalation
- 🔄 **TODO**: Dashboard integration
  - Create monitoring dashboard
  - Add real-time metrics display
  - Add historical trend analysis

**Week 6 Deliverables**:
- ✅ Audit & Events Service (Port 8004)
- ✅ Centralized event collection from all services
- ✅ Comprehensive audit trail system
- ✅ System monitoring and alerting
- ✅ Compliance reporting capabilities

---

### **Week 7: API Gateway & Integration**
**Goal**: Set up unified API access and service integration

#### **Phase 7.1: API Gateway Setup** (Days 43-45)
- 🔄 **TODO**: Configure Nginx for all services
  - Set up reverse proxy configuration
  - Add service routing rules
  - Configure upstream health checks
- 🔄 **TODO**: Set up SSL termination
  - Configure SSL certificates
  - Add HTTPS redirection
  - Set up security headers
- 🔄 **TODO**: Configure load balancing
  - Set up load balancing for scalable services
  - Add health-based routing
  - Configure session affinity
- 🔄 **TODO**: Set up rate limiting
  - Implement API rate limiting
  - Add per-user rate limits
  - Add burst handling

#### **Phase 7.2: Service Discovery** (Days 46-47)
- 🔄 **TODO**: Health check endpoints
  - Implement comprehensive health checks
  - Add dependency health checking
  - Add health check aggregation
- 🔄 **TODO**: Service registration
  - Implement service discovery
  - Add automatic service registration
  - Add service metadata management
- 🔄 **TODO**: Circuit breaker patterns
  - Implement circuit breakers
  - Add failure detection
  - Add automatic recovery
- 🔄 **TODO**: Retry logic
  - Implement intelligent retry logic
  - Add exponential backoff
  - Add retry circuit breaking

#### **Phase 7.3: Security Integration** (Days 48-49)
- 🔄 **TODO**: JWT validation across all services
  - Implement centralized JWT validation
  - Add token refresh handling
  - Add token blacklisting
- 🔄 **TODO**: Service-to-service authentication
  - Implement service authentication
  - Add service authorization
  - Add service identity management
- 🔄 **TODO**: CORS configuration
  - Configure CORS for all services
  - Add origin validation
  - Add preflight handling
- 🔄 **TODO**: Security headers
  - Add security headers
  - Implement CSP policies
  - Add XSS protection

**Week 7 Deliverables**:
- ✅ API Gateway with SSL termination
- ✅ Load balancing and rate limiting
- ✅ Service discovery and health monitoring
- ✅ Circuit breakers and retry logic
- ✅ Comprehensive security implementation

---

### **Week 8: Migration & Testing**
**Goal**: Complete migration and comprehensive testing

#### **Phase 8.1: Data Migration** (Days 50-52)
- 🔄 **TODO**: Migrate job data from legacy backend
  - Export job definitions and history
  - Transform data for new schema
  - Import data into job management service
- 🔄 **TODO**: Migrate execution history
  - Export execution logs and results
  - Transform execution data
  - Import into job execution service
- 🔄 **TODO**: Migrate schedule data
  - Export schedule definitions
  - Transform schedule data
  - Import into job scheduling service
- 🔄 **TODO**: Verify data integrity
  - Validate all migrated data
  - Check data relationships
  - Verify data completeness

#### **Phase 8.2: Integration Testing** (Days 53-54)
- 🔄 **TODO**: End-to-end workflow testing
  - Test complete job creation to execution workflow
  - Test scheduling and execution workflows
  - Test user management workflows
- 🔄 **TODO**: Performance testing
  - Load test all services
  - Test concurrent operations
  - Validate performance requirements
- 🔄 **TODO**: Load testing
  - Test system under high load
  - Test service scaling
  - Validate resource usage
- 🔄 **TODO**: Security testing
  - Test authentication and authorization
  - Test service-to-service security
  - Validate security headers and policies

#### **Phase 8.3: Frontend Updates** (Days 55-56)
- 🔄 **TODO**: Update all API calls to use new services
  - Update all service endpoints
  - Add proper error handling
  - Test all API integrations
- 🔄 **TODO**: Update authentication flows
  - Update login/logout flows
  - Add token refresh handling
  - Test authentication edge cases
- 🔄 **TODO**: Update error handling
  - Add service-specific error handling
  - Implement user-friendly error messages
  - Add error recovery mechanisms
- 🔄 **TODO**: Update real-time features
  - Update WebSocket connections
  - Add real-time status updates
  - Test real-time functionality

**Week 8 Deliverables**:
- ✅ Complete data migration from legacy backend
- ✅ Comprehensive integration testing
- ✅ Performance and load testing complete
- ✅ Frontend fully updated for microservices
- ✅ Production-ready microservices architecture

---

## 🔧 **Service Integration Dependencies**

### **Service Dependency Matrix**
| Service | Dependencies | Integration Points |
|---------|-------------|-------------------|
| **Auth Service** | None | JWT token validation for all services |
| **User Service** | Auth Service | User management for all services |
| **Universal Targets** | Auth, User | Target management for job services |
| **Job Management** | Auth, User, Targets | Job definitions for execution/scheduling |
| **Job Execution** | Auth, User, Targets, Job Mgmt | Execution engine for all job operations |
| **Job Scheduling** | Auth, User, Job Mgmt, Job Exec | Scheduling for automated job execution |
| **Audit & Events** | All Services | Event collection from all services |
| **Frontend** | All Services | UI for all service operations |

### **Critical Integration Points**
1. **Authentication Flow**: Auth Service → All Services
2. **User Context**: User Service → All Services  
3. **Target Validation**: Targets Service → Job Management/Execution
4. **Job Execution**: Job Management → Job Execution
5. **Scheduled Execution**: Job Scheduling → Job Execution
6. **Event Collection**: All Services → Audit & Events
7. **UI Operations**: Frontend → All Services

---

## 📊 **Success Metrics**

### **Technical Metrics**
- ✅ All 8 services independently deployable
- ✅ Zero shared databases between services
- ✅ Event-driven communication implemented
- ✅ <100ms average response time maintained
- ✅ 99.9% uptime for all services
- ✅ Horizontal scaling capability demonstrated

### **Business Metrics**
- ✅ Zero downtime migration achieved
- ✅ All existing features preserved
- ✅ User experience maintained or improved
- ✅ System performance maintained or improved
- ✅ Enhanced monitoring and observability

### **Quality Metrics**
- ✅ 90%+ test coverage for all services
- ✅ All security requirements met
- ✅ Complete audit trail implementation
- ✅ Comprehensive error handling
- ✅ Full documentation coverage

---

## 🚀 **Immediate Next Steps**

### **Priority 1: Start Week 1 - Infrastructure Setup**
```bash
cd /home/enabledrm/opsconductor-microservices

# 1. Update shared libraries with auth integration
cd shared-libs
# Add auth service client
# Add user service client
# Update event schemas

# 2. Test shared library integration
pip install -e .
python -c "from opsconductor_shared.auth.jwt_auth import get_current_user; print('Auth integration ready')"

# 3. Update docker-compose.yml
cp docker-compose.updated.yml docker-compose.yml
# Review and adjust service configurations
# Test infrastructure startup
```

### **Priority 2: Begin Week 2 - Extract Targets Service**
```bash
# 1. Create universal-targets-service directory
mkdir -p universal-targets-service/{app/{api,models,services,core},database,tests}

# 2. Extract target models from legacy backend
cp /home/enabledrm/backend/app/models/universal_target_models.py universal-targets-service/app/models/
cp /home/enabledrm/backend/app/api/v3/targets.py universal-targets-service/app/api/

# 3. Create service structure
# Follow the pattern from job-management-service
```

### **Priority 3: Set up Development Environment**
```bash
# 1. Install dependencies
pip install -r shared-libs/requirements.txt

# 2. Start infrastructure services
docker-compose up -d redis rabbitmq auth-postgres user-postgres

# 3. Start existing services
docker-compose up -d auth-service user-service

# 4. Verify service health
curl http://localhost:3000/health  # Auth service
curl http://localhost:3002/health  # User service
```

---

## 📝 **Development Standards**

### **Code Standards**
- Follow existing code patterns from auth/user services
- Use shared libraries for common functionality
- Implement comprehensive error handling
- Add proper logging and monitoring
- Follow REST API conventions

### **Testing Standards**
- Unit tests for all business logic
- Integration tests for service communication
- End-to-end tests for complete workflows
- Performance tests for scalability
- Security tests for all endpoints

### **Documentation Standards**
- API documentation for all endpoints
- Service integration documentation
- Deployment and configuration guides
- Troubleshooting and monitoring guides
- Architecture decision records

---

This workplan provides a comprehensive, week-by-week roadmap for transforming OpsConductor into a complete microservices architecture while preserving all existing functionality and properly integrating with the already-built Auth Service, User Service, and Frontend.

**Ready to begin Week 1: Infrastructure & Shared Libraries setup?**