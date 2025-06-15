from typing import List

from fastapi import APIRouter

from database import SessionDep
from schemas.reservation_schema import ReservationItemCreate, ReservationItemResponse
from services.reservation_service import (
    get_reservation_items_by_bot_class_id,
    insert_new_reservation_item,
)

reservation_router = APIRouter(prefix="/reservations", tags=["reservations"])


@reservation_router.get("")
def list_reservations():
    return


@reservation_router.post("")
def create_reservation():
    return


@reservation_router.patch("/{reservation_id}")
def update_reservation():
    return


@reservation_router.delete("/{reservation_id}")
def delete_reservation():
    return


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


@reservation_router.patch("/items/{item_id}")
def update_reservation_item():
    return


@reservation_router.delete("/items/{item_id}")
def delete_reservation_item():
    return
