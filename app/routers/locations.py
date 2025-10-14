# app/routers/locations.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, security

from ..database import get_db

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.LocationResponse])
def read_all_locations(db: Session = Depends(get_db)):
    return crud.get_locations(db)