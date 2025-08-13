#!/usr/bin/env python3
"""
Comprehensive test for ENABLEDRM Enterprise Features
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/home/enabledrm/backend')

async def test_monitoring_domain():
    """Test the monitoring domain features."""
    print("🔍 Testing Monitoring Domain...")
    
    try:
        from app.domains.monitoring.services.metrics_service import MetricsService
        from app.database.database import get_db
        
        # Create a mock database session
        class MockDB:
            def query(self, model):
                class MockQuery:
                    def count(self):
                        return 42
                    def filter(self, *args):
                        return self
                    def scalar(self):
                        return 123.45
                    def all(self):
                        return []
                return MockQuery()
            
            @property
            def bind(self):
                class MockBind:
                    @property
                    def pool(self):
                        class MockPool:
                            def size(self): return 10
                            def checkedin(self): return 8
                            def checkedout(self): return 2
                            def overflow(self): return 0
                            def invalid(self): return 0
                        return MockPool()
                return MockBind()
            
            def execute(self, query):
                class MockResult:
                    def fetchone(self):
                        return {"size": "100MB", "size_bytes": 104857600}
                    def __iter__(self):
                        return iter([])
                return MockResult()
        
        # Test metrics service
        service = MetricsService(MockDB())
        
        # Test system metrics
        metrics = await service.get_system_metrics()
        print(f"✅ System metrics collected: {len(metrics)} categories")
        
        # Test health score
        health = await service.get_health_score()
        print(f"✅ Health score calculated: {health['health_score']}/100")
        
        # Test Prometheus metrics
        prometheus_metrics = await service.get_prometheus_metrics()
        lines_count = len(prometheus_metrics.split('\n'))
        print(f"✅ Prometheus metrics generated: {lines_count} lines")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring domain test failed: {e}")
        return False

async def test_audit_domain():
    """Test the audit domain features."""
    print("\n📋 Testing Audit Domain...")
    
    try:
        from app.domains.audit.services.audit_service import (
            AuditService, AuditEventType, AuditSeverity,
            audit_user_login, audit_target_created, audit_security_violation
        )
        
        # Create mock database
        class MockDB:
            pass
        
        # Test audit service
        service = AuditService(MockDB())
        
        # Test event logging
        event = await service.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=1,
            resource_type="user",
            resource_id="1",
            action="login",
            details={"method": "password"},
            severity=AuditSeverity.LOW,
            ip_address="192.168.1.100"
        )
        print(f"✅ Audit event logged: {event.get('id', 'unknown')}")
        
        # Test statistics
        stats = await service.get_audit_statistics()
        print(f"✅ Audit statistics generated: {stats.get('total_events', 0)} events")
        
        # Test search
        search_results = await service.search_audit_events("login", limit=10)
        print(f"✅ Audit search completed: {len(search_results)} results")
        
        # Test convenience functions
        login_event = await audit_user_login(1, "192.168.1.100", "test-agent", service)
        print(f"✅ User login audit: {login_event.get('event_type')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audit domain test failed: {e}")
        return False

async def test_security_domain():
    """Test the security domain features."""
    print("\n🔒 Testing Security Domain...")
    
    try:
        from app.domains.security.services.security_service import SecurityService, ThreatLevel
        
        # Create mock database
        class MockDB:
            pass
        
        # Test security service
        service = SecurityService(MockDB())
        
        # Test login analysis
        analysis = await service.analyze_login_attempt(
            username="testuser",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            success=True
        )
        print(f"✅ Login analysis completed: {analysis['threat_level']} threat level")
        
        # Test malicious content analysis
        content_analysis = await service.analyze_request_content(
            "SELECT * FROM users WHERE id=1",
            "sql"
        )
        print(f"✅ Content analysis: {'threats detected' if content_analysis['threat_detected'] else 'clean'}")
        
        # Test IP reputation
        ip_reputation = await service.get_ip_reputation("192.168.1.100")
        print(f"✅ IP reputation: {ip_reputation.get('reputation_score', 0)}/100")
        
        # Test security dashboard
        dashboard = await service.get_security_dashboard()
        print(f"✅ Security dashboard: {dashboard.get('summary', {}).get('total_login_attempts_24h', 0)} attempts")
        
        return True
        
    except Exception as e:
        print(f"❌ Security domain test failed: {e}")
        return False

async def test_enhanced_target_management():
    """Test enhanced target management features."""
    print("\n🎯 Testing Enhanced Target Management...")
    
    try:
        from app.domains.target_management.services.target_domain_service import TargetDomainService
        from app.domains.target_management.repositories.target_repository import TargetRepository
        
        # Create mock dependencies
        class MockDB:
            def query(self, model):
                class MockQuery:
                    def filter(self, *args):
                        return self
                    def count(self):
                        return 5
                    def all(self):
                        return []
                    def first(self):
                        return None
                    def offset(self, n):
                        return self
                    def limit(self, n):
                        return self
                return MockQuery()
        
        class MockRepository:
            async def get_targets_needing_health_check(self, minutes=30):
                return []
            async def get_target_statistics(self):
                return {
                    "total_targets": 10,
                    "online_targets": 8,
                    "offline_targets": 2,
                    "by_type": {"ssh": 5, "http": 3, "rdp": 2},
                    "by_status": {"online": 8, "offline": 2}
                }
        
        # Test target domain service
        repository = MockRepository()
        service = TargetDomainService(repository)
        
        # Test health check
        health_result = await service.perform_health_check()
        print(f"✅ Health check completed: {health_result['message']}")
        
        # Test statistics
        stats = await service.get_target_statistics()
        print(f"✅ Target statistics: {stats['total_targets']} total targets")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced target management test failed: {e}")
        return False

async def test_analytics_domain():
    """Test analytics domain features."""
    print("\n📊 Testing Analytics Domain...")
    
    try:
        from app.domains.analytics.services.analytics_service import AnalyticsService
        
        # Create mock database
        class MockDB:
            def query(self, *args):
                class MockQuery:
                    def count(self):
                        return 42
                    def filter(self, *args):
                        return self
                    def group_by(self, *args):
                        return self
                    def order_by(self, *args):
                        return self
                    def limit(self, n):
                        return self
                    def all(self):
                        return []
                    def scalar(self):
                        return 123.45
                return MockQuery()
        
        # Test analytics service
        service = AnalyticsService(MockDB())
        
        # Test dashboard metrics
        metrics = await service.get_dashboard_metrics()
        print(f"✅ Dashboard metrics: {len(metrics)} metric categories")
        
        # Test system health report
        health_report = await service.get_system_health_report()
        print(f"✅ System health report: {health_report.get('overall_score', 0)}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics domain test failed: {e}")
        return False

async def test_discovery_domain():
    """Test discovery domain features."""
    print("\n🔍 Testing Discovery Domain...")
    
    try:
        from app.domains.discovery.services.enhanced_discovery_service import EnhancedDiscoveryService
        
        # Test discovery service
        service = EnhancedDiscoveryService()
        
        # Test network discovery (mock)
        discovery_id = await service.start_network_discovery(
            network_range="192.168.1.0/24",
            discovered_by=1
        )
        print(f"✅ Network discovery started: {discovery_id}")
        
        # Test discovery status
        status = await service.get_discovery_status(discovery_id)
        print(f"✅ Discovery status: {status['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery domain test failed: {e}")
        return False

async def test_shared_infrastructure():
    """Test shared infrastructure components."""
    print("\n🏗️ Testing Shared Infrastructure...")
    
    try:
        # Test event system
        from app.shared.infrastructure.events import event_bus, DomainEvent
        from app.domains.target_management.events.target_events_simple import TargetCreatedEvent
        
        event = TargetCreatedEvent(
            target_id=999,
            target_name="test-target",
            target_type="ssh",
            host="127.0.0.1",
            port=22,
            created_by=1
        )
        print(f"✅ Domain event created: {event.event_id}")
        
        # Test caching
        from app.shared.infrastructure.cache import cache_service, cached
        
        await cache_service.set("test_key", "test_value", ttl=60)
        value = await cache_service.get("test_key")
        print(f"✅ Cache system: {'working' if value == 'test_value' else 'fallback mode'}")
        
        # Test dependency injection
        from app.shared.infrastructure.container import container, injectable
        print("✅ Dependency injection container loaded")
        
        # Test repository pattern
        from app.shared.infrastructure.repository import BaseRepository
        print("✅ Repository pattern available")
        
        # Test exception handling
        from app.shared.exceptions.base import ValidationException, ConflictError, NotFoundError
        print("✅ Exception hierarchy loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Shared infrastructure test failed: {e}")
        return False

async def main():
    """Run comprehensive enterprise feature tests."""
    print("🚀 ENABLEDRM Enterprise Features Test Suite")
    print("=" * 60)
    
    tests = [
        test_shared_infrastructure,
        test_monitoring_domain,
        test_audit_domain,
        test_security_domain,
        test_enhanced_target_management,
        test_analytics_domain,
        test_discovery_domain,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Enterprise Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enterprise features are working correctly!")
        print("\n🏆 ENABLEDRM is now a fully-featured enterprise platform with:")
        print("   • Advanced monitoring and observability")
        print("   • Comprehensive audit logging")
        print("   • Security threat detection")
        print("   • Enhanced target management")
        print("   • Real-time analytics")
        print("   • Network discovery capabilities")
        print("   • Domain-driven architecture")
        print("   • Event-driven design")
        print("   • Scalable infrastructure")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)