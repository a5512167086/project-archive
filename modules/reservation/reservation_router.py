from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.reservation.reservation_schema import (
    DailyAvailableSlots,
    ReservationCreate,
    ReservationListResponse,
    ReservationPatch,
    ReservationResponse,
    ServiceCreate,
    ServiceDelete,
    ServicePatch,
    ServiceResponse,
)
from modules.reservation.reservation_service import (
    create_user_reservation,
    delete_service_by_service_id,
    delete_user_reservation,
    get_available_times_for_service,
    get_bot_reservations_list,
    get_services_by_bot_class_id,
    get_user_reservations_in_bot_list,
    insert_new_service,
    update_reservation_by_owner,
    update_service_by_service_id,
)
from shared.database import SessionDep
from shared.dependencies import get_current_user

reservation_router = APIRouter(prefix="/reservations", tags=["reservations"])
service_router = APIRouter(prefix="/services", tags=["services"])


@service_router.get("/{bot_uuid}", response_model=List[ServiceResponse])
def list_services(session: SessionDep, bot_uuid: UUID):
    return get_services_by_bot_class_id(session, bot_uuid)


@service_router.post("")
def create_service(
    session: SessionDep,
    service: ServiceCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_new_service(session, service, user_id)
    session.commit()


@service_router.delete("")
def delete_service(
    session: SessionDep,
    delete_service: ServiceDelete,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_service_by_service_id(
        session,
        delete_service.bot_uuid,
        delete_service.delete_service_list,
        user_id,
    )
    session.commit()


@service_router.patch("")
def update_service(
    session: SessionDep,
    service_patch: ServicePatch,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_service_by_service_id(session, service_patch, user_id)
    session.commit()


@service_router.get(
    "/{service_id}/available-times", response_model=List[DailyAvailableSlots]
)
def get_available_times(service_id: UUID, session: SessionDep):
    return get_available_times_for_service(session, service_id)


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
        service_id=reservation_detail.service_id,
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


@reservation_router.patch("", response_model=ReservationResponse)
def update_reservation(
    session: SessionDep,
    reservation_patch: ReservationPatch,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Update a reservation"""
    user_id = current_user["user_id"]
    updated_reservation = update_reservation_by_owner(
        session, user_id, reservation_patch
    )
    session.commit()

    return ReservationResponse(
        reservation_id=updated_reservation.reservation_id,
        service_id=updated_reservation.service_id,
        reservation_date=updated_reservation.reservation_date,
        start_time=updated_reservation.start_time,
        end_time=updated_reservation.end_time,
        price=updated_reservation.price,
        status=updated_reservation.status,
        payment_method=updated_reservation.payment_method,
        payment_status=updated_reservation.payment_status,
        note=updated_reservation.notes,
        created_at=updated_reservation.created_at,
    )
