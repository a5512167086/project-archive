from typing import List

from fastapi import APIRouter

from database import SessionDep
from schemas.reservation_schema import (
    ReservationCreate,
    ReservationItemCreate,
    ReservationItemDelete,
    ReservationItemPatch,
    ReservationItemResponse,
)
from services.reservation_service import (
    create_user_reservation,
    delete_reservation_item_by_object_id,
    get_reservation_items_by_bot_class_id,
    insert_new_reservation_item,
    update_reservation_item_by_object_id,
)

reservation_router = APIRouter(prefix="/reservations", tags=["reservations"])


@reservation_router.get(
    "/items/{bot_class_id}", response_model=List[ReservationItemResponse]
)
def list_reservation_items(session: SessionDep, bot_class_id: int):
    return get_reservation_items_by_bot_class_id(session, bot_class_id)


@reservation_router.post("/items")
def create_reservation_item(
    session: SessionDep, reservation_item: ReservationItemCreate
):
    insert_new_reservation_item(session, reservation_item)
    session.commit()


@reservation_router.delete("/items")
def delete_reservation_item(
    session: SessionDep, delete_reservation: ReservationItemDelete
):
    delete_reservation_item_by_object_id(
        session, delete_reservation.bot_class_id, delete_reservation.delete_object_list
    )
    session.commit()


@reservation_router.patch("/items")
def update_reservation_item(
    session: SessionDep, reservation_item_patch: ReservationItemPatch
):
    update_reservation_item_by_object_id(session, reservation_item_patch)
    session.commit()


@reservation_router.get("")
def list_reservations():
    return


@reservation_router.post("")
def create_reservation(session: SessionDep, reservation: ReservationCreate):
    create_user_reservation(session, reservation)
    session.commit()


@reservation_router.delete("/{reservation_id}")
def delete_reservation():
    return
