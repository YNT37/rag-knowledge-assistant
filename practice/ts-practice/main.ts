type RagStatus = {
    question: string;
    answer: string;
    loading: boolean;
}

const textStatus: RagStatus = {
    question: "什么是数据库？",
    answer: "",
    loading: false
}

function textfun(status: RagStatus): boolean {
    return status.loading;
}

const text = textfun(textStatus);

const array: RagStatus[] = [
    textStatus,
    {
        question: "111",
        answer: "",
        loading: false
    }
];

let more: string | null = null;
more = "11111";

function text2(m: string | null): string {
    if (m === null) {
        return "暂无回答";
    } else {
        return m;
    }
}

type QuestionRecord = {
    question: string;
    answer?: string;
};

const first: QuestionRecord = {
    question: "什么是数据库？"
};

const second: QuestionRecord = {
    question: "什么是事务？",
    answer: "事务是一组按整体处理的操作。"
};

const records: QuestionRecord[] = [
    first,
    second
];

function response(q: QuestionRecord): string {
    if (q.answer === undefined) {
        return "暂无回答";
    } else {
        return q.answer
    }
}

let f = response(first);
let s = response(second);

const record: QuestionRecord = {
    question: "11111",
    answer: ""
}

let r = response(record);


let data: unknown = "回答已生成";


function TextKnown(known: unknown): string {
    if (typeof known === "string") {
        return known;
    }

    return "回答格式错误";
}

function getAnswer(data: unknown): string {
    if (typeof data === "object" && data !== null && "answer" in data && typeof data.answer === "string") {
        return data.answer;
    }

    return "回答格式错误";

}

async function getAnswerAsync(data: unknown): Promise<string> {
    return getAnswer(data);
}

async function getAnswerLength(data: unknown): Promise<number> {
    const answer = await getAnswerAsync(data);
    return answer.length;
}

async function testAnswerLength(): Promise<number> {
    const len = await getAnswerLength({ answer: 200 });
    console.log(len);
    return len;
}

testAnswerLength();