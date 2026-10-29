import {createWebHistory, createRouter} from "vue-router";

import QuestionView from '@/views/QuestionView.vue'
import DocumentsView from '@/views/DocumentsView.vue'
import DocumentDetailView from '@/views/DocumentDetailView.vue'

const router = createRouter({
    history: createWebHistory('/'),
    routes: [
        {path: '/', name: 'question', component: QuestionView},
        {path: '/documents', name: 'documents', component: DocumentsView},
        {path: '/documents/:source', name: 'document-detail', component: DocumentDetailView},
    ]
})

export default router
