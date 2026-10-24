import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi import Depends

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s(%(name)s): %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("启动：准备共享资源")
    raw_value = os.getenv("SIMULATE_STARTUP_FAILURE", "false")
    simulate_startup_failure = raw_value.lower() == "true"
    try:
        app.state.resource = {"name": "模拟知识库"}
        logger.info("准备完成：资源名称=%s", app.state.resource["name"])
        if simulate_startup_failure:
            raise RuntimeError("模拟：启动准备失败")
        yield
    except RuntimeError:
        logger.exception("生命周期执行失败")
        raise
    finally:
        app.state.resource = None
        logger.info("关闭：清除资源=%s", app.state.resource)


app = FastAPI(lifespan=lifespan)


def get_resource_name(request: Request) -> dict[str, str]:
    return request.app.state.resource


@app.get("/status")
def get_status(resource: Annotated[dict[str, str], Depends(get_resource_name)]) -> dict[str, str]:
    logger.info("请求：读取状态")
    return {
        "status": "ok",
        "resource_name": resource["name"],
    }


@app.get("/resource")
def get_resource(resource: Annotated[dict[str, str], Depends(get_resource_name)]) -> dict[str, str]:
    return resource
