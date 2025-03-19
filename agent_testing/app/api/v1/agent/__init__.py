from fastapi import APIRouter

from .requirements import router as requirements_router
from .testcase import router as testcase_router

agent_router = APIRouter()
agent_router.include_router(requirements_router, tags=["智能体"])
agent_router.include_router(testcase_router, tags=["智能体"])
__all__ = ["agent_router"]