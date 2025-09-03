from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.bot.bot_service import BotService
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
from modules.reservation.reservation_service import ReservationService
from shared.clients.database import SessionDep
from shared.constants.error_code import ErrorCode
from shared.dependencies import get_current_user
from shared.exception import GlobalErrorException
from shared.queries.group_query import is_user_in_group
from shared.services.group_service import GroupService


def get_reservation_service(session: SessionDep) -> ReservationService:
    """依賴注入 ReservationService"""
    return ReservationService(session)


def get_bot_service(session: SessionDep) -> BotService:
    """依賴注入 BotService"""
    return BotService(session)


def get_group_service(session: SessionDep) -> GroupService:
    """依賴注入 GroupService"""
    return GroupService(session)


reservation_router = APIRouter(prefix="/reservations", tags=["reservations"])
service_router = APIRouter(prefix="/services", tags=["services"])


@service_router.get("/{bot_uuid}", response_model=List[ServiceResponse])
def list_services(
    bot_uuid: UUID,
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    bot = bot_service.validate_line_bot_exists(bot_uuid)
    return reservation_service.get_services_by_bot_class_id(bot.class_id)


@service_router.post("")
def create_service(
    service: ServiceCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_bot_ownership(user_id, service.bot_uuid)
    reservation_service.insert_new_service(service, bot.class_id)
    reservation_service.session.commit()


@service_router.delete("")
def delete_service(
    delete_service: ServiceDelete,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_bot_ownership(user_id, delete_service.bot_uuid)
    reservation_service.delete_service_by_service_id(
        bot.class_id,
        delete_service.delete_service_list,
    )
    reservation_service.session.commit()


@service_router.patch("")
def update_service(
    service_patch: ServicePatch,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_bot_ownership(user_id, service_patch.bot_uuid)
    reservation_service.update_service_by_service_id(service_patch, bot.class_id)
    reservation_service.session.commit()


@service_router.get(
    "/{service_id}/available-times", response_model=List[DailyAvailableSlots]
)
def get_available_times(
    service_id: UUID,
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
):
    return reservation_service.get_available_times_for_service(service_id)


@reservation_router.post("", response_model=ReservationResponse)
def create_reservation(
    reservation: ReservationCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
):
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(reservation.bot_uuid)
    bot_group = group_service.validate_group_exist_in_bot(bot.class_id, "Users")

    if not is_user_in_group(reservation_service.session, bot_group.group_id, user_id):
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
            error_message="User is not a member of this bot's group.",
        )

    reservation_detail = reservation_service.create_user_reservation(
        user_id, reservation, bot.class_id
    )
    reservation_service.session.commit()

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
    reservation_id: UUID,
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Delete a reservation by reservation ID"""
    user_id = current_user["user_id"]
    bot_service.validate_bot_ownership(user_id, bot_uuid)
    reservation_service.delete_user_reservation(reservation_id)
    reservation_service.session.commit()


@reservation_router.get(
    "/user/{bot_uuid}", response_model=List[ReservationListResponse]
)
def get_user_reservations_in_bot(
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
):
    """Get user's reservations in a specific bot"""
    user_id = current_user["user_id"]
    bot = bot_service.validate_line_bot_exists(bot_uuid)
    bot_group = group_service.validate_group_exist_in_bot(bot.class_id, "Users")
    if not is_user_in_group(reservation_service.session, bot_group.group_id, user_id):
        raise GlobalErrorException(
            error_code=ErrorCode.USER_NOT_IN_BOT_GROUP,
            error_message="User is not a member of this bot's group.",
        )
    reservations = reservation_service.get_user_reservations_in_bot_list(
        bot.class_id, user_id
    )
    return reservations


@reservation_router.get("/{bot_uuid}", response_model=List[ReservationListResponse])
def get_bot_reservations(
    bot_uuid: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Get all reservations for a bot (bot owner only)"""
    user_id = current_user["user_id"]
    bot = bot_service.validate_bot_ownership(user_id, bot_uuid)
    reservations = reservation_service.get_bot_reservations_list(bot.class_id)
    return reservations


@reservation_router.patch("", response_model=ReservationResponse)
def update_reservation(
    reservation_patch: ReservationPatch,
    current_user: Annotated[dict, Depends(get_current_user)],
    reservation_service: Annotated[
        ReservationService, Depends(get_reservation_service)
    ],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
):
    """Update a reservation"""
    user_id = current_user["user_id"]
    bot_service.validate_bot_ownership(user_id, reservation_patch.bot_uuid)
    updated_reservation = reservation_service.update_reservation_by_owner(
        reservation_patch
    )
    reservation_service.session.commit()

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
