from commands.faq import insert_faq_item
from exception import GlobalErrorException
from queries.faq import get_knowledge_class_id_by_bot_class_id
from schemas import InsertFAQRequest


def validate_knowledge_class(bot_class_id: int) -> int:
    knowledge_class_id = get_knowledge_class_id_by_bot_class_id(bot_class_id)
    if not knowledge_class_id:
        raise GlobalErrorException(
            error_code="KNOWLEDGE_CLASS_NOT_FOUND",
            error_message="Knowledge class not found for the given bot class",
        )
    return knowledge_class_id


def insert_single_faq(body: InsertFAQRequest):
    validate_knowledge_class(body.bot_class_id)
    insert_faq_item(body.bot_class_id, body.question, body.answer)
