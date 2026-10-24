import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


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
        if simulate_startup_failure:
            raise RuntimeError("模拟：启动准备失败")
        yield
    except RuntimeError:
        logger.exception("生命周期执行失败")
        raise
    finally:
        logger.info("关闭：释放共享资源")


app = FastAPI(lifespan=lifespan)


@app.get("/status")
def get_status() -> dict[str, str]:
    logger.info("请求：读取状态")
    return {"status": "ok"}
