import datetime
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import models, schemas

load_dotenv()
ES_HOST = os.getenv("ELASTICSEARCH_HOST")
ES_INDEX = os.getenv("ELASTICSEARCH_INDEX", "cameras_index")

es = Elasticsearch([ES_HOST])


logger = logging.getLogger("app.crud")


async def create_user(
    db: AsyncSession, user_in: schemas.UserCreate, hashed_password: str
):
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        logger.exception("IntegrityError on create_user")
        raise
    return user


async def get_user_by_username(db: AsyncSession, username: str):
    q = select(models.User).where(models.User.username == username)
    res = await db.execute(q)
    return res.scalars().first()


async def get_user(db: AsyncSession, user_id: int):
    q = select(models.User).where(models.User.id == user_id)
    r = await db.execute(q)
    return r.scalars().first()


async def create_camera(
    db: AsyncSession, camera_in: schemas.CameraCreate, owner_id: int
):
    camera = models.Camera(
        camera_id=camera_in.camera_id,
        name=camera_in.name,
        description=camera_in.description,
        location=camera_in.location,
        is_active=camera_in.is_active,
        owner_id=owner_id,
    )
    db.add(camera)
    try:
        await db.commit()
        await db.refresh(camera)
    except IntegrityError:
        await db.rollback()
        raise

    try:
        es.index(
            index=ES_INDEX,
            id=camera.camera_id,
            document={
                "camera_id": camera.camera_id,
                "name": camera.name,
                "description": camera.description,
                "location": camera.location,
                "owner_id": camera.owner_id,
                "is_active": camera.is_active,
                "is_deleted": camera.is_deleted,
                "created_at": camera.created_at.isoformat(),
            },
        )
    except Exception:
        logger.exception("Failed to index camera in Elasticsearch")
    return camera


async def get_camera_by_camera_id(db: AsyncSession, camera_id: str):
    q = select(models.Camera).where(models.Camera.camera_id == camera_id)
    r = await db.execute(q)
    return r.scalars().first()


async def list_cameras(
    db: AsyncSession,
    owner_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False,
):
    q = select(models.Camera)
    if owner_id:
        q = q.where(models.Camera.owner_id == owner_id)
    if not include_deleted:
        q = q.where(not models.Camera.is_deleted)
    q = q.offset(skip).limit(limit).order_by(models.Camera.created_at.desc())
    r = await db.execute(q)
    return r.scalars().all()


async def update_camera(
    db: AsyncSession, camera: models.Camera, payload: schemas.CameraUpdate
):
    changed = False
    if payload.name is not None:
        camera.name = payload.name
        changed = True
    if payload.description is not None:
        camera.description = payload.description
        changed = True
    if payload.location is not None:
        camera.location = payload.location
        changed = True
    if payload.is_active is not None:
        camera.is_active = payload.is_active
        changed = True

    if changed:
        camera.updated_at = datetime.datetime.utcnow()
        try:
            db.add(camera)
            await db.commit()
            await db.refresh(camera)
        except Exception:
            await db.rollback()
            raise

        try:
            es.update(
                index=ES_INDEX,
                id=camera.camera_id,
                doc={
                    "name": camera.name,
                    "description": camera.description,
                    "location": camera.location,
                    "is_active": camera.is_active,
                    "is_deleted": camera.is_deleted,
                },
            )
        except Exception:
            try:
                es.index(
                    index=ES_INDEX,
                    id=camera.camera_id,
                    document={
                        "camera_id": camera.camera_id,
                        "name": camera.name,
                        "description": camera.description,
                        "location": camera.location,
                        "owner_id": camera.owner_id,
                        "is_active": camera.is_active,
                        "is_deleted": camera.is_deleted,
                        "created_at": camera.created_at.isoformat(),
                    },
                )
            except Exception:
                logger.exception("Failed to index/update camera in ES")
    return camera


async def soft_delete_camera(db: AsyncSession, camera: models.Camera):
    camera.is_deleted = True
    camera.is_active = False
    camera.updated_at = datetime.datetime.utcnow()
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    try:
        es.update(
            index=ES_INDEX,
            id=camera.camera_id,
            doc={"is_deleted": True, "is_active": False},
        )
    except Exception:
        logger.exception("Failed to update ES on soft delete")
    return camera


async def hard_delete_camera(db: AsyncSession, camera: models.Camera):
    await db.delete(camera)
    await db.commit()
    try:
        es.delete(index=ES_INDEX, id=camera.camera_id, ignore=[404])
    except Exception:
        logger.exception("Failed to delete from ES")


def es_search(query: str, size: int = 10, from_: int = 0):
    try:
        res = es.search(
            index=ES_INDEX,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["name", "description", "location", "camera_id"],
                }
            },
            size=size,
            from_=from_,
        )
        return res
    except Exception:
        logger.exception("ES search failed")
        return {"hits": {"hits": []}}
