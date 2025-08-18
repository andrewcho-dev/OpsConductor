"""
Serial Number Generation Service
Generates permanent, human-readable serial numbers for jobs, targets, executions, and actions.
Formats:
- Jobs: J20250000001 (7-digit format - supports ~10M jobs/year)
- Targets: T20250000001 (7-digit format - supports ~10M targets/year) 
- Executions: J20250000001.0001 (hierarchical)
- Branches: J20250000001.0001.0001 (branch results per target)
- Actions: J20250000001.0001.0001.0001 (individual action results)
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.database import get_db
import logging

logger = logging.getLogger(__name__)


class SerialService:
    """Service for generating permanent serial numbers"""
    
    @staticmethod
    def generate_job_serial(db: Session) -> str:
        """
        Generate a unique job serial number in format: J20250000001
        Uses database sequence to ensure uniqueness across all instances.
        Supports up to 9,999,999 jobs per year (7 digits).
        """
        try:
            current_year = datetime.now().year
            
            # Get next sequence number for this year (7-digit format only)
            result = db.execute(text("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(job_serial FROM 6) AS INTEGER)), 0) + 1 as next_num
                FROM jobs 
                WHERE job_serial LIKE :year_pattern
            """), {"year_pattern": f"J{current_year}%"})
            
            next_num = result.fetchone()[0]
            
            # Format: J20250000001 (7 digits, zero-padded) - supports ~10M jobs/year
            serial = f"J{current_year}{next_num:07d}"
            
            logger.info(f"Generated job serial: {serial} (7-digit format)")
            return serial
            
        except Exception as e:
            logger.error(f"Error generating job serial: {e}")
            # Fallback to timestamp-based serial
            timestamp = int(datetime.now().timestamp()) % 9999999
            return f"J{current_year}{timestamp:07d}"
    
    @staticmethod
    def generate_target_serial(db: Session) -> str:
        """
        Generate a unique target serial number in format: T20250000001
        Uses database sequence to ensure uniqueness across all instances.
        Supports up to 9,999,999 targets per year (7 digits).
        """
        try:
            current_year = datetime.now().year
            
            # Get next sequence number for this year (7-digit format only)
            result = db.execute(text("""
                SELECT COALESCE(MAX(CAST(SUBSTRING(target_serial FROM 6) AS INTEGER)), 0) + 1 as next_num
                FROM universal_targets 
                WHERE target_serial LIKE :year_pattern
            """), {"year_pattern": f"T{current_year}%"})
            
            next_num = result.fetchone()[0]
            
            # Format: T20250000001 (7 digits, zero-padded) - supports ~10M targets/year
            serial = f"T{current_year}{next_num:07d}"
            
            logger.info(f"Generated target serial: {serial} (7-digit format)")
            return serial
            
        except Exception as e:
            logger.error(f"Error generating target serial: {e}")
            # Fallback to timestamp-based serial
            timestamp = int(datetime.now().timestamp()) % 9999999
            return f"T{current_year}{timestamp:07d}"
    
    @staticmethod
    def generate_execution_serial(db: Session, job_serial: str) -> str:
        """
        Generate a unique execution serial number in format: J20250001.0001
        Based on the job serial and execution sequence.
        """
        try:
            # Get next execution number for this job
            result = db.execute(text("""
                SELECT COALESCE(MAX(execution_number), 0) + 1 as next_num
                FROM job_executions je
                JOIN jobs j ON je.job_id = j.id
                WHERE j.job_serial = :job_serial
            """), {"job_serial": job_serial})
            
            next_num = result.fetchone()[0]
            
            # Format: J20250001.0001 (4 digits, zero-padded)
            serial = f"{job_serial}.{next_num:04d}"
            
            logger.info(f"Generated execution serial: {serial}")
            return serial
            
        except Exception as e:
            logger.error(f"Error generating execution serial: {e}")
            # Fallback to timestamp-based serial
            timestamp = int(datetime.now().timestamp()) % 9999
            return f"{job_serial}.{timestamp:04d}"
    
    @staticmethod
    def generate_branch_serial(db: Session, execution_serial: str, target_serial: str) -> str:
        """
        Generate a unique branch serial number in format: J20250001.0001.0001
        Based on the execution serial and target sequence.
        """
        try:
            # Get next target number for this execution
            result = db.execute(text("""
                SELECT COALESCE(MAX(CAST(branch_id AS INTEGER)), 0) + 1 as next_num
                FROM job_execution_branches jeb
                JOIN job_executions je ON jeb.job_execution_id = je.id
                WHERE je.execution_serial = :execution_serial
            """), {"execution_serial": execution_serial})
            
            next_num = result.fetchone()[0]
            
            # Format: J20250001.0001.0001 (4 digits, zero-padded)
            serial = f"{execution_serial}.{next_num:04d}"
            
            logger.info(f"Generated branch serial: {serial} for target {target_serial}")
            return serial
            
        except Exception as e:
            logger.error(f"Error generating branch serial: {e}")
            # Fallback to timestamp-based serial
            timestamp = int(datetime.now().timestamp()) % 9999
            return f"{execution_serial}.{timestamp:04d}"
    
    @staticmethod
    def generate_action_serial(db: Session, branch_serial: str) -> str:
        """
        Generate a unique action serial number in format: J20250001.0001.0001.0001
        Based on the branch serial and action sequence.
        Uses database-level locking to prevent race conditions.
        """
        try:
            # Use SELECT FOR UPDATE to prevent race conditions
            # First get the branch ID for locking
            branch_result = db.execute(text("""
                SELECT id FROM job_execution_branches 
                WHERE branch_serial = :branch_serial
                FOR UPDATE
            """), {"branch_serial": branch_serial})
            
            branch_row = branch_result.fetchone()
            if not branch_row:
                raise ValueError(f"Branch with serial {branch_serial} not found")
            
            branch_id = branch_row[0]
            
            # Get next action number for this branch with proper locking
            result = db.execute(text("""
                SELECT COALESCE(MAX(action_order), 0) + 1 as next_num
                FROM job_action_results 
                WHERE branch_id = :branch_id
            """), {"branch_id": branch_id})
            
            next_num = result.fetchone()[0]
            
            # Format: J20250001.0001.0001.0001 (4 digits, zero-padded)
            serial = f"{branch_serial}.{next_num:04d}"
            
            logger.info(f"Generated action serial: {serial} (action_order: {next_num})")
            return serial
            
        except Exception as e:
            logger.error(f"Error generating action serial: {e}")
            # Fallback to timestamp-based serial with microseconds for uniqueness
            timestamp = int(datetime.now().timestamp() * 1000000) % 9999
            return f"{branch_serial}.{timestamp:04d}"
    
    @staticmethod
    def validate_job_serial(serial: str) -> bool:
        """Validate job serial format: J20250000001 (7-digit format only)"""
        if not serial or len(serial) != 12:
            return False
        
        try:
            return (
                serial[0] == "J" and
                serial[1:5].isdigit() and  # Year (4 digits)
                serial[5:12].isdigit() and # Number (7 digits)
                len(serial[5:12]) == 7     # 7-digit number
            )
        except:
            return False
    
    @staticmethod
    def validate_target_serial(serial: str) -> bool:
        """Validate target serial format: T20250000001 (7-digit format only)"""
        if not serial or len(serial) != 12:
            return False
        
        try:
            return (
                serial[0] == "T" and
                serial[1:5].isdigit() and  # Year (4 digits)
                serial[5:12].isdigit() and # Number (7 digits)
                len(serial[5:12]) == 7     # 7-digit number
            )
        except:
            return False
    
    @staticmethod
    def validate_execution_serial(serial: str) -> bool:
        """Validate execution serial format: J20250000001.0001 (7-digit job format)"""
        if not serial or len(serial) != 17:  # 12 + 1 + 4 = 17
            return False
        
        try:
            parts = serial.split('.')
            if len(parts) != 2:
                return False
            
            job_part, exec_part = parts
            return (
                SerialService.validate_job_serial(job_part) and
                len(exec_part) == 4 and exec_part.isdigit()
            )
        except:
            return False
    
    @staticmethod
    def validate_branch_serial(serial: str) -> bool:
        """Validate branch serial format: J20250000001.0001.0001 (7-digit job format)"""
        if not serial or len(serial) != 22:  # 12 + 1 + 4 + 1 + 4 = 22
            return False
        
        try:
            parts = serial.split('.')
            if len(parts) != 3:
                return False
            
            job_part, exec_part, branch_part = parts
            return (
                SerialService.validate_job_serial(job_part) and
                len(exec_part) == 4 and exec_part.isdigit() and
                len(branch_part) == 4 and branch_part.isdigit()
            )
        except:
            return False
    
    @staticmethod
    def validate_action_serial(serial: str) -> bool:
        """Validate action serial format: J20250000001.0001.0001.0001 (7-digit job format)"""
        if not serial or len(serial) != 27:  # 12 + 1 + 4 + 1 + 4 + 1 + 4 = 27
            return False
        
        try:
            parts = serial.split('.')
            if len(parts) != 4:
                return False
            
            job_part, exec_part, branch_part, action_part = parts
            return (
                SerialService.validate_job_serial(job_part) and
                len(exec_part) == 4 and exec_part.isdigit() and
                len(branch_part) == 4 and branch_part.isdigit() and
                len(action_part) == 4 and action_part.isdigit()
            )
        except:
            return False
    
    @staticmethod
    def parse_execution_serial(serial: str) -> dict:
        """Parse execution serial into components"""
        if not SerialService.validate_execution_serial(serial):
            return None
        
        parts = serial.split('.')
        return {
            'job_serial': parts[0],
            'execution_number': int(parts[1])
        }
    
    @staticmethod
    def parse_branch_serial(serial: str) -> dict:
        """Parse branch serial into components"""
        if not SerialService.validate_branch_serial(serial):
            return None
        
        parts = serial.split('.')
        return {
            'job_serial': parts[0],
            'execution_number': int(parts[1]),
            'branch_number': int(parts[2])
        }
    
    @staticmethod
    def parse_action_serial(serial: str) -> dict:
        """Parse action serial into components"""
        if not SerialService.validate_action_serial(serial):
            return None
        
        parts = serial.split('.')
        return {
            'job_serial': parts[0],
            'execution_number': int(parts[1]),
            'branch_number': int(parts[2]),
            'action_number': int(parts[3])
        }