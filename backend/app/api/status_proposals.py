from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas, models
from app.auth import get_current_user_or_api_key

router = APIRouter(prefix="/status-proposals", tags=["status-proposals"])


@router.post("/{proposal_id}/approve", response_model=schemas.StatusProposalResponse)
def approve_proposal(
    proposal_id: UUID,
    approval: schemas.StatusProposalApproval,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_proposal = crud.get_status_proposal(db, proposal_id=proposal_id)
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if db_proposal.status != "pending":
        raise HTTPException(status_code=400, detail="Proposal is not pending")
    
    # JWT 인증된 사용자의 ID를 approved_by로 사용 (API Key인 경우도 user 객체)
    approval_data = schemas.StatusProposalApproval(
        approved_by=current_user.id,
        rejected_reason=approval.rejected_reason
    )
    return crud.approve_status_proposal(db, proposal_id=proposal_id, approval=approval_data)


@router.post("/{proposal_id}/reject", response_model=schemas.StatusProposalResponse)
def reject_proposal(
    proposal_id: UUID,
    rejection: schemas.StatusProposalRejection,
    current_user: models.User = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    db_proposal = crud.get_status_proposal(db, proposal_id=proposal_id)
    if not db_proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if db_proposal.status != "pending":
        raise HTTPException(status_code=400, detail="Proposal is not pending")
    
    return crud.reject_status_proposal(
        db,
        proposal_id=proposal_id,
        rejected_reason=rejection.rejected_reason,
        rejected_by=current_user.id
    )
