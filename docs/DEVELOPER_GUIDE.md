# EnableDRM Developer Guide

## Getting Started with Execution Serialization

This guide covers how to work with EnableDRM's hierarchical execution serialization system in your applications.

## Understanding the Serialization Hierarchy

### Serial Format Structure
```
J20250001.0001.0001
│ │      │    │
│ │      │    └── Target sequence (0001-9999)
│ │      └────── Execution sequence (0001-9999)
│ └──────────── Job serial (year + 5-digit sequence)
└─────────────── Prefix (J=Job, T=Target)
```

### Relationship Mapping
```
Job (J20250001)
├── Execution 1 (J20250001.0001)
│   ├── Target Result 1 (J20250001.0001.0001) → T20250001
│   ├── Target Result 2 (J20250001.0001.0002) → T20250002
│   └── Target Result 3 (J20250001.0001.0003) → T20250003
├── Execution 2 (J20250001.0002)
│   ├── Target Result 1 (J20250001.0002.0001) → T20250001
│   └── Target Result 2 (J20250001.0002.0002) → T20250002
└── Execution 3 (J20250001.0003)
    └── Target Result 1 (J20250001.0003.0001) → T20250004
```

## Backend Development

### Working with SerialService

#### Generating Serials
```python
from app.services.serial_service import SerialService
from sqlalchemy.orm import Session

def create_job_execution(db: Session, job_id: int):
    # Get the job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    # Generate execution serial
    execution_serial = SerialService.generate_execution_serial(db, job.job_serial)
    
    # Create execution
    execution = JobExecution(
        job_id=job_id,
        execution_serial=execution_serial,
        execution_number=get_next_execution_number(job_id),
        status=ExecutionStatus.RUNNING
    )
    
    db.add(execution)
    db.flush()
    
    return execution
```

#### Validating Serials
```python
def validate_execution_request(execution_serial: str):
    if not SerialService.validate_execution_serial(execution_serial):
        raise ValueError(f"Invalid execution serial format: {execution_serial}")
    
    # Parse components
    components = SerialService.parse_execution_serial(execution_serial)
    job_serial = components['job_serial']
    execution_number = components['execution_number']
    
    return job_serial, execution_number
```

#### Database Queries
```python
def get_execution_hierarchy(db: Session, job_serial: str):
    """Get complete execution hierarchy for a job"""
    
    # Get job
    job = db.query(Job).filter(Job.job_serial == job_serial).first()
    
    # Get all executions
    executions = db.query(JobExecution).filter(
        JobExecution.execution_serial.like(f"{job_serial}.%")
    ).order_by(JobExecution.execution_number).all()
    
    # Get all branches
    branches = db.query(JobExecutionBranch).filter(
        JobExecutionBranch.branch_serial.like(f"{job_serial}.%")
    ).order_by(JobExecutionBranch.branch_serial).all()
    
    return {
        'job': job,
        'executions': executions,
        'branches': branches
    }
```

### Creating New API Endpoints

#### Serial-based Lookup Endpoint
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/executions/serial/{execution_serial}")
async def get_execution_by_serial(
    execution_serial: str,
    db: Session = Depends(get_db)
):
    # Validate serial format
    if not SerialService.validate_execution_serial(execution_serial):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid execution serial format: {execution_serial}"
        )
    
    # Find execution
    execution = db.query(JobExecution).filter(
        JobExecution.execution_serial == execution_serial
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {execution_serial}"
        )
    
    return execution

@router.get("/executions/branch/{branch_serial}")
async def get_branch_by_serial(
    branch_serial: str,
    db: Session = Depends(get_db)
):
    # Validate serial format
    if not SerialService.validate_branch_serial(branch_serial):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid branch serial format: {branch_serial}"
        )
    
    # Find branch
    branch = db.query(JobExecutionBranch).filter(
        JobExecutionBranch.branch_serial == branch_serial
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=404,
            detail=f"Branch not found: {branch_serial}"
        )
    
    return branch
