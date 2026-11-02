# 技术资料知识库

这是一个单用户可用的 FastAPI + Vue 3 RAG 知识库。用户可以自定义资料分类、导入和删除 Markdown 资料，并基于已登记资料进行语义检索、问答和引用核对。项目同时保留原有的任务管理和大模型练习接口。

## P0 功能

- 自定义分类：列表、新建、改名、删除；删除普通分类时，其资料自动移入“未分类”。
- 资料管理：导入 Markdown、按分类列表、查看正文、移动分类、删除正文与元数据。
- 数据持久化：MySQL 保存分类和资料元数据，Markdown 正文保存在本地目录。
- 重启恢复：启动时检查资料正文，并恢复删除事务遗留的暂存文件。
- RAG 问答：只读取 MySQL 已登记的资料；资料变动后在下一次检索时重建内存索引。
- 引用核对：问答结果返回来源文件、文本块编号和原始片段，前端可跳转查看资料原文。
- 三个前端页面：知识问答、资料管理、资料详情。

## 技术栈

- Python 3.12、FastAPI、Pydantic 2
- SQLAlchemy 2、MySQL 8、PyMySQL
- Sentence Transformers、PyTorch、本地 Embedding 模型
- OpenAI 兼容接口（当前配置为 DeepSeek）
- Vue 3、TypeScript、Vue Router、Vite
- pytest

## 目录结构

```text
FastAPIProject/
├── main.py                         # uvicorn 兼容入口
├── init_kb.py                      # 建表、默认分类、旧资料登记与恢复检查
├── app/
│   ├── main.py                     # FastAPI 应用、路由和启动恢复
│   ├── api/
│   │   ├── category_api.py         # 分类接口
│   │   ├── document_api.py         # 资料接口
│   │   ├── rag_api.py              # 检索与 RAG 接口
│   │   ├── chat_api.py             # 大模型问答接口
│   │   └── task_api.py             # 原任务管理接口
│   ├── core/                       # 数据库、路径校验和共享状态
│   ├── models/kb_models.py         # Category、Document ORM
│   ├── schemas/kb_schemas.py       # 分类和资料请求/响应模型
│   └── services/                   # 分类、资料、检索和模型业务
├── frontend/src/
│   ├── api/knowledge.ts
│   ├── router/index.ts
│   ├── types/
│   └── views/
├── practice/documents/             # 默认 Markdown 正文目录
├── tests/test_kb_p0.py             # P0 隔离业务测试
├── tests/test_main.py              # 原接口回归测试
├── requirements.txt
└── .env.example
```

## 首次配置

创建并激活虚拟环境，然后安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

已有虚拟环境无需重复创建。Windows/NVIDIA GPU环境在基础依赖安装后，再选择CUDA构建：

```powershell
python -m pip install --no-deps -r requirements-cuda.txt
python -m pip check
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

本机已验证 `2.14.1+cu126 / 12.6 / True`。CPU环境跳过CUDA安装；不要用IDE的普通批量升级替换GPU构建。CUDA源与版本固定在 `requirements-cuda.txt`，官方轮子入口：https://download.pytorch.org/whl/cu126/torch/。

复制环境变量示例：

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

在 `.env` 中填写以下配置。不要把真实密钥或密码提交到 Git：

```dotenv
LLM_API_KEY=你的DeepSeek密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
EMBEDDING_MODEL_PATH=你的本地Embedding模型绝对路径
RAG_CHUNK_SIZE=400
RAG_CHUNK_OVERLAP=80

