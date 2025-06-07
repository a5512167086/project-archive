from fastapi import APIRouter

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


@reservation_router.get("/items")
def list_reservation_items():
    return


@reservation_router.post("/item")
def create_reservation_item():
    return


@reservation_router.patch("/item/{item_id}")
def update_reservation_item():
    return


@reservation_router.delete("/item/{item_id}")
def delete_reservation_item():
    return
