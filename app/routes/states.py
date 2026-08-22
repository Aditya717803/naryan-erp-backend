from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.state import State
from app.schemas.state import StateResponse
from app.routes.auth import get_current_user



router = APIRouter(
    prefix="/states",
    tags=["States"],
    dependencies= [Depends(get_current_user)]
)


@router.get(
    "/",
    response_model=list[StateResponse],
)
def get_states(db: Session = Depends(get_db)):
    states = db.scalars(
        select(State).order_by(State.code)
    ).all()

    return states