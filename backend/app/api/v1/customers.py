from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.customer import CustomerActivityCreate, CustomerCreate, CustomerOwnerUpdate, CustomerStatusUpdate, CustomerUpdate
from app.services.customer_service import add_customer_activity, create_customer, get_customer_detail, list_customer_assignees, list_customers, serialize_customer, serialize_customer_activity, soft_delete_customer, update_customer, update_customer_owner, update_customer_status

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def get_customers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, status_filter: str | None = Query(None, alias="status"), customer_type: str | None = None, owner_id: UUID | None = None, source: str | None = None, project: str | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customers, meta = list_customers(db, current_user, page=page, page_size=page_size, search=search, customer_status=status_filter, customer_type=customer_type, owner_id=owner_id, source=source, project=project, next_follow_up_from=next_follow_up_from, next_follow_up_to=next_follow_up_to)
    return success_response(data=[serialize_customer(item) for item in customers], message="Customers retrieved", meta=meta)


@router.get("/assignees")
def get_assignees(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=[{"id": user.id, "full_name": user.full_name, "email": user.email} for user in list_customer_assignees(db, current_user)], message="Customer assignees retrieved")


@router.post("")
def post_customer(payload: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_customer(create_customer(db, payload, current_user), detail=True), message="Customer created")


@router.get("/{customer_id}")
def get_customer(customer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_customer(get_customer_detail(db, customer_id, current_user), detail=True), message="Customer retrieved")


@router.put("/{customer_id}")
def put_customer(customer_id: UUID, payload: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer(db, customer, payload, current_user), detail=True), message="Customer updated")


@router.post("/{customer_id}/status")
def post_status(customer_id: UUID, payload: CustomerStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer_status(db, customer, payload, current_user), detail=True), message="Customer status updated")


@router.post("/{customer_id}/owner")
def post_owner(customer_id: UUID, payload: CustomerOwnerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer_owner(db, customer, payload, current_user), detail=True), message="Customer owner updated")


@router.post("/{customer_id}/activities")
def post_activity(customer_id: UUID, payload: CustomerActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer_activity(add_customer_activity(db, customer, payload, current_user)), message="Customer activity created")


@router.delete("/{customer_id}")
def delete_customer(customer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user); soft_delete_customer(db, customer, current_user)
    return success_response(data=None, message="Customer deleted")
