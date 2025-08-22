#!/usr/bin/env python3
"""
Script to manually start stuck discovery jobs
"""

import sys
import os
sys.path.append('/app')

from app.tasks.discovery_tasks import run_discovery_job_task

def start_discovery_jobs():
    """Start the stuck discovery jobs"""
    job_ids = [3, 4]  # The stuck jobs
    
    for job_id in job_ids:
        try:
            print(f"Starting discovery job {job_id}...")
            result = run_discovery_job_task.delay(job_id)
            print(f"✅ Discovery job {job_id} queued successfully. Task ID: {result.id}")
        except Exception as e:
            print(f"❌ Failed to start discovery job {job_id}: {str(e)}")

if __name__ == "__main__":
    start_discovery_jobs()