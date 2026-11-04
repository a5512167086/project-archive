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


def generate_taekwondo_dojo_data(bot_uuid: UUID) -> List[ServiceCreate]:
    default_schedules = [
        ServiceScheduleCreate(
            schedule_type="weekly",
            weekday=day,
            start_time=time(17, 0),
            end_time=time(21, 0),
            capacity=12,
            is_active=True,
        )
        for day in range(1, 6)  # Monday to Friday
    ] + [
        ServiceScheduleCreate(
            schedule_type="weekly",
            weekday=6,  # Saturday
            start_time=time(9, 0),
            end_time=time(17, 0),
            capacity=16,
            is_active=True,
        )
    ]

    coach_group = ServiceOptionGroupCreate(
        group_name="Coach Selection",
        group_description="Choose your preferred coach",
        selection_type=SelectionType.single,
        is_required=False,
        display_order=0,
        options=[
            ServiceOptionCreate(option_name="No Preference", price=0, display_order=0),
            ServiceOptionCreate(option_name="Coach Kim", price=0, display_order=1),
            ServiceOptionCreate(option_name="Coach Park", price=200, display_order=2),
            ServiceOptionCreate(
                option_name="Head Master Session", price=500, display_order=3
            ),
        ],
    )

    level_group = ServiceOptionGroupCreate(
        group_name="Student Level",
        group_description="Please select the student's current level. Final placement may be adjusted on-site.",
        selection_type=SelectionType.single,
        is_required=True,
        display_order=1,
        options=[
            ServiceOptionCreate(option_name="Beginner", price=0, display_order=0),
            ServiceOptionCreate(
                option_name="White / Yellow Belt", price=0, display_order=1
            ),
            ServiceOptionCreate(
                option_name="Yellow / Green Belt", price=0, display_order=2
            ),
            ServiceOptionCreate(
                option_name="Blue Belt and Above", price=0, display_order=3
            ),
        ],
    )

    age_group = ServiceOptionGroupCreate(
        group_name="Age Group",
        group_description="Some classes are arranged based on age group",
        selection_type=SelectionType.single,
        is_required=True,
        display_order=2,
        options=[
            ServiceOptionCreate(
                option_name="Ages 4-6 (Preschool)", price=0, display_order=0
            ),
            ServiceOptionCreate(
                option_name="Ages 7-12 (Children)", price=0, display_order=1
            ),
            ServiceOptionCreate(
                option_name="Ages 13-17 (Teen)", price=0, display_order=2
            ),
            ServiceOptionCreate(option_name="Adults 18+", price=0, display_order=3),
        ],
    )

    gear_rental_group = ServiceOptionGroupCreate(
        group_name="Protective Gear Rental",
        group_description="Optional rental equipment for class or sparring training",
        selection_type=SelectionType.multiple,
        is_required=False,
        display_order=3,
        options=[
            ServiceOptionCreate(option_name="Head Guard", price=50, display_order=0),
            ServiceOptionCreate(
                option_name="Chest Protector", price=80, display_order=1
            ),
            ServiceOptionCreate(
                option_name="Arm and Shin Guard Set", price=100, display_order=2
            ),
            ServiceOptionCreate(
                option_name="Full Protective Gear Set", price=200, display_order=3
            ),
        ],
    )

    uniform_group = ServiceOptionGroupCreate(
        group_name="Equipment Add-ons",
        group_description="Optional beginner equipment purchase",
        selection_type=SelectionType.multiple,
        is_required=False,
        display_order=4,
        options=[
            ServiceOptionCreate(
                option_name="Dobok Uniform", price=1200, display_order=0
            ),
            ServiceOptionCreate(option_name="White Belt", price=150, display_order=1),
            ServiceOptionCreate(
                option_name="Protective Gear Set", price=2500, display_order=2
            ),
            ServiceOptionCreate(
                option_name="Kick Pad Training Set", price=900, display_order=3
            ),
        ],
    )

    goal_group = ServiceOptionGroupCreate(
        group_name="Training Goal",
        group_description="Help the coach understand your training objective",
        selection_type=SelectionType.single,
        is_required=False,
        display_order=5,
        options=[
            ServiceOptionCreate(option_name="Basic Fitness", price=0, display_order=0),
            ServiceOptionCreate(
                option_name="Self-defense and Technique", price=0, display_order=1
            ),
            ServiceOptionCreate(
                option_name="Belt Promotion Preparation", price=0, display_order=2
            ),
            ServiceOptionCreate(
                option_name="Competition Training", price=300, display_order=3
            ),
        ],
    )

    services = [
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Beginner Taekwondo Trial Class",
            service_description="Perfect for first-time students to experience basic techniques, kicking, and taekwondo etiquette.",
            duration_minutes=60,
            price=300,
            option_groups=[coach_group, age_group, uniform_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Preschool Taekwondo Group Class",
            service_description="A fun, game-based class designed to improve focus, balance, and basic coordination.",
            duration_minutes=50,
            price=450,
            option_groups=[coach_group, age_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Children's Beginner Taekwondo Class",
            service_description="Builds a strong foundation in stance, kicking, poomsae basics, and discipline.",
            duration_minutes=60,
            price=500,
            option_groups=[coach_group, level_group, age_group, goal_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Children's Advanced Promotion Class",
            service_description="For students with prior experience, focusing on poomsae, advanced kicking, and belt test preparation.",
            duration_minutes=75,
            price=650,
            option_groups=[coach_group, level_group, goal_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Teen / Adult Mixed Taekwondo Class",
            service_description="A balanced training class for teens and adults, covering fitness, technique, and sparring fundamentals.",
            duration_minutes=90,
            price=700,
            option_groups=[
                coach_group,
                level_group,
                age_group,
                goal_group,
                gear_rental_group,
            ],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Poomsae Special Training Class",
            service_description="Focused on poomsae precision, rhythm, stability, and performance for testing or competition.",
            duration_minutes=90,
            price=800,
            option_groups=[coach_group, level_group, goal_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Sparring Performance Training Class",
            service_description="Intensive training in competition rules, footwork, reaction timing, and match rhythm.",
            duration_minutes=90,
            price=950,
            option_groups=[coach_group, level_group, goal_group, gear_rental_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="One-on-One Private Lesson",
            service_description="Personalized training tailored to the student's level and goals for faster improvement.",
            duration_minutes=60,
            price=1800,
            option_groups=[coach_group, level_group, goal_group, gear_rental_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Semi-Private Lesson (2 Students)",
            service_description="Train with a friend while still receiving focused instruction and personalized feedback.",
            duration_minutes=60,
            price=2600,
            option_groups=[coach_group, level_group, goal_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Belt Promotion Registration",
            service_description="Includes belt test registration, movement review, and assessment scheduling.",
            duration_minutes=30,
            price=1200,
            option_groups=[coach_group, level_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Competition Athlete Training Program",
            service_description="High-intensity training designed for school team members and students preparing for tournaments.",
            duration_minutes=120,
            price=1500,
            option_groups=[coach_group, level_group, goal_group, gear_rental_group],
            default_schedules=default_schedules,
        ),
        ServiceCreate(
            bot_uuid=bot_uuid,
            service_name="Seasonal Taekwondo Intensive Camp",
            service_description="A short-term intensive program combining fitness, techniques, poomsae, and sparring practice.",
            duration_minutes=180,
            price=2200,
            option_groups=[coach_group, age_group, level_group, uniform_group],
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

    services_data = generate_taekwondo_dojo_data(bot_uuid)
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
        description="Seed reservation service data (Taekwondo Dojo example)."
    )
    parser.add_argument(
        "--bot-uuid",
        required=True,
        help="The UUID of the bot to associate the services with.",
    )
    args = parser.parse_args()

    seed_services(args.bot_uuid)
