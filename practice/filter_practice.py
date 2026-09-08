tasks = [
    {"id": 1, "title": "Python 学习任务", "done": False},
    {"id": 2, "title": "Redis", "done": False},
    {"id": 3, "title": "Python 练习任务", "done": False},
]


def task_filter(tasks: list[dict], keyword: str) -> list[dict]:
    result = []

    for task in tasks:
        if keyword.lower() in task["title"].lower():
            result.append(task)

    return result


if __name__ == "__main__":
    print("搜索 Python：", task_filter(tasks, "python"))
    print("搜索 Redis：", task_filter(tasks, "redis"))
    print("搜索空字符串：", task_filter(tasks, ""))
