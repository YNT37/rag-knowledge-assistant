# FastAPI 任务练习

这是一个用于学习 FastAPI 基础的内存任务 API，覆盖路由、路径参数、查询参数、请求体、Pydantic 校验、响应模型、HTTP 状态码、异常处理和 CRUD。

## 项目结构

```text
FastAPIProject/
├── main.py                    # FastAPI 应用与任务接口
├── test_main.http             # PyCharm HTTP Client 接口测试
├── requirements.txt           # Python 依赖
├── practice/
│   └── filter_practice.py     # Python 列表、字典和搜索练习
└── README.md                  # 项目说明
```

`.venv`、`.idea`、缓存和本地环境变量由 `.gitignore` 排除，不属于项目源码。

## 运行项目

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

启动后访问：

- API 文档：<http://127.0.0.1:8000/docs>
- 备用文档：<http://127.0.0.1:8000/redoc>
- 首页：<http://127.0.0.1:8000/>

如果需要重新创建环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 任务接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/tasks` | 查询全部任务 |
| `GET` | `/tasks/{task_id}` | 根据 ID 查询任务 |
| `POST` | `/tasks` | 创建任务 |
| `PUT` | `/tasks/{task_id}` | 完整更新任务 |
| `PATCH` | `/tasks/{task_id}` | 局部更新任务 |
| `DELETE` | `/tasks/{task_id}` | 删除任务 |
| `GET` | `/search` | 按标题搜索并分页 |

可以在 `/docs` 中交互测试，也可以在 PyCharm 中打开 `test_main.http`，点击每个请求旁边的运行按钮。

## 当前限制

- `tasks` 是内存列表，不是数据库。
- 创建、修改和删除的数据会在服务重启后丢失。
- 当前项目用于基础练习，后续再接入数据库、配置文件、自动化测试和目录分层。

## 运行 Python 小练习

```powershell
.\.venv\Scripts\python.exe .\practice\filter_practice.py
```
