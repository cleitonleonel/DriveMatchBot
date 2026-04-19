from fastapi import APIRouter, Depends, HTTPException
from drivematch.controllers.user import UserController
from pydantic import BaseModel

router = APIRouter()


def get_controller():
    return UserController()


class SettingsUpdate(BaseModel):
    base_fare: float = None
    price_per_km: float = None
    price_per_min: float = None
    service_fee: float = None
    default_platform_percentage: float = None


@router.get("/stats")
async def get_stats(controller: UserController = Depends(get_controller)):
    return await controller.get_admin_stats()


@router.get("/metrics")
async def get_metrics(controller: UserController = Depends(get_controller)):
    return await controller.get_financial_metrics()


@router.post("/users/{user_id}/toggle")
async def toggle_user(user_id: int, controller: UserController = Depends(get_controller)):
    success, new_state = await controller.toggle_user_active(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "is_active": new_state}


@router.get("/settings")
async def get_settings(controller: UserController = Depends(get_controller)):
    return await controller.get_system_settings()


@router.patch("/settings")
async def update_settings(data: SettingsUpdate, controller: UserController = Depends(get_controller)):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    await controller.update_system_settings(**update_data)
    return {"success": True}


@router.post("/payouts/{request_id}/confirm")
async def confirm_payout(request_id: int, controller: UserController = Depends(get_controller)):
    success, telegram_id = await controller.confirm_payout(request_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to confirm payout")
    return {"success": True, "telegram_id": telegram_id}
