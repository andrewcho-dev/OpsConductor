"""
Alert API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.alert_service import AlertService
from app.schemas.alert import (
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertLogResponse
)
from opsconductor_shared.auth.dependencies import get_current_user
from opsconductor_shared.models.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert rule"""
    service = AlertService(db)
    return await service.create_alert_rule(
        rule_data=rule,
        user_id=current_user.id
    )


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alert rules"""
    service = AlertService(db)
    return await service.list_alert_rules(
        skip=skip,
        limit=limit,
        active_only=active_only,
        user_id=current_user.id
    )


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific alert rule"""
    service = AlertService(db)
    rule = await service.get_alert_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_update: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an alert rule"""
    service = AlertService(db)
    rule = await service.update_alert_rule(
        rule_id=rule_id,
        update_data=rule_update,
        user_id=current_user.id
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an alert rule"""
    service = AlertService(db)
    success = await service.delete_alert_rule(rule_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )


@router.get("/logs", response_model=List[AlertLogResponse])
async def list_alert_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alert logs"""
    service = AlertService(db)
    return await service.list_alert_logs(
        skip=skip,
        limit=limit,
        severity=severity,
        status=status,
        user_id=current_user.id
    )


@router.get("/logs/{log_id}", response_model=AlertLogResponse)
async def get_alert_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific alert log"""
    service = AlertService(db)
    log = await service.get_alert_log(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert log not found"
        )
    return log


@router.post("/logs/{log_id}/acknowledge", response_model=AlertLogResponse)
async def acknowledge_alert(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert"""
    service = AlertService(db)
    log = await service.acknowledge_alert(log_id, current_user.id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert log not found"
        )
    return log


@router.post("/logs/{log_id}/resolve", response_model=AlertLogResponse)
async def resolve_alert(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    service = AlertService(db)
    log = await service.resolve_alert(log_id, current_user.id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert log not found"
        )
    return log