from fastapi import APIRouter

from . import (
    netbox,
)

api_router = APIRouter()

api_router.include_router(netbox.router)