```

#### Performance Analytics Endpoint
```python
@router.get("/targets/{target_serial}/performance")
async def get_target_performance(
    target_serial: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    # Validate target serial
    if not SerialService.validate_target_serial(target_serial):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target serial format: {target_serial}"
        )
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get target performance data
    branches = db.query(JobExecutionBranch).filter(
        and_(
            JobExecutionBranch.target_serial_ref == target_serial,
            JobExecutionBranch.created_at >= start_date,
            JobExecutionBranch.created_at <= end_date
        )
    ).all()
    
    # Calculate metrics
    total_executions = len(branches)
    successful = len([b for b in branches if b.status == ExecutionStatus.COMPLETED])
    failed = len([b for b in branches if b.status == ExecutionStatus.FAILED])
    
    return {
        "target_serial": target_serial,
        "period_days": days,
        "total_executions": total_executions,
        "successful_executions": successful,
        "failed_executions": failed,
        "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0
    }
```

### Database Migrations

#### Adding Serial Fields to Existing Tables
```python
# migration file: add_execution_serials.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add execution serial fields
    op.add_column('job_executions', 
        sa.Column('execution_uuid', postgresql.UUID(), nullable=True))
    op.add_column('job_executions', 
        sa.Column('execution_serial', sa.String(50), nullable=True))
    
    # Add branch serial fields
    op.add_column('job_execution_branches', 
        sa.Column('branch_uuid', postgresql.UUID(), nullable=True))
    op.add_column('job_execution_branches', 
        sa.Column('branch_serial', sa.String(100), nullable=True))
    op.add_column('job_execution_branches', 
        sa.Column('target_serial_ref', sa.String(50), nullable=True))
    
    # Create indexes
    op.create_index('idx_execution_serial', 'job_executions', ['execution_serial'])
    op.create_index('idx_branch_serial', 'job_execution_branches', ['branch_serial'])
    op.create_index('idx_target_serial_ref', 'job_execution_branches', ['target_serial_ref'])

def downgrade():
    # Remove indexes
    op.drop_index('idx_target_serial_ref')
    op.drop_index('idx_branch_serial')
    op.drop_index('idx_execution_serial')
    
    # Remove columns
    op.drop_column('job_execution_branches', 'target_serial_ref')
    op.drop_column('job_execution_branches', 'branch_serial')
    op.drop_column('job_execution_branches', 'branch_uuid')
    op.drop_column('job_executions', 'execution_serial')
    op.drop_column('job_executions', 'execution_uuid')
```

## Frontend Development

### Working with Execution Serials in React

#### Displaying Execution Serials
```jsx
import React from 'react';
import { Typography, Box, Chip } from '@mui/material';

const ExecutionSerialDisplay = ({ execution }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Typography 
        variant="body1" 
        sx={{ 
          fontFamily: 'monospace', 
          fontWeight: 600,
          fontSize: '0.9rem'
        }}
      >
        {execution.execution_serial}
      </Typography>
      <Chip 
        label={`#${execution.execution_number}`}
        size="small"
        variant="outlined"
      />
    </Box>
  );
};

const BranchSerialDisplay = ({ branch }) => {
  return (
    <Box>
      <Typography 
        variant="body2" 
        sx={{ 
          fontFamily: 'monospace', 
          fontWeight: 600,
          fontSize: '0.75rem'
        }}
      >
        {branch.branch_serial}
      </Typography>
      {branch.target_serial_ref && (
        <Typography 
          variant="caption" 
          color="text.secondary"
          sx={{ fontFamily: 'monospace' }}
        >
          → {branch.target_serial_ref}
        </Typography>
      )}
    </Box>
  );
};
```

#### Serial-based Navigation
```jsx
import { useNavigate } from 'react-router-dom';

const ExecutionNavigator = () => {
  const navigate = useNavigate();
  
  const navigateToExecution = (executionSerial) => {
    navigate(`/executions/${executionSerial}`);
  };
  
  const navigateToBranch = (branchSerial) => {
    navigate(`/executions/branch/${branchSerial}`);
  };
  
  const navigateToTarget = (targetSerial) => {
    navigate(`/targets/${targetSerial}`);
  };
  
  return (
    // Navigation component implementation
  );
};
```

#### Search and Filter Components
```jsx
import React, { useState, useEffect } from 'react';
import { TextField, Autocomplete } from '@mui/material';

