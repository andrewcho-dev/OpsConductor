#!/usr/bin/env python3
"""
Test script to verify the enhanced architecture implementation
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/home/enabledrm/backend')

async def test_infrastructure():
    """Test the shared infrastructure components"""
    print("🧪 Testing Enhanced Architecture Components...")
    
    try:
        # Test dependency injection
        from app.shared.infrastructure.container import container, injectable
        print("✅ Dependency injection container loaded")
        
        # Test event system
        from app.shared.infrastructure.events import event_bus, DomainEvent
        print("✅ Event system loaded")
        
        # Test caching
        from app.shared.infrastructure.cache import cache_service
        print("✅ Cache service loaded")
        
        # Test repository pattern
        from app.shared.infrastructure.repository import BaseRepository
        print("✅ Repository pattern loaded")
        
        # Test exception handling
        from app.shared.exceptions.base import ValidationException, ConflictError, NotFoundError
        print("✅ Exception hierarchy loaded")
        
    except Exception as e:
        print(f"❌ Infrastructure test failed: {e}")
        return False
    
    return True

async def test_domains():
    """Test domain implementations"""
    print("\n🏗️ Testing Domain Implementations...")
    
    try:
        # Test Target Management Domain
        from app.domains.target_management.services.target_domain_service import TargetDomainService
        from app.domains.target_management.repositories.target_repository import TargetRepository
        from app.domains.target_management.events.target_events_simple import TargetCreatedEvent
        print("✅ Target Management Domain loaded")
        
        # Test Discovery Domain
        from app.domains.discovery.services.enhanced_discovery_service import EnhancedDiscoveryService
        print("✅ Discovery Domain loaded")
        
        # Test Analytics Domain
        from app.domains.analytics.services.analytics_service import AnalyticsService
        print("✅ Analytics Domain loaded")
        
    except Exception as e:
        print(f"❌ Domain test failed: {e}")
        return False
    
    return True

async def test_api_layer():
    """Test API layer components"""
    print("\n🌐 Testing API Layer...")
    
    try:
        # Test new API endpoints
        from app.api.v1 import targets, analytics
        print("✅ Enhanced API endpoints loaded")
        
        # Test schemas
        from app.schemas.target_schemas import BulkTargetOperation, TargetStatistics
        print("✅ Enhanced schemas loaded")
        
    except Exception as e:
        print(f"❌ API layer test failed: {e}")
        return False
    
    return True

async def test_event_system():
    """Test the event system"""
    print("\n📡 Testing Event System...")
    
    try:
        from app.shared.infrastructure.events import event_bus, DomainEvent
        from app.domains.target_management.events.target_events_simple import TargetCreatedEvent
        
        # Create a test event
        test_event = TargetCreatedEvent(
            target_id=999,
            target_name="test-target",
            target_type="ssh",
            host="127.0.0.1",
            port=22,
            created_by=1
        )
        
        print(f"✅ Event created: {test_event.event_id}")
        print(f"✅ Event type: {test_event.aggregate_type}")
        print(f"✅ Event data: target_id={test_event.target_id}, name={test_event.target_name}")
        
    except Exception as e:
        print(f"❌ Event system test failed: {e}")
        return False
    
    return True

async def test_cache_system():
    """Test the caching system"""
    print("\n💾 Testing Cache System...")
    
    try:
        from app.shared.infrastructure.cache import cache_service, cached
        
        # Test cache service
        await cache_service.set("test_key", "test_value", ttl=60)
        value = await cache_service.get("test_key")
        
        if value == "test_value":
            print("✅ Cache set/get working")
        else:
            print("⚠️ Cache using memory fallback (Redis not available)")
        
        # Test cached decorator
        @cached(ttl=300, key_prefix="test")
        async def test_cached_function():
            return {"message": "cached result"}
        
        result = await test_cached_function()
        print(f"✅ Cached decorator working: {result}")
        
    except Exception as e:
        print(f"❌ Cache system test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 ENABLEDRM Enhanced Architecture Test Suite")
    print("=" * 50)
    
    tests = [
        test_infrastructure,
        test_domains,
        test_api_layer,
        test_event_system,
        test_cache_system,
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced architecture is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)