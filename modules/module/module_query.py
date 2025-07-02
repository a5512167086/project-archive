from typing import List

from sqlmodel import Session, select

from modules.module.moduel_model import ModuleSettingView
from shared.models.class_model import SubClassView
from shared.queries.entity_query import get_entity_id_by_name


def get_single_module_setting(
    session: Session, module_class_id: int, module_name: str
) -> ModuleSettingView | None:
    setting = session.exec(
        select(ModuleSettingView).where(
            ModuleSettingView.class_id == module_class_id,
            ModuleSettingView.chinese_name == module_name,
        )
    ).first()

    return setting


def get_setting_class_id_by_bot_class_id(
    session: Session, bot_class_id: int
) -> int | None:
    setting_entity_id = get_entity_id_by_name(session, "設定")

    result = session.exec(
        select(SubClassView.class_id).where(
            SubClassView.parent_class_id == bot_class_id,
            SubClassView.entity_id == setting_entity_id,
        )
    ).first()

    return result


def get_all_settings_by_class_id(
    session: Session, class_id: int
) -> List[ModuleSettingView]:
    settings = session.exec(
        select(ModuleSettingView).where(ModuleSettingView.class_id == class_id)
    ).all()

    return settings