const ExecutionSerialSearch = ({ onSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  
  useEffect(() => {
    if (searchTerm.length >= 3) {
      fetchExecutionSuggestions(searchTerm)
        .then(setSuggestions);
    }
  }, [searchTerm]);
  
  const fetchExecutionSuggestions = async (term) => {
    const response = await fetch(`/api/executions/search?q=${term}&limit=10`);
    const data = await response.json();
    return data.results;
  };
  
  return (
    <Autocomplete
      options={suggestions}
      getOptionLabel={(option) => option.execution_serial}
      renderOption={(props, option) => (
        <Box component="li" {...props}>
          <Box>
            <Typography sx={{ fontFamily: 'monospace' }}>
              {option.execution_serial}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {option.job_name} - {option.status}
            </Typography>
          </Box>
        </Box>
      )}
      onInputChange={(event, value) => setSearchTerm(value)}
      onChange={(event, value) => onSelect(value)}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Search Executions"
          placeholder="J20250001.0001"
          variant="outlined"
        />
      )}
    />
  );
};
```

### API Integration Patterns

#### Fetching Execution Data
```javascript
// API service for execution operations
class ExecutionService {
  static async getBySerial(executionSerial) {
    const response = await fetch(`/api/executions/serial/${executionSerial}`);
    if (!response.ok) {
      throw new Error(`Execution not found: ${executionSerial}`);
    }
    return response.json();
  }
  
  static async getBranchBySerial(branchSerial) {
    const response = await fetch(`/api/executions/branch/${branchSerial}`);
    if (!response.ok) {
      throw new Error(`Branch not found: ${branchSerial}`);
    }
    return response.json();
  }
  
  static async getTargetPerformance(targetSerial, days = 30) {
    const response = await fetch(`/api/targets/${targetSerial}/performance?days=${days}`);
    if (!response.ok) {
      throw new Error(`Target not found: ${targetSerial}`);
    }
    return response.json();
  }
  
  static async searchExecutions(query, type = 'all', limit = 50) {
    const params = new URLSearchParams({ q: query, type, limit });
    const response = await fetch(`/api/executions/search?${params}`);
    return response.json();
  }
}

// React hook for execution data
const useExecution = (executionSerial) => {
  const [execution, setExecution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (executionSerial) {
      ExecutionService.getBySerial(executionSerial)
        .then(setExecution)
        .catch(setError)
        .finally(() => setLoading(false));
    }
  }, [executionSerial]);
  
  return { execution, loading, error };
};
```

## Testing

### Unit Tests for Serial Service
```python
import pytest
from app.services.serial_service import SerialService

class TestSerialService:
    def test_validate_job_serial(self):
        # Valid formats
        assert SerialService.validate_job_serial("J20250001") == True
        assert SerialService.validate_job_serial("J20251337") == True
        
        # Invalid formats
        assert SerialService.validate_job_serial("JOB20250001") == False
        assert SerialService.validate_job_serial("J2025001") == False
        assert SerialService.validate_job_serial("J202500001") == False
    
    def test_validate_execution_serial(self):
        # Valid formats
        assert SerialService.validate_execution_serial("J20250001.0001") == True
        assert SerialService.validate_execution_serial("J20251337.9999") == True
        
        # Invalid formats
        assert SerialService.validate_execution_serial("J20250001") == False
        assert SerialService.validate_execution_serial("J20250001.001") == False
        assert SerialService.validate_execution_serial("J20250001.00001") == False
    
    def test_parse_execution_serial(self):
        result = SerialService.parse_execution_serial("J20250001.0042")
        assert result == {
            'job_serial': 'J20250001',
            'execution_number': 42
        }
    
    def test_parse_branch_serial(self):
        result = SerialService.parse_branch_serial("J20250001.0042.0123")
        assert result == {
            'job_serial': 'J20250001',
            'execution_number': 42,
            'branch_number': 123
        }
