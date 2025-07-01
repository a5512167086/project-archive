from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from database import SessionDep
from dependencies import get_current_user
from schemas.reservation_schema import (
    DailyAvailableSlots,
    ReservationCreate,
    ReservationItemCreate,
    ReservationItemDelete,
    ReservationItemPatch,
    ReservationItemResponse,
    ReservationListResponse,
    ReservationResponse,
)
from services.reservation_service import (
    create_user_reservation,
    delete_reservation_item_by_reservation_item_id,
    delete_user_reservation,
    get_available_times_for_item,
    get_bot_reservations_list,
    get_reservation_items_by_bot_class_id,
    get_user_reservations_in_bot_list,
    insert_new_reservation_item,
    update_reservation_item_by_reservation_item_id,
)

reservation_router = APIRouter(prefix="/reservations", tags=["reservations"])


@reservation_router.get(
    "/items/{bot_uuid}", response_model=List[ReservationItemResponse]
)
def list_reservation_items(session: SessionDep, bot_uuid: UUID):
    return get_reservation_items_by_bot_class_id(session, bot_uuid)


@reservation_router.post("/items")
def create_reservation_item(
    session: SessionDep,
    reservation_item: ReservationItemCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_new_reservation_item(session, reservation_item, user_id)
    session.commit()


@reservation_router.delete("/items")
def delete_reservation_item(
    session: SessionDep,
    delete_reservation: ReservationItemDelete,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_reservation_item_by_reservation_item_id(
        session,
        delete_reservation.bot_uuid,
        delete_reservation.delete_reservation_item_list,
        user_id,
    )
    session.commit()


@reservation_router.patch("/items")
def update_reservation_item(
    session: SessionDep,
    reservation_item_patch: ReservationItemPatch,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_reservation_item_by_reservation_item_id(
        session, reservation_item_patch, user_id
    )
    session.commit()


@reservation_router.get(
    "/items/{reservation_item_id}/available-times",
    response_model=List[DailyAvailableSlots],
)
def get_available_times(reservation_item_id: UUID, session: SessionDep):
    return get_available_times_for_item(session, reservation_item_id)


@reservation_router.post("", response_model=ReservationResponse)
def create_reservation(
    session: SessionDep,
    reservation: ReservationCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    reservation_detail = create_user_reservation(session, user_id, reservation)
    session.commit()

    return ReservationResponse(
        reservation_id=reservation_detail.reservation_id,
        reservation_item_id=reservation_detail.reservation_item_id,
        reservation_date=reservation_detail.reservation_date,
        start_time=reservation_detail.start_time,
        end_time=reservation_detail.end_time,
        price=reservation_detail.price,
        status=reservation_detail.status,
        payment_method=reservation_detail.payment_method,
        payment_status=reservation_detail.payment_status,
        note=reservation_detail.notes,
        created_at=reservation_detail.created_at,
    )


@reservation_router.delete("/{reservation_id}")
def delete_reservation(
    session: SessionDep,
    reservation_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    print(f"Deleting reservation {reservation_id} for user {user_id}")
    delete_user_reservation(session, reservation_id)
    session.commit()


@reservation_router.get(
    "/user/{bot_uuid}", response_model=List[ReservationListResponse]
)
def get_user_reservations_in_bot(
    session: SessionDep,
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get user's reservations in a specific bot"""
    user_id = current_user["user_id"]
    reservations = get_user_reservations_in_bot_list(session, bot_uuid, user_id)
    return reservations


@reservation_router.get("/{bot_uuid}", response_model=List[ReservationListResponse])
def get_bot_reservations(
    session: SessionDep,
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get all reservations for a bot (bot owner only)"""
    user_id = current_user["user_id"]
    reservations = get_bot_reservations_list(session, bot_uuid, user_id)
    return reservations
