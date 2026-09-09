import sqlite3
from pathlib import Path

db_path = Path(__file__).with_name("sqlite_practice.db")

connection = sqlite3.connect(db_path)
connection.row_factory=sqlite3.Row

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

task_id = 1111

cursor = connection.execute(
    """
    SELECT id, title, done
    FROM tasks
    WHERE id = ?
    """,
    (task_id,),
)

row = cursor.fetchone()

if row is None:
    print("任务不存在")
else:
    print("查询结果为：",dict(row))



connection.close()