from typing import Optional

from sqlmodel import Session, select

from models.class_object_relation_model import ClassObjectRelation
from models.moduel_setting_model import ModuleSetting, ModuleSettingView
from models.object_model import Object
from queries.entity_query import get_entity_id_by_name


def insert_module_setting(
    session: Session, setting_class_id: int, module_name: str, is_enabled: bool
):
    setting_entity_id = get_entity_id_by_name(session, "設定")

    module_obj = Object(
        chinese_name=module_name, english_name=module_name, entity_id=setting_entity_id
    )
    session.add(module_obj)
    session.flush()

    module_setting = ModuleSetting(
        object_id=module_obj.object_id, is_enabled=is_enabled
    )
    session.add(module_setting)

    relation = ClassObjectRelation(
        class_id=setting_class_id, object_id=module_obj.object_id
    )
    session.add(relation)


def update_module_setting(
    session: Session,
    setting_class_id: int,
    module_name: str,
    is_enabled: Optional[bool] = None,
    version: Optional[str] = None,
    description: Optional[str] = None,
):
    module_view = session.exec(
        select(ModuleSettingView).where(
            ModuleSettingView.class_id == setting_class_id,
            ModuleSettingView.chinese_name == module_name,
        )
    ).first()

    module_setting = session.exec(
        select(ModuleSetting).where(ModuleSetting.object_id == module_view.object_id)
    ).first()

    if is_enabled is not None:
        module_setting.is_enabled = is_enabled
    if version is not None:
        module_setting.version = version
    if description is not None:
        module_setting.description = description

    session.add(module_setting)
