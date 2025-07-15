from typing import Optional

from sqlmodel import Session, select

from modules.module.moduel_model import ModuleSetting, ModuleSettingView
from shared.models.class_object_relation_model import ClassObjectRelation
from shared.models.object_model import Object
from shared.queries.entity_query import get_entity_id_by_name


class ModuleCommand:
    def __init__(self, session: Session):
        self.session = session

    def insert_module_setting(
        self, setting_class_id: int, module_name: str, is_enabled: bool
    ):
        setting_entity_id = get_entity_id_by_name(self.session, "設定")

        module_obj = Object(
            chinese_name=module_name,
            english_name=module_name,
            entity_id=setting_entity_id,
        )
        self.session.add(module_obj)
        self.session.flush()

        module_setting = ModuleSetting(
            object_id=module_obj.object_id, is_enabled=is_enabled
        )
        self.session.add(module_setting)

        relation = ClassObjectRelation(
            class_id=setting_class_id, object_id=module_obj.object_id
        )
        self.session.add(relation)

    def update_module_setting(
        self,
        setting_class_id: int,
        module_name: str,
        is_enabled: Optional[bool] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
    ):
        module_view = self.session.exec(
            select(ModuleSettingView).where(
                ModuleSettingView.class_id == setting_class_id,
                ModuleSettingView.chinese_name == module_name,
            )
        ).first()

        module_setting = self.session.exec(
            select(ModuleSetting).where(
                ModuleSetting.object_id == module_view.object_id
            )
        ).first()

        if is_enabled is not None:
            module_setting.is_enabled = is_enabled
        if version is not None:
            module_setting.version = version
        if description is not None:
            module_setting.description = description

        self.session.add(module_setting)
