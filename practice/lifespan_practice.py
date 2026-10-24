from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("启动：准备共享资源")

    try:
        yield
    finally:
        print("关闭：释放共享资源")


app = FastAPI(lifespan=lifespan)


@app.get("/status")
def get_status() -> dict[str, str]:
    print("请求：读取状态")
    return {"status": "ok"}
