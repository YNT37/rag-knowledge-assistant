export type RagSource = {
    source: string;
    chunk_id: number;
    content: string;
}

type RagResponse = {
    answer: string;
    sources: RagSource[];
}


function getAnswer(data: unknown): string {
    if (typeof data === "object" && data !== null && "answer" in data && typeof data.answer === "string") {
        return data.answer;
    }

    return "回答格式错误";

}


export async function requestAnswer(question: string): Promise<string> {

    const requestData = {"question": question};

    const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(requestData),
    };

    const response = await fetch("http://localhost:8000/ai/rag", requestOptions);

    if (response.ok) {
        const responseData: unknown = await response.json();
        return getAnswer(responseData);

    } else {
        return "请求失败";
    }
}

function getRagSource(data: unknown): RagSource | null {
    if (typeof data === "object" && data !== null && "source" in data && typeof data.source === "string"
        && "chunk_id" in data && typeof data.chunk_id === "number"
        && "content" in data && typeof data.content === "string"
    ) {
        return {
            source: data.source,
            chunk_id: data.chunk_id,
            content: data.content,
        };
    }
    return null;
}

function getRagSources(data: unknown): RagSource[] | null {
    const sources: RagSource[] = [];
    if (Array.isArray(data)) {
        for (const item of data) {
            const source = getRagSource(item);
            if (source) {
                sources.push(source);
            } else {
                return null;
            }
        }
        return sources;
    }
    return null;
}

function getRagResponse(data: unknown): RagResponse | null {
    if (typeof data === "object" && data !== null && "answer" in data && typeof data.answer === "string" && "sources" in data) {
        const sources = getRagSources(data.sources);

        if (sources === null) {
            return null;
        }

        return {
            answer: data.answer,
            sources: sources,
        }
    }
    return null;
}

export async function requestRagResponse(
    question: string
): Promise<RagResponse | string> {
    const requestData = {question: question};
    const requestOptions = {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(requestData),
    }
    const response = await fetch("http://localhost:8000/ai/rag", requestOptions);
    if (response.ok) {
        const responseData: unknown = await response.json();
        const result = getRagResponse(responseData);
        if (result === null) {
            return "回答格式错误"
        }
        return result
    }

    return "请求失败"
}

