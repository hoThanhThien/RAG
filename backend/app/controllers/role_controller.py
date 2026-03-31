from fastapi import APIRouter
router = APIRouter()

@router.get("/roles")
def get_roles():
    return [{"role_id": 1, "role_name": "Admin"}]
