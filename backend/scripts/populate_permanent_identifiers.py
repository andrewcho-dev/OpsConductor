#!/usr/bin/env python3
"""
Populate Permanent Identifiers for Existing Records
This script populates UUID and serial number fields for existing jobs and targets
that were created before the permanent identifier system was implemented.
"""

import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database.database import get_database_url
from app.models.job_models import Job
from app.models.universal_target_models import UniversalTarget
from app.services.serial_service import SerialService

def populate_job_identifiers(session):
    """Populate UUID and serial numbers for existing jobs"""
    print("🔄 Populating job identifiers...")
    
    # Get all jobs that don't have UUIDs or serials
    jobs_without_uuid = session.query(Job).filter(
        (Job.job_uuid == None) | (Job.job_serial == None)
    ).order_by(Job.id).all()
    
    if not jobs_without_uuid:
        print("✅ All jobs already have permanent identifiers")
        return
    
    print(f"📊 Found {len(jobs_without_uuid)} jobs needing identifiers")
    
    # Get the current year for serial generation
    current_year = datetime.now().year
    
    # Find the highest existing serial number for this year
    result = session.execute(text("""
        SELECT COALESCE(MAX(CAST(SUBSTRING(job_serial FROM 10) AS INTEGER)), 0) as max_num
        FROM jobs 
        WHERE job_serial LIKE :year_pattern
    """), {"year_pattern": f"JOB-{current_year}-%"})
    
    next_serial_num = result.fetchone()[0] + 1
    
    # Update each job
    updated_count = 0
    for job in jobs_without_uuid:
        try:
            # Generate UUID if missing
            if not job.job_uuid:
                job.job_uuid = uuid.uuid4()
            
            # Generate serial if missing
            if not job.job_serial:
                job.job_serial = f"JOB-{current_year}-{next_serial_num:06d}"
                next_serial_num += 1
            
            session.add(job)
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   📝 Updated {updated_count} jobs...")
                
        except Exception as e:
            print(f"❌ Error updating job ID {job.id}: {e}")
            continue
    
    session.commit()
    print(f"✅ Successfully updated {updated_count} jobs with permanent identifiers")


def populate_target_identifiers(session):
    """Populate UUID and serial numbers for existing targets"""
    print("🔄 Populating target identifiers...")
    
    # Get all targets that don't have UUIDs or serials
    targets_without_uuid = session.query(UniversalTarget).filter(
        (UniversalTarget.target_uuid == None) | (UniversalTarget.target_serial == None)
    ).order_by(UniversalTarget.id).all()
    
    if not targets_without_uuid:
        print("✅ All targets already have permanent identifiers")
        return
    
    print(f"📊 Found {len(targets_without_uuid)} targets needing identifiers")
    
    # Get the current year for serial generation
    current_year = datetime.now().year
    
    # Find the highest existing serial number for this year (using correct T20250000001 format)
    result = session.execute(text("""
        SELECT COALESCE(MAX(CAST(SUBSTRING(target_serial FROM 6) AS INTEGER)), 0) as max_num
        FROM universal_targets 
        WHERE target_serial LIKE :year_pattern
    """), {"year_pattern": f"T{current_year}%"})
    
    next_serial_num = result.fetchone()[0] + 1
    
    # Update each target
    updated_count = 0
    for target in targets_without_uuid:
        try:
            # Generate UUID if missing
            if not target.target_uuid:
                target.target_uuid = uuid.uuid4()
            
            # Generate serial if missing (using correct T20250000001 format)
            if not target.target_serial:
                target.target_serial = f"T{current_year}{next_serial_num:07d}"
                next_serial_num += 1
            
            session.add(target)
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   📝 Updated {updated_count} targets...")
                
        except Exception as e:
            print(f"❌ Error updating target ID {target.id}: {e}")
            continue
    
    session.commit()
    print(f"✅ Successfully updated {updated_count} targets with permanent identifiers")


def verify_population(session):
    """Verify that all records now have permanent identifiers"""
    print("🔍 Verifying permanent identifier population...")
    
    # Check jobs
    jobs_without_identifiers = session.query(Job).filter(
        (Job.job_uuid == None) | (Job.job_serial == None)
    ).count()
    
    # Check targets
    targets_without_identifiers = session.query(UniversalTarget).filter(
        (UniversalTarget.target_uuid == None) | (UniversalTarget.target_serial == None)
    ).count()
    
    total_jobs = session.query(Job).count()
    total_targets = session.query(UniversalTarget).count()
    
    print(f"📊 Verification Results:")
    print(f"   Jobs: {total_jobs - jobs_without_identifiers}/{total_jobs} have permanent identifiers")
    print(f"   Targets: {total_targets - targets_without_identifiers}/{total_targets} have permanent identifiers")
    
    if jobs_without_identifiers == 0 and targets_without_identifiers == 0:
        print("✅ All records now have permanent identifiers!")
        return True
    else:
        print(f"❌ Still missing identifiers: {jobs_without_identifiers} jobs, {targets_without_identifiers} targets")
        return False


def main():
    """Main function to populate permanent identifiers"""
    print("🚀 Starting Permanent Identifier Population Script")
    print("=" * 60)
    
    try:
        # Create database connection
        database_url = get_database_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print(f"🔗 Connected to database")
        
        # Populate job identifiers
        populate_job_identifiers(session)
        print()
        
        # Populate target identifiers
        populate_target_identifiers(session)
        print()
        
        # Verify population
        success = verify_population(session)
        print()
        
        if success:
            print("🎉 Permanent identifier population completed successfully!")
            print("✅ All existing records now have UUIDs and serial numbers")
            print("✅ Frontend should now display all records properly")
        else:
            print("⚠️  Some records still missing identifiers - manual intervention may be needed")
            
    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)
        
    finally:
        if 'session' in locals():
            session.close()
            print("🔌 Database connection closed")
    
    print("=" * 60)
    print("🏁 Script completed")


if __name__ == "__main__":
    main()