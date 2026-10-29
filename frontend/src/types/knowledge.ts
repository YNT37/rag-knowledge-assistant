export type CategoryItem = {
  id: number
  name: string
  is_default: boolean
  document_count: number
}

export type CategoryList = {
  count: number
  data: CategoryItem[]
}

export type DocumentItem = {
  id: number
  source: string
  category_id: number
  category_name: string
}

export type DocumentList = {
  count: number
  data: DocumentItem[]
}

export type DocumentDetail = DocumentItem & {
  content: string
  char_count: number
}

export type DocumentCreateInput = {
  source: string
  content: string
  category_id: number | null
}
