from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.models.user import User
from app.permissions.dependencies import require_auth
from app.schemas.customer import CustomerActivityCreate, CustomerCreate, CustomerOwnerUpdate, CustomerRelatedPersonCreate, CustomerRelatedPersonUpdate, CustomerStatusUpdate, CustomerUpdate
from app.services.customer_service import add_customer_activity, add_related_person, create_customer, delete_related_person, get_customer_detail, list_customer_assignees, list_customers, list_related_people, serialize_customer, serialize_customer_activity, serialize_related_person, soft_delete_customer, update_customer, update_customer_owner, update_customer_status, update_related_person

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def get_customers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = None, status_filter: str | None = Query(None, alias="status"), customer_type: str | None = None, owner_id: UUID | None = None, source: str | None = None, project: str | None = None, next_follow_up_from: date | None = None, next_follow_up_to: date | None = None, gender: str | None = None, province: str | None = None, district: str | None = None, financial_rating: str | None = None, buying_purpose: str | None = None, interested_property_type: str | None = None, buying_timeline: str | None = None, score_label: str | None = None, score_min: int | None = Query(None, ge=0), score_max: int | None = Query(None, ge=0), scope: str | None = Query(None), db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    if scope == "mine":
        owner_id = current_user.id
    customers, meta = list_customers(db, current_user, page=page, page_size=page_size, search=search, customer_status=status_filter, customer_type=customer_type, owner_id=owner_id, source=source, project=project, next_follow_up_from=next_follow_up_from, next_follow_up_to=next_follow_up_to, gender=gender, province=province, district=district, financial_rating=financial_rating, buying_purpose=buying_purpose, interested_property_type=interested_property_type, buying_timeline=buying_timeline, score_label=score_label, score_min=score_min, score_max=score_max)
    return success_response(data=[serialize_customer(item) for item in customers], message="Customers retrieved", meta=meta)


@router.get("/assignees")
def get_assignees(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=[{"id": user.id, "full_name": user.full_name, "email": user.email} for user in list_customer_assignees(db, current_user)], message="Customer assignees retrieved")


@router.post("")
def post_customer(payload: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_customer(create_customer(db, payload, current_user), detail=True, db=db, actor=current_user), message="Customer created")


@router.get("/{customer_id}/related-people")
def get_related_people(customer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=[serialize_related_person(item) for item in list_related_people(db, customer_id, current_user)], message="Related people retrieved")


@router.post("/{customer_id}/related-people")
def post_related_person(customer_id: UUID, payload: CustomerRelatedPersonCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_related_person(add_related_person(db, customer_id, payload, current_user)), message="Related person created")


@router.put("/{customer_id}/related-people/{person_id}")
def put_related_person(customer_id: UUID, person_id: UUID, payload: CustomerRelatedPersonUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_related_person(update_related_person(db, customer_id, person_id, payload, current_user)), message="Related person updated")


@router.delete("/{customer_id}/related-people/{person_id}")
def remove_related_person(customer_id: UUID, person_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    delete_related_person(db, customer_id, person_id, current_user)
    return success_response(data=None, message="Related person deleted")


@router.get("/{customer_id}")
def get_customer(customer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return success_response(data=serialize_customer(get_customer_detail(db, customer_id, current_user), detail=True, db=db, actor=current_user), message="Customer retrieved")


@router.put("/{customer_id}")
def put_customer(customer_id: UUID, payload: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer(db, customer, payload, current_user), detail=True, db=db, actor=current_user), message="Customer updated")


@router.post("/{customer_id}/status")
def post_status(customer_id: UUID, payload: CustomerStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer_status(db, customer, payload, current_user), detail=True, db=db, actor=current_user), message="Customer status updated")


@router.post("/{customer_id}/owner")
def post_owner(customer_id: UUID, payload: CustomerOwnerUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer(update_customer_owner(db, customer, payload, current_user), detail=True, db=db, actor=current_user), message="Customer owner updated")


@router.post("/{customer_id}/activities")
def post_activity(customer_id: UUID, payload: CustomerActivityCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user)
    return success_response(data=serialize_customer_activity(add_customer_activity(db, customer, payload, current_user)), message="Customer activity created")


@router.delete("/{customer_id}")
def delete_customer(customer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    customer = get_customer_detail(db, customer_id, current_user); soft_delete_customer(db, customer, current_user)
    return success_response(data=None, message="Customer deleted")
