from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.saved_filter import SavedFilter
from app.models.user import User
from app.schemas.saved_filter import SavedFilterCreate, SavedFilterRead, SavedFilterUpdate

router = APIRouter(prefix="/saved-filters", tags=["saved-filters"])


def _get_owned_or_404(db: Session, user: User, filter_id: int) -> SavedFilter:
    saved_filter = db.get(SavedFilter, filter_id)
    if saved_filter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")
    if saved_filter.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the filter owner")
    return saved_filter


@router.get("", response_model=list[SavedFilterRead])
def list_saved_filters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(SavedFilter)
        .filter(SavedFilter.owner_user_id == user.id)
        .order_by(SavedFilter.id)
        .all()
    )


@router.post("", response_model=SavedFilterRead, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    payload: SavedFilterCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    saved_filter = SavedFilter(
        owner_user_id=user.id,
        name=payload.name,
        query=payload.query.model_dump(exclude_none=True),
    )
    db.add(saved_filter)
    db.commit()
    db.refresh(saved_filter)
    return saved_filter


@router.get("/{filter_id}", response_model=SavedFilterRead)
def get_saved_filter(
    filter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return _get_owned_or_404(db, user, filter_id)


@router.patch("/{filter_id}", response_model=SavedFilterRead)
def update_saved_filter(
    filter_id: int,
    payload: SavedFilterUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    saved_filter = _get_owned_or_404(db, user, filter_id)
    if payload.name is not None:
        saved_filter.name = payload.name
    if payload.query is not None:
        saved_filter.query = payload.query.model_dump(exclude_none=True)
    db.commit()
    db.refresh(saved_filter)
    return saved_filter


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    filter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    saved_filter = _get_owned_or_404(db, user, filter_id)
    db.delete(saved_filter)
    db.commit()
