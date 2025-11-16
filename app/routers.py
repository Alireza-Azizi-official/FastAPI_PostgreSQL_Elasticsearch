from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, crud, schemas
from .db import get_db

router = APIRouter(prefix="/api")


@router.post("/token", response_model=schemas.Token, tags=['AUTH'])
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials"
        )
    access_token = auth.create_access_token({"sub": user.username})
    return schemas.Token(
        access_token=access_token, token_type="bearer", expires_in=int(60 * 60)
    )


@router.post("/users", response_model=schemas.UserRead, tags=['AUTH'])
async def register_user(
    user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)
):
    hashed = auth.get_password_hash(user_in.password)
    try:
        user = await crud.create_user(db, user_in, hashed)
    except Exception:
        raise HTTPException(status_code=400, detail="User creation failed or duplicate")
    return user


@router.get("/users/me", response_model=schemas.UserRead, tags=['USERS'])
async def read_own_user(current_user=Depends(auth.get_current_active_user)):
    return current_user


@router.post("/cameras", response_model=schemas.CameraRead, tags=['CAMERAS'])
async def create_camera(
    camera_in: schemas.CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    existing = await crud.get_camera_by_camera_id(db, camera_in.camera_id)
    if existing:
        raise HTTPException(status_code=400, detail="camera_id already exists")
    camera = await crud.create_camera(db, camera_in, owner_id=current_user.id)
    return camera


@router.get("/cameras", response_model=List[schemas.CameraRead],tags=['CAMERAS'])
async def list_cameras(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    if q:
        res = crud.es_search(q, size=limit, from_=skip)
        hits = res.get("hits", {}).get("hits", [])
        camera_ids = [h["_source"]["camera_id"] for h in hits]
        cameras = []
        for cid in camera_ids:
            cam = await crud.get_camera_by_camera_id(db, cid)
            if cam and cam.owner_id == current_user.id and not cam.is_deleted:
                cameras.append(cam)
        return cameras
    cameras = await crud.list_cameras(
        db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return cameras


@router.get("/cameras/{camera_id}", response_model=schemas.CameraRead,tags=['CAMERAS'])
async def get_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    camera = await crud.get_camera_by_camera_id(db, camera_id)
    if not camera or camera.is_deleted or camera.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.put("/cameras/{camera_id}", response_model=schemas.CameraRead,tags=['CAMERAS'])
async def update_camera(
    camera_id: str,
    payload: schemas.CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    camera = await crud.get_camera_by_camera_id(db, camera_id)
    if not camera or camera.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera = await crud.update_camera(db, camera, payload)
    return camera


@router.delete("/cameras/{camera_id}", response_model=schemas.CameraRead,tags=['CAMERAS'])
async def soft_delete(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    camera = await crud.get_camera_by_camera_id(db, camera_id)
    if not camera or camera.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera = await crud.soft_delete_camera(db, camera)
    return camera


@router.delete("/cameras/{camera_id}/hard", status_code=204,tags=['CAMERAS'])
async def hard_delete(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(auth.get_current_active_user),
):
    camera = await crud.get_camera_by_camera_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if camera.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete")
    await crud.hard_delete_camera(db, camera)
    return JSONResponse(status_code=204, content=None)
