import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database.database import Base, get_db

# Banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override da dependência de banco
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Criação e destruição das tabelas entre os testes
@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_todo():
    response = client.post("/todos/", json={
        "title": "Fazer testes",
        "description": "Criar testes com pytest",
        "status": "pending"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Fazer testes"
    assert data["description"] == "Criar testes com pytest"
    assert data["status"] == "pending"
    assert "id" in data

def test_read_todos():
    client.post("/todos/", json={"title": "Tarefa 1", "description": "descrição 1","status": "pending"})
    client.post("/todos/", json={"title": "Tarefa 2", "status": "done"})
    response = client.get("/todos/")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 2
    assert todos[0]["title"] == "Tarefa 1"
    assert todos[1]["title"] == "Tarefa 2"
    assert todos[0]["status"] == "pending"
    assert todos[1]["status"] == "done"
    assert todos[0]["description"] == "descrição 1" 
    assert todos[1]["description"] is None


def test_read_single_todo():
    res = client.post("/todos/", json={"title": "Ver tarefa", "status": "pending"})
    todo_id = res.json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Ver tarefa"

def test_update_todo():
    res = client.post("/todos/", json={"title": "Original", "status": "pending"})
    todo_id = res.json()["id"]
    update = client.put(f"/todos/{todo_id}", json={"title": "Atualizada", "status": "done"})
    assert update.status_code == 200
    assert update.json()["title"] == "Atualizada"
    assert update.json()["status"] == "done"

def test_delete_todo():
    res = client.post("/todos/", json={"title": "Para deletar", "status": "pending"})
    todo_id = res.json()["id"]
    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"detail": "Todo deleted"}

    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404



