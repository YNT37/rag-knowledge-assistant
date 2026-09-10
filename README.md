# FastAPI SQLite 任务管理 API

这是一个用于学习 Python 后端开发的任务管理 API。项目基于 FastAPI 和 SQLite，实现任务的增删改查、关键词搜索、分页、数据校验和持久化存储。

## 已实现功能

- 查询全部任务和根据 ID 查询单条任务
- 创建、完整修改、部分修改和删除任务
- 按标题关键词搜索
- 使用 `LIMIT` 和 `OFFSET` 分页
- 使用 Pydantic 校验请求和响应
- 使用 SQLite 持久化数据
- 为不存在的任务返回 404
- 为非法请求数据返回 422

## 项目结构

```text
FastAPIProject/
├── main.py                     # FastAPI 路由、请求模型和响应模型
├── database.py                 # SQLite 数据访问层
├── test_main.http              # PyCharm HTTP 请求练习
├── requirements.txt            # Python 依赖
├── practice/
│   ├── filter_practice.py      # Python 筛选练习
│   └── sqlite_practice.py      # SQLite 基础练习
├── .gitignore
└── README.md
```

运行时会在项目目录生成 `tasks.db`。该文件保存本地任务数据，并已通过 `.gitignore` 排除，不提交到 Git。

## 运行项目

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

启动后访问：

- Swagger 文档：<http://127.0.0.1:8000/docs>
- ReDoc 文档：<http://127.0.0.1:8000/redoc>
- 首页：<http://127.0.0.1:8000/>

如果需要重新创建环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 接口说明

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/tasks` | 查询全部任务 |
| `GET` | `/tasks/{task_id}` | 根据 ID 查询任务 |
| `POST` | `/tasks` | 创建任务 |
| `PUT` | `/tasks/{task_id}` | 完整修改任务 |
| `PATCH` | `/tasks/{task_id}` | 部分修改任务 |
| `DELETE` | `/tasks/{task_id}` | 删除任务 |
| `GET` | `/search` | 按标题搜索并分页 |

## 请求示例

创建任务：

```json
{
  "title": "学习 FastAPI",
  "done": false
}
```

部分修改任务：

```json
{
  "done": true
}
```

搜索和分页：

```text
GET /search?keyword=FastAPI&skip=0&limit=10
```

## 请求处理流程

```text
客户端发起 HTTP 请求
→ FastAPI 匹配路由
→ Pydantic 校验 Path、Query 和 Body
→ 路由调用 database.py
→ database.py 执行参数化 SQL
→ SQLite 读取或修改数据
→ 响应模型校验结果
→ FastAPI 返回状态码和 JSON
```

`main.py` 负责 HTTP 接口，`database.py` 负责数据库操作，避免把路由和 SQL 全部写在同一个文件中。

## 验证结果

已通过 Swagger 手动验证：

- POST 创建任务并返回 201
- GET 根据 ID 查询任务
- PUT 完整修改任务
- PATCH 只修改指定字段
- 关键词搜索和分页
- 服务重启后数据仍然存在
- 不存在的任务返回 404
- 空标题返回 422
- 删除后再次查询返回 404

## 当前限制

- 尚未实现用户注册、登录和权限控制
- 尚未编写自动化接口测试
- 尚未加入日志、配置管理和数据库迁移
- 尚未进行生产环境部署
- 当前是 Python 后端基础项目，不包含 LLM、RAG 或 Agent 功能

## 后续计划

- 增加自动化测试
- 完善异常处理和数据库连接管理
- 学习 SQLAlchemy 或其他 ORM
- 将后端基础能力复用到 AI 应用项目
