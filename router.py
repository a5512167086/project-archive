from fastapi import APIRouter

router = APIRouter()

@router.get('/search')
def get_search_data():
    return 'ok'