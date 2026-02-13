import argparse
import logging
from datetime import time
from typing import List
from uuid import UUID

from sqlmodel import Session

from modules.bot.bot_query import BotQuery
from modules.reservation.reservation_command import ReservationCommand
from modules.reservation.reservation_query import ReservationQuery
from modules.reservation.reservation_schema import (
    ServiceCreate,
    ServiceOptionCreate,
    ServiceOptionGroupCreate,
    ServiceScheduleCreate,
)
from shared.clients.database import engine
from shared.constants.common import SelectionType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db() -> Session:
    return Session(engine)


def generate_barber_shop_data(bot_uuid: UUID) -> List[ServiceCreate]:
    default_schedules = [
        ServiceScheduleCreate(
            schedule_type="weekly",
            weekday=day,
            start_time=time(10, 0),
            end_time=time(20, 0),
            capacity=2,
            is_active=True,
        )
        for day in range(7)
    ]

    designer_group = ServiceOptionGroupCreate(
        group_name="指定設計師",
        group_description="請選擇為您服務的設計師",
        selection_type=SelectionType.single,
        is_required=True,
        display_order=0,
        options=[
            ServiceOptionCreate(option_name="不指定", price=0, display_order=0),
            ServiceOptionCreate(
                option_name="資深設計師 Alice", price=200, display_order=1
            ),
            ServiceOptionCreate(option_name="店長 Kevin", price=500, display_order=2),
        ],
    )

    shampoo_group = ServiceOptionGroupCreate(
        group_name="加購洗髮服務",
        selection_type=SelectionType.single,
        is_required=False,
        display_order=1,
        options=[
            ServiceOptionCreate(option_name="一般洗髮", price=200, display_order=0),
            ServiceOptionCreate(option_name="精油舒壓洗髮", price=350, display_order=1),
        ],
    )

    length_group = ServiceOptionGroupCreate(
        group_name="髮長說明",
        group_description="請依照實際長度選擇，現場將進行確認",
        selection_type=SelectionType.single,
        is_required=True,
        display_order=0,
        options=[
            ServiceOptionCreate(option_name="短髮 (耳上)", price=0, display_order=0),
            ServiceOptionCreate(
                option_name="中長髮 (及肩)", price=300, display_order=1
            ),
            ServiceOptionCreate(option_name="長髮 (過肩)", price=600, display_order=2),
            ServiceOptionCreate(
                option_name="特長髮 (及腰)", price=900, display_order=3
            ),
        ],
    )

    extra_group = ServiceOptionGroupCreate(
        group_name="其他加購服務",
        group_description="可複選，升級您的服務體驗",
        selection_type=SelectionType.multiple,
        is_required=False,
        display_order=2,
        options=[
            ServiceOptionCreate(
                option_name="頭皮隔離 (染燙推薦)", price=300, display_order=0
            ),
            ServiceOptionCreate(option_name="瞬間水療護髮", price=500, display_order=1),
            ServiceOptionCreate(option_name="眉型修整", price=100, display_order=2),
            ServiceOptionCreate(option_name="造型品定型", price=50, display_order=3),
        ],
    )

    services = [
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="男士精緻剪髮",
            service_description="含剪髮、修容、簡易造型。",
            duration_minutes=45,
            price=600,
            option_groups=[designer_group, shampoo_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="女士設計剪髮",
            service_description="根據臉型設計專屬髮型，含基礎吹整。",
            duration_minutes=60,
            price=800,
            option_groups=[designer_group, shampoo_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="兒童剪髮 (12歲以下)",
            service_description="耐心引導，提供汽車座椅，讓寶貝不害怕。",
            duration_minutes=30,
            price=400,
            option_groups=[designer_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="瀏海修剪",
            service_description="快速修整瀏海，維持完美視線。",
            duration_minutes=15,
            price=150,
            option_groups=[],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="基礎護髮",
            service_description="快速補充水分，改善毛躁。",
            duration_minutes=45,
            price=1200,
            option_groups=[length_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="深層結構護髮",
            service_description="重建髮絲結構，回復彈性與光澤。",
            duration_minutes=90,
            price=2500,
            option_groups=[length_group, shampoo_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="頭皮深層SPA",
            service_description="頭皮檢測、去角質、按摩放鬆、毛囊調理。",
            duration_minutes=60,
            price=1800,
            option_groups=[extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="日系空氣感燙髮",
            service_description="打造自然蓬鬆線條，含洗剪。",
            duration_minutes=180,
            price=3000,
            option_groups=[designer_group, length_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="質感單色染髮",
            service_description="使用進口染膏，色彩飽和持久 (不含漂)。",
            duration_minutes=120,
            price=2000,
            option_groups=[designer_group, length_group, extra_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="男士油頭造型 (洗+抓)",
            service_description="重要場合必備，包含洗髮與精緻抓髮造型。",
            duration_minutes=40,
            price=500,
            option_groups=[designer_group, extra_group],
            default_schedules=default_schedules,
        ),
    ]

    return services


def seed_services(bot_uuid_str: str):
    db = get_db()
    reservation_command = ReservationCommand(db)
    reservation_query = ReservationQuery(db)
    bot_query = BotQuery(db)

    try:
        bot_uuid = UUID(bot_uuid_str)
    except ValueError:
        logger.error("Invalid BOT_UUID format.")
        return

    logger.info(f"--- Fetching Bot with UUID: {bot_uuid} ---")
    bot = bot_query.get_bot_by_uuid(bot_uuid)
    if not bot:
        logger.error(f"Bot with UUID {bot_uuid} not found.")
        return
    logger.info(
        f"Using bot with UUID: {bot.bot_detail_id} and class_id: {bot.class_id}"
    )

    service_class_id = reservation_query.get_service_class_id_by_bot_class_id(
        bot.class_id
    )

    if not service_class_id:
        logger.error(
            f"Service class ID not found for bot class_id: {bot.class_id}. "
            "Please ensure the Reservation module is enabled and initialized for this bot."
        )
        return

    logger.info(f"Found Service Class ID: {service_class_id}")

    services_data = generate_barber_shop_data(bot_uuid)
    logger.info(f"Generated {len(services_data)} services to insert.")

    logger.info("--- Inserting Services ---")
    success_count = 0

    for service in services_data:
        try:
            reservation_command.insert_reservation_item(
                service_class_id=service_class_id,
                service_name=service.service_name,
                service_description=service.service_description,
                service_duration_minutes=service.duration_minutes,
                service_price=service.price,
                option_group_list=service.option_groups,
                schedule_list=service.default_schedules,
            )
            logger.info(f"Inserted service: {service.service_name}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to insert service '{service.service_name}': {e}")
            db.rollback()
            continue

    db.commit()
    logger.info(
        f"--- Seeding finished. Successfully inserted {success_count} services. ---"
    )
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed reservation service data (Barber Shop example)."
    )
    parser.add_argument(
        "--bot-uuid",
        required=True,
        help="The UUID of the bot to associate the services with.",
    )
    args = parser.parse_args()

    seed_services(args.bot_uuid)