```

### Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestExecutionAPI:
    def test_get_execution_by_serial(self):
        # Create test execution
        execution_serial = "J20250001.0001"
        
        response = client.get(f"/api/executions/serial/{execution_serial}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['execution_serial'] == execution_serial
    
    def test_get_branch_by_serial(self):
        # Create test branch
        branch_serial = "J20250001.0001.0001"
        
        response = client.get(f"/api/executions/branch/{branch_serial}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['branch_serial'] == branch_serial
    
    def test_invalid_serial_format(self):
        response = client.get("/api/executions/serial/invalid_serial")
        assert response.status_code == 400
        assert "Invalid execution serial format" in response.json()['detail']
```

### Frontend Tests
```javascript
// Jest tests for React components
import { render, screen } from '@testing-library/react';
import ExecutionSerialDisplay from './ExecutionSerialDisplay';

describe('ExecutionSerialDisplay', () => {
  test('displays execution serial correctly', () => {
    const execution = {
      execution_serial: 'J20250001.0001',
      execution_number: 1
    };
    
    render(<ExecutionSerialDisplay execution={execution} />);
    
    expect(screen.getByText('J20250001.0001')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
  });
  
  test('displays branch serial with target reference', () => {
    const branch = {
      branch_serial: 'J20250001.0001.0001',
      target_serial_ref: 'T20250001'
    };
    
    render(<BranchSerialDisplay branch={branch} />);
    
    expect(screen.getByText('J20250001.0001.0001')).toBeInTheDocument();
    expect(screen.getByText('→ T20250001')).toBeInTheDocument();
  });
});
```

## Performance Considerations

### Database Optimization
```sql
-- Optimized queries for serial lookups
CREATE INDEX CONCURRENTLY idx_execution_serial_prefix 
ON job_executions USING btree (left(execution_serial, 9));

CREATE INDEX CONCURRENTLY idx_branch_serial_execution 
ON job_execution_branches USING btree (left(branch_serial, 14));

-- Partitioning by year for large datasets
CREATE TABLE job_executions_2025 PARTITION OF job_executions
FOR VALUES FROM ('J2025') TO ('J2026');
```

### Caching Strategies
```python
from functools import lru_cache
import redis

# Redis caching for frequently accessed executions
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_execution_cached(execution_serial: str):
    # Check cache first
    cached = redis_client.get(f"execution:{execution_serial}")
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    execution = get_execution_from_db(execution_serial)
    
    # Cache for 1 hour
    redis_client.setex(
        f"execution:{execution_serial}", 
        3600, 
        json.dumps(execution)
    )
    
    return execution
```

## Best Practices

### 1. Always Validate Serials
```python
def process_execution_request(execution_serial: str):
    if not SerialService.validate_execution_serial(execution_serial):
        raise ValueError(f"Invalid execution serial: {execution_serial}")
    
    # Process the request
```

### 2. Use Consistent Error Handling
```python
class SerialNotFoundError(Exception):
    def __init__(self, serial: str, serial_type: str):
        self.serial = serial
        self.serial_type = serial_type
        super().__init__(f"{serial_type} not found: {serial}")

def get_execution_or_404(execution_serial: str):
    execution = get_execution(execution_serial)
    if not execution:
        raise SerialNotFoundError(execution_serial, "Execution")
    return execution
```

### 3. Implement Proper Logging
```python
import logging

logger = logging.getLogger(__name__)

def create_execution(job_serial: str):
    execution_serial = SerialService.generate_execution_serial(db, job_serial)
    
    logger.info(
        "Created execution",
        extra={
            "job_serial": job_serial,
            "execution_serial": execution_serial,
            "action": "execution_created"
        }
    )
    
    return execution_serial
```

### 4. Use Type Hints
```python
from typing import Optional, List, Dict, Any

def get_execution_hierarchy(job_serial: str) -> Dict[str, Any]:
    """Get complete execution hierarchy for a job"""
    return {
        'job_serial': job_serial,
        'executions': get_executions(job_serial),
        'branches': get_branches(job_serial)
    }

def parse_serial_components(serial: str) -> Optional[Dict[str, Any]]:
    """Parse serial into components"""
    if SerialService.validate_execution_serial(serial):
        return SerialService.parse_execution_serial(serial)
    elif SerialService.validate_branch_serial(serial):
        return SerialService.parse_branch_serial(serial)
    return None
```

This developer guide provides comprehensive coverage of working with the EnableDRM execution serialization system across all layers of the application.