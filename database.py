import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).with_name("tasks.db")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row) -> dict:
    task = dict(row)
    task["done"] = bool(task["done"])
    return task


def init_db() -> None:
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        SELECT id, title, done
        FROM tasks
        ORDER BY id
        """
    )
    rows = cursor.fetchall()
    connection.close()

    tasks = []
    for row in rows:
        tasks.append(row_to_dict(row))

    return tasks


def get_task_by_id(task_id: int) -> dict | None:
    connection = get_connection()
    cursor = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    task = row_to_dict(row)
    return task


def create_task(title: str, done: bool = False) -> dict:
    connection = get_connection()
    cursor = connection.execute(
        """
        INSERT INTO tasks (title, done)
        VALUES (?, ?)
        """,
        (title, done),
    )

    connection.commit()
    task_id = cursor.lastrowid
    connection.close()

    return get_task_by_id(task_id)


def update_task(task_id: int, title: str, done: bool) -> dict | None:
    connection = get_connection()
    cursor = connection.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (title, done, task_id),
    )
    connection.commit()
    updated_row = cursor.rowcount
    connection.close()
    if updated_row == 0:
        return None
    task = get_task_by_id(task_id)
    return task


def update_task_partial(
    task_id: int,
    title: str | None = None,
    done: bool | None = None,
) -> dict | None:
    task = get_task_by_id(task_id)
    if task is None:
        return None
    if title is None:
        title = task["title"]
    if done is None:
        done = task["done"]
    return update_task(task_id, title, done)


def delete_task(task_id: int) -> dict | None:
    task = get_task_by_id(task_id)
    if task is None:
        return None
    connection = get_connection()
    connection.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )
    connection.commit()
    connection.close()
    return task


def search_tasks(keyword: str, skip: int, limit: int) -> list[dict]:
    connection = get_connection()
    cursor = connection.execute(
        """
        SELECT id, title, done
        FROM tasks
        WHERE title LIKE ?
        ORDER BY id
        LIMIT ?
        OFFSET ?
        """,
        (f"%{keyword}%", limit, skip),
    )
    rows = cursor.fetchall()
    connection.close()

    tasks = []
    for row in rows:
        tasks.append(row_to_dict(row))

    return tasks
if __name__ == "__main__":
    init_db()
    print(get_all_tasks())

