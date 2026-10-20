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

console.log(f);
console.log(s);