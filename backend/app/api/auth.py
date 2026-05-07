import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app import crud, schemas, models
from app.auth import verify_password, get_password_hash, create_access_token, get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db, user, hashed_password)


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserWithTeam)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


# ========== API Keys ==========

@router.get("/api-keys", response_model=List[schemas.ApiKeyResponse])
def list_api_keys(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    keys = crud.get_api_keys_by_user(db, user_id=current_user.id)
    # 생성된 키는 노출하지 않음
    return keys


@router.post("/api-keys", response_model=schemas.ApiKeyResponse)
def create_api_key(
    key_data: schemas.ApiKeyCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 랜덤 키 생성 (sym_ 접두사 + 32바이트 URL-safe 랜덤 문자열)
    raw_key = f"sym_{secrets.token_urlsafe(32)}"
    key_hash = get_password_hash(raw_key)
    
    db_key = crud.create_api_key(
        db,
        user_id=current_user.id,
        name=key_data.name or "Unnamed Agent",
        key_hash=key_hash
    )
    
    # 응답에만 raw_key를 포함 (이후에는 다시 노출되지 않음)
    response_data = schemas.ApiKeyResponse.model_validate(db_key)
    response_data.key = raw_key
    return response_data


@router.delete("/api-keys/{key_id}")
def delete_api_key(
    key_id: UUID,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_api_key(db, key_id=key_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deleted"}
