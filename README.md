# FastAPI SQLite 与 RAG 知识库 API

这是一个用于学习 Python 后端与 AI 应用开发的综合项目。项目从 FastAPI + SQLite 任务管理 API 起步，逐步加入大模型调用、多轮对话、本地 Embedding 语义检索、RAG 知识库问答和自动化测试。

当前版本能够展示以下能力：

- 使用 FastAPI 设计 REST API；
- 使用 Pydantic 校验请求和约束响应；
- 使用 SQLite 实现任务数据持久化和 CRUD；
- 调用 OpenAI 兼容格式的大模型 API；
- 实现单轮问答和由客户端传入历史的多轮对话；
- 读取本地 Markdown 文档并进行重叠切片；
- 使用本地 Qwen3 Embedding 模型进行语义检索；
- 将检索结果作为上下文交给大模型生成带来源回答；
- 使用 pytest、TestClient、monkeypatch 和临时数据库完成自动化测试。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic 2
- SQLite
- OpenAI Python SDK（兼容 DeepSeek API）
- Sentence Transformers
- Qwen3-Embedding-0.6B
- PyTorch + CUDA
- pytest

## 项目结构

```text
FastAPIProject/
├── main.py                         # FastAPI 路由、请求模型和响应模型
├── database.py                     # SQLite 数据访问层
├── llm_service.py                  # 大模型 API 调用
├── rag_service.py                  # Embedding、语义检索与 RAG 服务
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量示例
├── tests/
│   └── test_main.py                # 自动化接口测试
├── practice/
│   ├── documents/                  # 本地 Markdown 知识库
│   ├── rag_document_practice.py    # 文档读取与重叠切片
│   ├── retrieval_evaluation_practice.py # 检索评估脚本
│   └── check_torch.py              # PyTorch 与 CUDA 检查
├── test_main.http                  # PyCharm HTTP 请求练习
├── .gitignore
└── README.md
```

运行时会在项目目录使用 `tasks.db` 保存任务数据。`.env`、数据库文件、虚拟环境和缓存文件不应提交到 Git。

## 2026-10-16 代码整理

独立的基础、算法、SQLite/ORM和早期模型练习共16份，已归档到本机同级目录
`../FastAPIProject-practice-archive-2026-10-16/`，保留原文件与清理前快照，不属于产品运行依赖。
`practice/rag_document_practice.py`、`practice/documents/`、检索评估与设备检查仍保留。
原数据库、环境、配置和待核实的空JS文件保持原位。

主入口已移除3个依赖演示接口、4个打印中间件和未用SQLAlchemy导入；保留12个显式业务/欢迎接口。
手工HTTP文件移除2条当前无对应路由的旧请求。RAG文档处理模块的迁移不在本次范围。

## 核心数据流

### 任务管理

```text
客户端请求
→ FastAPI 路由
→ Pydantic 请求校验
→ database.py
→ SQLite
→ 响应模型校验
→ JSON 响应
```

### RAG 知识库问答

```text
用户问题
→ Pydantic 清理和校验
→ 本地 Embedding 模型生成问题向量
→ 与文档块向量计算相似度
→ Top K 排序和最低分过滤
→ 组装带来源的上下文
→ 调用大模型
→ 返回回答
```

`rag_service.py` 使用延迟初始化：导入模块时不会立刻加载模型；第一次语义检索时才加载模型、读取文档并生成文档向量，同一 Python 进程中的后续请求会复用这些资源。

## 创建运行环境

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 可选：安装 CUDA 版本 PyTorch

普通环境可以使用 CPU。当前开发机使用 CUDA 12.6 构建：

```powershell
python -m pip install --force-reinstall torch==2.14.0 --index-url https://download.pytorch.org/whl/cu126
```

检查运行设备：

```powershell
python practice/check_torch.py
```

预期在支持的 NVIDIA 显卡环境中看到：

```text
CUDA 是否可用： True
```

## 配置环境变量

复制示例文件：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中填写：

```text
LLM_API_KEY=你的DeepSeek密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
EMBEDDING_MODEL_PATH=你的本地Embedding模型目录
```

