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