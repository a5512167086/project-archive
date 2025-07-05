from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends

from modules.ecomm.ecomm_schema import (
    BrandResponse,
    DeleteBrandRequest,
    InsertBrandRequest,
    UpdateBrandRequest,
)
from modules.ecomm.ecomm_service import (
    delete_brands_by_ids,
    get_all_brands,
    insert_single_brand,
    update_brand_by_id,
)
from shared.database import SessionDep
from shared.dependencies import get_current_user

brand_router = APIRouter(prefix="/brands", tags=["brands"])


@brand_router.get("/{bot_uuid}", response_model=List[BrandResponse])
def list_brands(session: SessionDep, bot_uuid: UUID):
    return get_all_brands(session, bot_uuid)


@brand_router.post("")
def create_brand(
    session: SessionDep,
    brand: InsertBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    insert_single_brand(session, brand, user_id)
    session.commit()


@brand_router.delete("")
def delete_brands(
    session: SessionDep,
    delete_request: DeleteBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    delete_brands_by_ids(session, delete_request, user_id)
    session.commit()


@brand_router.patch("")
def update_brand(
    session: SessionDep,
    update_request: UpdateBrandRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    user_id = current_user["user_id"]
    update_brand_by_id(session, update_request, user_id)
    session.commit()