DB_USER=knowledge_app
DB_PASSWORD=你的MySQL密码
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=knowledge_base
```

`KB_DOCUMENTS_DIR` 是可选项；默认目录为 `practice/documents`。如果填写，必须使用绝对路径。

`RAG_CHUNK_SIZE`和`RAG_CHUNK_OVERLAP`控制字符切块。默认400/80适合当前短篇学习资料；资料量或内容结构变化后，应结合检索评测再调整。

MySQL 数据库和账号准备完成后，在项目根执行初始化：

```powershell
python .\init_kb.py
```

脚本会幂等创建表和默认“未分类”，登记正文目录中尚未登记的 `.md` 文件，并检查暂存恢复状态。重复执行不会重复插入同一资料。

## 启动

先确认MySQL80服务为Running；若Stopped，由本人在管理员PowerShell执行 `Start-Service -Name MySQL80`。`WinError 10061`优先检查数据库服务和端口。

启动后端（项目根、已激活虚拟环境）：

```powershell
python -m uvicorn app.main:app --reload
```

另开终端启动前端：

```powershell
Set-Location .\frontend
# 仅首次或锁文件变化后安装依赖：npm.cmd ci
npm.cmd run dev
```

访问地址：

- 前端：<http://localhost:5173/>
- Swagger：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

第一次提问会加载Embedding模型并构建内存索引；同一进程内后续问题复用索引。资料增删后，下次检索重新构建。终端会显示：

```text
RAG索引重建完成：chunks=..., chunk_size=..., overlap=..., device=cuda:0, elapsed=...s
RAG问答完成：sources=..., retrieval=...s, generation=...s, total=...s
```

`retrieval`首次包含索引初始化，`generation`是外部模型等待时间。切块量减少不等于检索质量自动提升；更换参数后需用真实问题核对引用。

## 知识库接口

| 方法 | 路径 | 作用 |
|---|---|---|
| `GET` | `/categories` | 查询分类及资料数量 |
| `POST` | `/categories` | 新建分类 |
| `PATCH` | `/categories/{category_id}` | 修改分类名称 |
| `DELETE` | `/categories/{category_id}` | 删除普通分类并迁移资料 |
| `GET` | `/documents` | 查询资料，可传 `category_id` |
| `POST` | `/documents` | 导入 Markdown 资料 |
| `GET` | `/documents/{source}` | 查看资料正文 |
| `PATCH` | `/documents/{source}/category` | 移动资料分类 |
| `DELETE` | `/documents/{source}` | 删除资料元数据和正文 |
| `POST` | `/ai/retrieve` | 返回相关文本块，不调用大模型 |
| `POST` | `/ai/rag` | 返回知识库回答和引用片段 |

导入资料示例：

```json
{
  "source": "fastapi-notes.md",
  "content": "# FastAPI\n\n这里是资料正文。",
  "category_id": null
}
```

`category_id` 为 `null` 时资料进入“未分类”。文件名必须是单层、小写 `.md` 文件名，正文不能为空且最多 20000 字符。

## 验证

前端类型检查和生产构建：

```powershell
Set-Location .\frontend
npm run build
```

P0与旧接口回归统一使用隔离入口：

```powershell
# 在项目根且已激活.venv时运行
python .\scripts\check_kb.py
```

脚本仅复制Python源码和测试到临时目录，不复制开发`.env`、数据库或正文；使用临时SQLite与正文目录，阻断真实MySQL、Embedding模型加载和外部请求。旧接口导入时会初始化`tasks.db`，因此日常请使用此入口，避免在开发数据上直接执行旧测试。自动化使用替身，不代替真实模型质量与MySQL验证。

## 演示与验收

1. 新建“演示分类”，导入一份自行编写的Markdown，正文含唯一事实。
2. 在知识问答中提问，核回答、来源片段及“查看原文”一致。
3. 移动该资料；删除其普通分类时，资料应进入“未分类”。
4. 重启后端，确认分类、正文与归属保留；首次提问会重新加载模型和索引。
5. 删除刚创建的演示资料，确认列表、正文与新检索不再包含它。

2026-10-29：本人已确认分类增改删、资料导入/移动/删除、引用打开原文和重启保留全部通过；此前真实问答截图与CUDA验证已留证。性能秒数以终端实测为准，尚无规模压测结论。临时`p0-acceptance.md`是本地验收资料，提交代码时单独排除；如需清理，从页面删除以保持数据库与文件一致，不直接删文件。

## 当前边界

- 当前按单用户、单个 FastAPI 进程设计；不要使用多个 worker 并发修改资料。
- 文档向量保存在进程内，进程重启或资料变化后按需重建。
- 尚未实现登录、权限、多知识库、向量数据库、异步任务、Docker 和生产部署。
- 原任务管理仍使用 SQLite `tasks.db`，与知识库 MySQL 数据分开。
