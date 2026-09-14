from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.models import TrustedContact, User
from app.schemas.contacts import ContactCreate, ContactPublic, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

MAX_CONTACTS = 2


@router.get("", response_model=List[ContactPublic])
def list_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(TrustedContact).filter(TrustedContact.user_id == current_user.id).all()


@router.post("", response_model=ContactPublic, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(TrustedContact).filter(TrustedContact.user_id == current_user.id).all()

    if len(existing) >= MAX_CONTACTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can only have {MAX_CONTACTS} trusted contacts. Edit or delete one first.",
        )

    if any(c.phone == payload.phone for c in existing):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This phone number is already added.")

    contact = TrustedContact(
        user_id=current_user.id,
        name=payload.name,
        phone=payload.phone,
        relationship_label=payload.relationship_label,
        email=payload.email,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactPublic)
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(TrustedContact)
        .filter(TrustedContact.id == contact_id, TrustedContact.user_id == current_user.id)
        .first()
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")

    if payload.phone is not None:
        duplicate = (
            db.query(TrustedContact)
            .filter(
                TrustedContact.user_id == current_user.id,
                TrustedContact.phone == payload.phone,
                TrustedContact.id != contact_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This phone number is already added.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = (
        db.query(TrustedContact)
        .filter(TrustedContact.id == contact_id, TrustedContact.user_id == current_user.id)
        .first()
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")

    db.delete(contact)
    db.commit()
    return None
