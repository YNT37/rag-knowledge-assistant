import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("tasks.db")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.commit()
    connection.close()


def get_all_tasks() -> list[dict]:
    connection = get_connection()

    cursor = connection.execute(
        """
        SELECT id,title,done FROM tasks
        """
    )
    rows = cursor.fetchall()
    connection.close()

    tasks = []
    for row in rows:
        task = dict(row)
        task["done"] = bool(task["done"])
        tasks.append(task)

    return tasks

def create_task(title: str, done: bool =False) -> dict:
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO tasks (title, done) VALUES (?, ?)
        """
        , (title, done),
    )

    connection.commit()

    new_task = {
        "id": cursor.lastrowid,
        "title": title,
        "done": done,
    }

    connection.close()

    return new_task


def get_task_by_id(task_id: int) -> dict:
    connection = get_connection()
    cursor = connection.execute(
        """
        SELECT * FROM tasks WHERE id = ?
        """
        ,(task_id,),
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    task = dict(row)
    task["done"] = bool(task["done"])

    return task


def update_task(task_id: int, title: str, done: bool) -> None:
    connection = get_connection()
    cursor = connection.execute(
        """
        UPDATE tasks SET title = ?, done = ? WHERE id =?
        """
        ,(title,done,task_id),
    )

    connection.commit()
    task

init_db()


