import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from drivematch.controllers.user import UserController
from web.routes.admin_api import router as api_router

app = FastAPI(title="DriveMatch Admin")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="web/templates")


# Dependency for controller
def get_controller():
    return UserController()


# Simple Auth (Environment Variable)
ADMIN_TOKEN = os.getenv("ADMIN_WEB_TOKEN", "drivematch_admin_secret")


async def verify_token(request: Request):
    token = request.headers.get("X-Admin-Token") or request.query_params.get("token")
    if token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, controller: UserController = Depends(get_controller)):
    stats = await controller.get_admin_stats()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"stats": stats, "active_page": "dashboard"}
    )


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, controller: UserController = Depends(get_controller)):
    users = await controller.get_all_users(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"users": users, "active_page": "users"}
    )


@app.get("/travels", response_class=HTMLResponse)
async def travels_page(request: Request, controller: UserController = Depends(get_controller)):
    travels = await controller.list_travels_paginated(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="travels.html",
        context={"travels": travels, "active_page": "travels"}
    )


@app.get("/payouts", response_class=HTMLResponse)
async def payouts_page(request: Request, controller: UserController = Depends(get_controller)):
    requests = await controller.list_pending_payouts()
    return templates.TemplateResponse(
        request=request,
        name="payouts.html",
        context={"payout_requests": requests, "active_page": "payouts"}
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, controller: UserController = Depends(get_controller)):
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"active_page": "settings"}
    )


# Include API router
app.include_router(api_router, prefix="/api")
