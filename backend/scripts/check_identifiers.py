#!/usr/bin/env python3
"""
Quick check script to see the current state of permanent identifiers
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database import get_database_url

def check_identifiers():
    """Check the current state of permanent identifiers"""
    try:
        # Create database connection
        database_url = get_database_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("🔍 CHECKING PERMANENT IDENTIFIER STATUS")
        print("=" * 50)
        
        # Check jobs
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(job_uuid) as with_uuid,
                COUNT(job_serial) as with_serial
            FROM jobs
        """))
        job_stats = result.fetchone()
        
        print(f"📊 JOBS:")
        print(f"   Total: {job_stats[0]}")
        print(f"   With UUID: {job_stats[1]}")
        print(f"   With Serial: {job_stats[2]}")
        print(f"   Missing UUID: {job_stats[0] - job_stats[1]}")
        print(f"   Missing Serial: {job_stats[0] - job_stats[2]}")
        
        # Check targets
        result = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(target_uuid) as with_uuid,
                COUNT(target_serial) as with_serial
            FROM universal_targets
        """))
        target_stats = result.fetchone()
        
        print(f"\n📊 TARGETS:")
        print(f"   Total: {target_stats[0]}")
        print(f"   With UUID: {target_stats[1]}")
        print(f"   With Serial: {target_stats[2]}")
        print(f"   Missing UUID: {target_stats[0] - target_stats[1]}")
        print(f"   Missing Serial: {target_stats[0] - target_stats[2]}")
        
        # Show samples if any exist
        if job_stats[0] > 0:
            print(f"\n📋 SAMPLE JOBS:")
            result = session.execute(text("""
                SELECT id, job_uuid, job_serial, name 
                FROM jobs 
                ORDER BY id 
                LIMIT 3
            """))
            for row in result:
                uuid_display = str(row[1])[:8] + "..." if row[1] else "None"
                print(f"   ID {row[0]}: UUID={uuid_display}, Serial={row[2] or 'None'}, Name={row[3]}")
        
        if target_stats[0] > 0:
            print(f"\n📋 SAMPLE TARGETS:")
            result = session.execute(text("""
                SELECT id, target_uuid, target_serial, name 
                FROM universal_targets 
                ORDER BY id 
                LIMIT 3
            """))
            for row in result:
                uuid_display = str(row[1])[:8] + "..." if row[1] else "None"
                print(f"   ID {row[0]}: UUID={uuid_display}, Serial={row[2] or 'None'}, Name={row[3]}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        total_missing = (job_stats[0] - job_stats[1]) + (job_stats[0] - job_stats[2]) + (target_stats[0] - target_stats[1]) + (target_stats[0] - target_stats[2])
        
        if total_missing == 0:
            print("   ✅ All records have permanent identifiers - no action needed!")
        else:
            print("   🔧 Run the population script to add missing identifiers:")
            print("   python3 scripts/populate_permanent_identifiers.py")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error checking identifiers: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    check_identifiers()