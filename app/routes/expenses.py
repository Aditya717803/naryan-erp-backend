from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense
from app.routes.auth import get_current_user
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate


router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
):
    expense = Expense(**expense_data.model_dump())
    db.add(expense)
    try:
        db.commit()
        db.refresh(expense)
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create expense",
        ) from error
    return expense


@router.get("", response_model=list[ExpenseResponse])
def get_expenses(
    limit: int = Query(default=5, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Expense)
        .order_by(Expense.date.desc(), Expense.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    for field, value in expense_data.model_dump().items():
        setattr(expense, field, value)
    try:
        db.commit()
        db.refresh(expense)
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update expense",
        ) from error
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    try:
        db.delete(expense)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete expense",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
