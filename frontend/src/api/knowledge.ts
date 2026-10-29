import type {
  CategoryItem,
  CategoryList,
  DocumentCreateInput,
  DocumentDetail,
  DocumentItem,
  DocumentList,
} from '@/types/knowledge'


const API_BASE = 'http://localhost:8000'


function errorDetail(data: unknown, status: number): string {
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    if (typeof data.detail === 'string' && data.detail.trim() !== '') {
      return data.detail
    }
    if (Array.isArray(data.detail)) {
      const messages = data.detail.flatMap(item => {
        if (
          typeof item === 'object' &&
          item !== null &&
          'msg' in item &&
          typeof item.msg === 'string'
        ) {
          return [item.msg]
        }
        return []
      })
      if (messages.length > 0) return messages.join('；')
    }
  }
  return `请求失败（${status}）`
}


async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options)
  let data: unknown
  try {
    data = await response.json()
  } catch {
    throw new Error(`服务器返回了无法解析的响应（${response.status}）`)
  }
  if (!response.ok) {
    throw new Error(errorDetail(data, response.status))
  }
  return data as T
}


function jsonOptions(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  }
}


export function getCategories(): Promise<CategoryList> {
  return requestJson<CategoryList>('/categories')
}


export function createCategory(name: string): Promise<CategoryItem> {
  return requestJson<CategoryItem>('/categories', jsonOptions('POST', {name}))
}


export function renameCategory(id: number, name: string): Promise<CategoryItem> {
  return requestJson<CategoryItem>(
    `/categories/${id}`,
    jsonOptions('PATCH', {name}),
  )
}


export function deleteCategory(id: number): Promise<void> {
  return requestJson<void>(`/categories/${id}`, {method: 'DELETE'})
}


export function getDocuments(categoryId: number | null = null): Promise<DocumentList> {
  const query = categoryId === null ? '' : `?category_id=${categoryId}`
  return requestJson<DocumentList>(`/documents${query}`)
}


export function createDocument(input: DocumentCreateInput): Promise<DocumentItem> {
  return requestJson<DocumentItem>('/documents', jsonOptions('POST', input))
}


export function moveDocument(source: string, categoryId: number): Promise<DocumentItem> {
  return requestJson<DocumentItem>(
    `/documents/${encodeURIComponent(source)}/category`,
    jsonOptions('PATCH', {category_id: categoryId}),
  )
}


export function deleteDocument(source: string): Promise<void> {
  return requestJson<void>(`/documents/${encodeURIComponent(source)}`, {
    method: 'DELETE',
  })
}


export function getDocument(source: string): Promise<DocumentDetail> {
  return requestJson<DocumentDetail>(`/documents/${encodeURIComponent(source)}`)
}