当前使用的本地模型为：

```text
Qwen/Qwen3-Embedding-0.6B
```

`.env` 包含本机路径和 API 密钥，已经通过 `.gitignore` 排除，不应上传到 GitHub。`.env.example` 只用于说明项目需要哪些配置。

## 启动项目

```powershell
python -m uvicorn main:app --reload
```

启动后访问：

- Swagger 文档：<http://127.0.0.1:8000/docs>
- ReDoc 文档：<http://127.0.0.1:8000/redoc>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>
- 首页：<http://127.0.0.1:8000/>

## 接口说明

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/` | 固定欢迎信息，未检查数据库或模型健康 |
| `GET` | `/tasks` | 查询全部任务 |
| `GET` | `/tasks/{task_id}` | 根据 ID 查询任务 |
| `POST` | `/tasks` | 创建任务 |
| `PUT` | `/tasks/{task_id}` | 完整修改任务 |
| `PATCH` | `/tasks/{task_id}` | 部分修改任务 |
| `DELETE` | `/tasks/{task_id}` | 删除任务 |
| `GET` | `/search` | 按标题搜索并分页 |
| `POST` | `/ai/ask` | 单轮大模型问答 |
| `POST` | `/ai/chat` | 带客户端历史的多轮对话 |
| `POST` | `/ai/rag` | 基于本地知识库生成回答 |
| `POST` | `/ai/retrieve` | 只返回相关文本块，不调用大模型 |

## 请求示例

### 创建任务

```json
{
  "title": "学习 FastAPI",
  "done": false
}
```

### RAG 问答

```json
{
  "question": "FastAPI 有什么作用？"
}
```

如果知识库中没有足够相关的资料，接口正常返回：

```json
{
  "answer": "根据现有资料无法回答"
}
```

### 纯语义检索

```json
{
  "question": "什么工具可以管理代码版本？",
  "top_k": 2
}
```

响应示例：

```json
{
  "question": "什么工具可以管理代码版本？",
  "count": 1,
  "data": [
    {
      "rank": 1,
      "source": "git.md",
      "chunk_id": 1,
      "content": "Git 是一个分布式版本控制系统。",
      "score": 0.63
    }
  ]
}
```

## 自动化测试

以下是原测试入口。现有测试导入main时会初始化数据库，须先使用隔离副本或专用测试数据库，避免操作开发数据：

```powershell
python -m pytest -v
```

旧README记录为36 passed，仅作历史记录。2026-10-16，本轮清理后的独立副本执行现有测试为44 passed；副本数据库隔离，禁用.env加载，模型构造和外部连接被阻断，模型/检索接口由原测试替身验证。这不代表真实检索或模型回答质量通过。

测试覆盖：

- 任务查询、创建和数据校验；
- 不存在资源的 404；
- 查询参数边界；
- 临时 SQLite 数据库隔离；
- 单轮和多轮 AI 问答；
- 模型未配置、连接失败和无效回答；
- RAG 正常回答和无资料兜底；
- 问题空白清理和 500 字符边界；
- 纯检索正常结果、空结果、默认 Top K 和范围校验；
- 检索服务不可用时返回 503。

自动化测试使用 `monkeypatch` 替换真实模型调用，因此不会下载或加载 Embedding 模型，不会占用 GPU，也不会调用付费大模型 API。

## 当前限制

- 任务数据库仍直接使用 `sqlite3`，尚未接入 ORM；
- 文档向量只缓存在当前进程内，重启后需要重新生成；
- 尚未使用向量数据库；
- 切块策略和相似度阈值仍是练习级固定配置；
- 尚未实现用户注册、登录、JWT 和知识库权限隔离；
- 尚未加入重排序、检索评测、日志、限流和缓存；
- 尚未进行 Docker 化和生产环境部署。

## 后续计划

1. 学习 SQLAlchemy 或 SQLModel，把任务数据访问迁移到 ORM；
2. 拆分 `routers`、`schemas`、`services` 和配置模块；
3. 持久化文档向量并接入向量数据库；
4. 增加检索评测、重排序和结构化引用；
5. 增加身份认证、日志、Docker 和部署说明。
