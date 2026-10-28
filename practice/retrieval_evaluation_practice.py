from app.services.rag_service import search_chunks

evaluation_cases = [
    {
        "question": "什么工具可以管理代码版本？",
        "expected_source": "git.md",
        "answerable": True,
    },
    {
        "question": "FastAPI 的作用是什么？",
        "expected_source": "fastapi.md",
        "answerable": True,
    },
    {
        "question": "文档中介绍的轻量级关系型数据库是什么？",
        "expected_source": "sqlite.md",
        "answerable": True,
    },
    {
        "question": "如何制作巧克力蛋糕？",
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "什么工具可以通过分支让不同功能独立开发？",
        "expected_source": "git.md",
        "answerable": True,
    },
    {
        "question": "哪个Python框架能够自动生成接口文档？",
        "expected_source": "fastapi.md",
        "answerable": True,
    },
    {
        "question": "轻量数据库和其他数据库的区别",
        "expected_source": "sqlite.md",
        "answerable": False,
    },
    {
        "question": "Python 列表应该怎样排序？",
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "MySQL 应该怎样创建索引？",
        "expected_source": None,
        "answerable": False,
    },
    {
        "question": "开发 Python API 可以使用什么 Web 框架？",
        "expected_source": "fastapi.md",
        "answerable": True,
    },
    {
        "question": "怎么使用github仓库管理代码",
        "expected_source": "git.md",
        "answerable": False,
    },
    {
        "question": "想留下一次代码改动的记录，应该使用什么操作？",
        "expected_source": "git.md",
        "answerable": True,
    },
    {
        "question": "Git 中如何撤销最近一次提交？",
        "expected_source": "git.md",
        "answerable": False,
    },
    {
        "question": "FastAPI 支持哪些开发能力？",
        "expected_source": "fastapi.md",
        "answerable": True,
    },
    {
        "question": "SQLite 如何创建索引？",
        "expected_source": "sqlite.md",
        "answerable": False,
    },
    {
        "question": "如何养护多肉植物？",
        "expected_source": None,
        "answerable": False,
    },
]


def evaluate_cases(
        cases: list[dict],
        top_k: int = 2,
        min_score: float = 0.5,
) -> None:
    hit_count = 0
    answer_total = 0
    answer_hit = 0
    no_answer_total = 0
    no_answer_correct = 0
    answerable_total = 0
    answerable_hit = 0
    related_no_answer_total = 0
    related_no_answer_hit = 0

    for case in cases:
        question = case["question"]
        expected_source = case["expected_source"]
        answerable = case["answerable"]

        if expected_source is None:
            case_type = "无相关资料"
        elif answerable:
            case_type = "有相关资料，足以回答"
        else:
            case_type = "有相关资料，但不足以回答"

        search_results = search_chunks(
            question,
            top_k=top_k,
            min_score=min_score,
        )

        actual_sources = []

        for result in search_results:
            actual_sources.append(result["source"])

        if expected_source is None:
            no_answer_total += 1
            is_hit = len(actual_sources) == 0
            if is_hit:
                no_answer_correct += 1
        else:
            answer_total += 1
            is_hit = expected_source in actual_sources
            if is_hit:
                answer_hit += 1

            if answerable:
                answerable_total += 1
                if is_hit:
                    answerable_hit += 1
            else:
                related_no_answer_total += 1
                if is_hit:
                    related_no_answer_hit += 1

        if is_hit:
            hit_count += is_hit

        print("问题：", question)
        print("题型：", case_type)
        print("预期来源：", expected_source)
        print("实际来源：", actual_sources)
        print("是否命中：", is_hit)
        print("-" * 30)

    total_count = len(cases)

    if total_count == 0:
        hit_rate = 0.0
    else:
        hit_rate = hit_count / total_count

    print(
        f"{top_k}:"
        f"{hit_count}/{total_count} "
        f"({hit_rate:.2%})"
    )
    print(f"有预期相关来源的题，来源命中：{answer_hit}/{answer_total}")
    print(f"无相关来源的题，正确返回空：{no_answer_correct}/{no_answer_total}")
    print(f"资料足够题的来源命中：{answerable_hit}/{answerable_total}")
    print(f"相关但不足题的来源命中：{related_no_answer_hit}/{related_no_answer_total}")


if __name__ == "__main__":
    evaluate_cases(
        evaluation_cases,
        top_k=2,
        min_score=0.5
    )
    debug_questions = [
        "怎么使用github仓库管理代码",
        "怎么使用 GitHub 仓库管理代码？",
    ]

    for debug_question in debug_questions:
        debug_results = search_chunks(
            question=debug_question,
            top_k=3,
            min_score=0,
        )

        print("调试问题：", debug_question)

        for result in debug_results:
            print(
                result["source"],
                result["chunk_id"],
                result["score"],
            )

        print("-" * 20)
