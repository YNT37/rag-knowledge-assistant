from fastapi.testclient import TestClient
from openai import APIConnectionError
from  httpx2 import Request

from main import app
import llm_service

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