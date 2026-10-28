export type RagSource = {
    source: string;
    chunk_id: number;
    content: string;
}

export type RagResponse = {
    answer: string;
    sources: RagSource[];
}
