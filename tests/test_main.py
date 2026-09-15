from fastapi.testclient import TestClient
from openai import APIConnectionError
from  httpx2 import Request

from main import app
import llm_service
import database


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}

def test_get_missing_task():
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}

def test_get_tasks_returns_list():
    response = client.get("/tasks")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)

def test_search_rejects_invalid_limit():
    response = client.get(
        "/search",
        params={"limit": 0},
    )

    assert response.status_code == 422

def test_create_task_rejects_empty_title():
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "done": False,
        }
    )

    assert response.status_code == 422

def test_ai_ask_rejects_empty_question():
    response = client.post(
        "/ai/ask",
        json={
            "question": "",
        }
    )

    assert response.status_code == 422

def test_ai_ask_returns_model_answer(monkeypatch):
    def fake_ask_llm(question:str):
        assert question == "什么是请求体？"
        return "模拟回答"

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "模拟回答"}

def test_ai_ask_returns_503_when_ask_fails(monkeypatch):
    def fake_ask_llm(question:str):
        raise APIConnectionError(
            request=Request("post", "https://example.invalid")
        )

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "模型服务暂不可用"}

def test_ai_ask_returns_502_when_response_is_none(monkeypatch):
    def fake_ask_llm(question:str):
        return None

    monkeypatch.setattr(llm_service, "ask_llm", fake_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}

def test_ai_ask_returns_502_when_response_is_empty(monkeypatch):
    def fask_ask_llm(question:str):
        return ""

    monkeypatch.setattr(llm_service, "ask_llm", fask_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}

def test_ai_ask_returns_502_when_response_is_whitespace(monkeypatch):
    def fask_ask_llm(question:str):
        return "   "

    monkeypatch.setattr(llm_service, "ask_llm", fask_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型未返回有效回答"}


def test_ai_ask_returns_503_when_api_key_is_missing(monkeypatch):
    def fask_ask_llm(question:str):
        return "模拟回答"

    monkeypatch.setattr(llm_service, "api_key", None )
    monkeypatch.setattr(llm_service, "ask_llm", fask_ask_llm)

    response = client.post(
        "/ai/ask",
        json={"question": "什么是请求体？"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "模型服务未配置"}


def test_database_uses_temporary_file(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks_test.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)

    database.init_db()

    assert test_db.exists()
    assert database.get_all_tasks() == []


def test_ai_chat_sends_history_and_current_question(monkeypatch):
    monkeypatch.setattr(llm_service, "api_key", "test_key")
    monkeypatch.setattr(llm_service, "base_url", "https://example.invalid")
    monkeypatch.setattr(llm_service, "model", "test_model")

    def fask_ask_llm(messages):
        assert messages == [
            {"role": "system", "content": "你是一名耐心的 Python 老师。"},
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "FastAPI 是后端框架"},
            {"role": "user", "content": "它能做什么？"},
        ]

        return "它可以编写后端 API"

    monkeypatch.setattr(llm_service, "ask_chat", fask_ask_llm)

    response = client.post(
        "/ai/chat",
        json={
            "question": "它能做什么？",
            "history": [
                {"role": "user", "content": "我正在学习 FastAPI"},
                {"role": "assistant", "content": "FastAPI 是后端框架"},
            ],
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "它可以编写后端 API",
        "history": [
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "FastAPI 是后端框架"},
            {"role": "user", "content": "它能做什么？"},
            {"role": "assistant", "content": "它可以编写后端 API"},
        ]
    }

def test_ai_chat_works_without_history(monkeypatch):
    monkeypatch.setattr(llm_service, "api_key", "test_key")
    monkeypatch.setattr(llm_service, "base_url", "https://example.invalid")
    monkeypatch.setattr(llm_service, "model", "test_model")

    def fask_ask_llm(messages):
        assert messages == [
                {"role": "system", "content": "你是一名耐心的 Python 老师。"},
                {"role": "user", "content": "我正在学习 FastAPI"},
        ]

        return "欢迎学习 FastAPI"

    monkeypatch.setattr(llm_service, "ask_chat", fask_ask_llm)

    response = client.post(
        "/ai/chat",
        json = {"question": "我正在学习 FastAPI"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "欢迎学习 FastAPI",
        "history": [
            {"role": "user", "content": "我正在学习 FastAPI"},
            {"role": "assistant", "content": "欢迎学习 FastAPI"},
        ]
    }