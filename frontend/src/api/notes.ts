import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface Note {
    id: string;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
}

export interface CreateNoteData {
    title: string;
    content: string;
}

export interface GenerateResponse {
    response: string;
    sources: Array<{
        content: string;
        metadata: {
            note_id: string;
            title: string;
        };
    }>;
}

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const notesApi = {
    createNote: async (data: CreateNoteData): Promise<Note> => {
        const response = await api.post<Note>('/notes/', data);
        return response.data;
    },

    getNotes: async (): Promise<Note[]> => {
        const response = await api.get<Note[]>('/notes/');
        return response.data;
    },

    deleteNote: async (noteId: string): Promise<void> => {
        await api.delete(`/notes/${noteId}`);
    },

    generateResponse: async (query: string): Promise<GenerateResponse> => {
        const response = await api.post<GenerateResponse>('/notes/generate', null, {
            params: { query }
        });
        return response.data;
    },
}; 