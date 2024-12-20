# Frontend Setup Guide

## Step 1: Project Setup

1. Create a new Vite project:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
```

2. Install dependencies:
```bash
npm install @mantine/core @mantine/hooks @emotion/react @tabler/icons-react react-query axios
```

3. Create the following folder structure:
```
frontend/
├── src/
│   ├── components/
│   │   ├── CreateNote.tsx
│   │   ├── NoteList.tsx
│   │   ├── QueryNotes.tsx
│   │   └── NoteCard.tsx
│   ├── api/
│   │   └── notes.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
```

## Step 2: API Setup

Create `src/api/notes.ts`:
```typescript
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

export interface QueryResponse {
    answer: string;
    context: string;
    has_results: boolean;
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
    queryNotes: async (query: string): Promise<QueryResponse> => {
        const response = await api.post<QueryResponse>('/query/', { query });
        return response.data;
    },
};
```

## Step 3: Components

1. Create `src/components/CreateNote.tsx`:
```tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { TextInput, Button, Stack, Paper, Title, Textarea, Alert } from '@mantine/core';
import { notesApi, CreateNoteData } from '../api/notes';

export function CreateNote() {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const queryClient = useQueryClient();

    const mutation = useMutation(notesApi.createNote, {
        onSuccess: () => {
            queryClient.invalidateQueries('notes');
            setTitle('');
            setContent('');
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const noteData: CreateNoteData = { title, content };
        mutation.mutate(noteData);
    };

    return (
        <Paper>
            <form onSubmit={handleSubmit}>
                <Stack spacing="md">
                    <Title order={2}>Create Note</Title>
                    <TextInput
                        required
                        label="Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        size="md"
                    />
                    <Textarea
                        required
                        label="Content"
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        minRows={4}
                        size="md"
                    />
                    <Button
                        type="submit"
                        loading={mutation.isLoading}
                        disabled={!title || !content || mutation.isLoading}
                    >
                        Create Note
                    </Button>
                    {mutation.isError && (
                        <Alert color="red" title="Error" variant="filled">
                            Failed to create note. Please try again.
                        </Alert>
                    )}
                </Stack>
            </form>
        </Paper>
    );
}
```

2. Create `src/components/NoteCard.tsx`:
```tsx
import { Card, Text, Title } from '@mantine/core';
import { Note } from '../api/notes';

interface NoteCardProps {
    note: Note;
}

export function NoteCard({ note }: NoteCardProps) {
    return (
        <Card shadow="sm" p="lg" radius="md" withBorder>
            <Title order={3} size="h4" mb="md">
                {note.title}
            </Title>
            <Text lineClamp={3} color="dimmed" size="sm">
                {note.content}
            </Text>
        </Card>
    );
}
```

3. Create `src/components/NoteList.tsx`:
```tsx
import { useQuery } from 'react-query';
import { Grid, Paper, Stack, Title, Group, Badge, Text, Skeleton } from '@mantine/core';
import { notesApi } from '../api/notes';
import { NoteCard } from './NoteCard';

function LoadingSkeleton() {
    return (
        <Stack spacing="xl">
            <Skeleton height={30} width="30%" />
            <Grid>
                {Array(4).fill(0).map((_, i) => (
                    <Grid.Col key={i} span={6}>
                        <Skeleton height={200} radius="md" />
                    </Grid.Col>
                ))}
            </Grid>
        </Stack>
    );
}

export function NoteList() {
    const { data: notes, isLoading, error } = useQuery('notes', notesApi.getNotes);

    if (isLoading) return <LoadingSkeleton />;
    if (error) return <Text color="red">Error loading notes</Text>;
    if (!notes?.length) {
        return (
            <Paper sx={{ textAlign: 'center', padding: '2rem' }}>
                <Text color="dimmed" size="lg">
                    No notes found. Create your first note to get started!
                </Text>
            </Paper>
        );
    }

    return (
        <Paper>
            <Stack spacing="xl">
                <Group position="apart">
                    <Title order={2}>Your Notes</Title>
                    <Badge size="lg" variant="light">
                        {notes.length} {notes.length === 1 ? 'Note' : 'Notes'}
                    </Badge>
                </Group>
                <Grid>
                    {notes.map((note) => (
                        <Grid.Col key={note.id} span={6}>
                            <NoteCard note={note} />
                        </Grid.Col>
                    ))}
                </Grid>
            </Stack>
        </Paper>
    );
}
```

4. Create `src/components/QueryNotes.tsx`:
```tsx
import { useState } from 'react';
import { useMutation } from 'react-query';
import { TextInput, Button, Stack, Paper, Text, Code, Title, Alert, Box, Collapse } from '@mantine/core';
import { IconSearch, IconBrain, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { notesApi, QueryResponse } from '../api/notes';

export function QueryNotes() {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<QueryResponse | null>(null);
    const [showContext, setShowContext] = useState(false);

    const mutation = useMutation(notesApi.queryNotes, {
        onSuccess: (data) => {
            setResponse(data);
            setShowContext(false);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        mutation.mutate(query);
    };

    return (
        <Paper>
            <Stack spacing="md">
                <Title order={2}>Query Notes</Title>
                <Text size="sm" color="dimmed">
                    Ask questions about your notes using AI
                </Text>

                <form onSubmit={handleSubmit}>
                    <Stack spacing="md">
                        <TextInput
                            required
                            label="Your Question"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g., What did I write about machine learning?"
                            size="md"
                            icon={<IconBrain size={16} />}
                        />
                        <Button
                            type="submit"
                            loading={mutation.isLoading}
                            disabled={!query}
                            leftIcon={<IconSearch size={16} />}
                            size="md"
                        >
                            Search Notes
                        </Button>
                    </Stack>
                </form>

                {response && (
                    <Box mt="md">
                        <Alert
                            color={response.has_results ? 'indigo' : 'yellow'}
                            variant="light"
                            radius="md"
                        >
                            <Text size="md" sx={{ lineHeight: 1.6 }}>
                                {response.answer}
                            </Text>
                        </Alert>

                        {response.has_results && (
                            <Paper withBorder mt="md" radius="md" p="md">
                                <Button
                                    variant="subtle"
                                    color="gray"
                                    fullWidth
                                    onClick={() => setShowContext(!showContext)}
                                    rightIcon={
                                        showContext ? (
                                            <IconChevronUp size={16} />
                                        ) : (
                                            <IconChevronDown size={16} />
                                        )
                                    }
                                >
                                    {showContext ? 'Hide Context' : 'Show Context'}
                                </Button>
                                <Collapse in={showContext}>
                                    <Code block mt="sm">
                                        {response.context}
                                    </Code>
                                </Collapse>
                            </Paper>
                        )}
                    </Box>
                )}

                {mutation.isError && (
                    <Alert color="red" title="Error" variant="filled" mt="md">
                        Failed to query notes. Please try again.
                    </Alert>
                )}
            </Stack>
        </Paper>
    );
}
```

## Step 4: App Setup

1. Update `src/App.tsx`:
```tsx
import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from 'react-query';
import { CreateNote } from './components/CreateNote';
import { NoteList } from './components/NoteList';
import { QueryNotes } from './components/QueryNotes';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            staleTime: 5 * 60 * 1000,
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <MantineProvider
                withGlobalStyles
                withNormalizeCSS
                theme={{
                    colorScheme: 'light',
                    fontFamily: 'Inter, sans-serif',
                    headings: { fontFamily: 'Inter, sans-serif' },
                    primaryColor: 'indigo',
                    components: {
                        Paper: {
                            defaultProps: {
                                p: 'xl',
                                shadow: 'sm',
                                radius: 'md',
                                withBorder: true,
                            },
                        },
                        Button: {
                            defaultProps: {
                                radius: 'md',
                            },
                            styles: {
                                root: {
                                    fontWeight: 600,
                                },
                            },
                        },
                    },
                }}
            >
                <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
                    <Stack spacing="xl">
                        <CreateNote />
                        <Grid>
                            <Grid.Col span={8}>
                                <NoteList />
                            </Grid.Col>
                            <Grid.Col span={4}>
                                <QueryNotes />
                            </Grid.Col>
                        </Grid>
                    </Stack>
                </div>
            </MantineProvider>
        </QueryClientProvider>
    );
}

export default App;
```

2. Update `src/main.tsx`:
```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
```

## Step 5: Run the Application

1. Start the development server:
```bash
npm run dev
```

2. Open your browser and navigate to `http://localhost:5173`

The application should now be running with all the components and styling in place. 

# Frontend Technical Details

## Tech Stack

- **Framework**: React 18 with TypeScript
- **UI Library**: Mantine v6
- **State Management**: React Query
- **HTTP Client**: Axios
- **Icons**: Tabler Icons
- **Build Tool**: Vite

## Component Structure

### 1. App Layout
```tsx
<MantineProvider
    withGlobalStyles
    withNormalizeCSS
    theme={{
        colorScheme: 'light',
        fontFamily: 'Inter, sans-serif',
        headings: { fontFamily: 'Inter, sans-serif' },
        primaryColor: 'indigo',
        components: {
            Paper: {
                defaultProps: {
                    p: 'xl',
                    shadow: 'sm',
                    radius: 'md',
                    withBorder: true,
                }
            },
            Button: {
                defaultProps: {
                    radius: 'md',
                },
                styles: {
                    root: {
                        fontWeight: 600,
                    },
                },
            },
        },
    }}
>
    <QueryClientProvider client={queryClient}>
        <AppShell>
            {/* Components */}
        </AppShell>
    </QueryClientProvider>
</MantineProvider>
```

### 2. Components

#### CreateNote
```tsx
<Paper>
    <Stack spacing="md">
        <Title order={2}>Create Note</Title>
        <TextInput
            label="Title"
            required
            size="md"
        />
        <Textarea
            label="Content"
            required
            minRows={4}
            size="md"
        />
        <Button type="submit">
            Create Note
        </Button>
    </Stack>
</Paper>
```

#### NoteList
```tsx
<Paper>
    <Stack spacing="xl">
        <Group position="apart">
            <Title order={2}>Your Notes</Title>
            <Badge size="lg" variant="light">
                {notes.length} Notes
            </Badge>
        </Group>
        <Grid>
            {notes.map((note) => (
                <Grid.Col span={6}>
                    <NoteCard note={note} />
                </Grid.Col>
            ))}
        </Grid>
    </Stack>
</Paper>
```

#### QueryNotes
```tsx
<Paper>
    <Stack spacing="md">
        <Title order={2}>Query Notes</Title>
        <TextInput
            label="Your Question"
            required
            icon={<IconBrain />}
        />
        <Button leftIcon={<IconSearch />}>
            Search Notes
        </Button>
        {response && (
            <Alert variant="light" radius="md">
                <Text>{response.answer}</Text>
            </Alert>
        )}
        {response?.has_results && (
            <Paper withBorder>
                <Button variant="subtle" fullWidth>
                    Show Context
                </Button>
                <Collapse in={showContext}>
                    <Code block>
                        {response.context}
                    </Code>
                </Collapse>
            </Paper>
        )}
    </Stack>
</Paper>
```

## Styling Guidelines

### 1. Colors
- Primary: Indigo (`theme.colors.indigo`)
- Background: White
- Text: Dark Gray (`theme.colors.gray[8]`)
- Borders: Light Gray (`theme.colors.gray[3]`)

### 2. Typography
```css
/* Headings */
Title {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: theme.colors.gray[8]
}

/* Body Text */
Text {
    fontSize: '1rem',
    lineHeight: 1.6,
    color: theme.colors.gray[7]
}

/* Input Labels */
Label {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: theme.colors.gray[7]
}
```

### 3. Spacing
```css
/* Component Spacing */
Stack {
    spacing: 'md' /* 1rem */
}

/* Grid Layout */
Grid {
    gutter: 'xl' /* 2rem */
}

/* Padding */
Paper {
    padding: 'xl' /* 2rem */
}
```

### 4. Shadows and Borders
```css
Paper {
    shadow: 'sm',
    radius: 'md',
    border: '1px solid',
    borderColor: theme.colors.gray[2]
}
```

## State Management

### 1. React Query Configuration
```tsx
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            staleTime: 5 * 60 * 1000,
        },
    },
});
```

### 2. API Integration
```typescript
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
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
    queryNotes: async (query: string): Promise<QueryResponse> => {
        const response = await api.post<QueryResponse>('/query/', { query });
        return response.data;
    },
};
```

## Loading States

### 1. Skeleton Loading
```tsx
function LoadingSkeleton() {
    return (
        <Stack spacing="xl">
            <Skeleton height={30} width="30%" />
            <Grid>
                {Array(4).fill(0).map((_, i) => (
                    <Grid.Col key={i} span={6}>
                        <Skeleton height={200} radius="md" />
                    </Grid.Col>
                ))}
            </Grid>
        </Stack>
    );
}
```

### 2. Button Loading States
```tsx
<Button
    loading={mutation.isLoading}
    disabled={!formValid || mutation.isLoading}
>
    {mutation.isLoading ? 'Creating...' : 'Create Note'}
</Button>
```

## Error Handling

### 1. Error Display
```tsx
{mutation.isError && (
    <Alert
        color="red"
        title="Error"
        variant="filled"
    >
        Failed to create note. Please try again.
    </Alert>
)}
```

### 2. Form Validation
```tsx
const [errors, setErrors] = useState<Record<string, string>>({});

const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!title) newErrors.title = 'Title is required';
    if (!content) newErrors.content = 'Content is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
};
```

## Performance Optimizations

1. **Memoization**
```tsx
const MemoizedNoteCard = React.memo(NoteCard);
```

2. **Query Caching**
```tsx
const { data: notes } = useQuery('notes', notesApi.getNotes, {
    staleTime: 5 * 60 * 1000,
    cacheTime: 30 * 60 * 1000,
});
```

3. **Lazy Loading**
```tsx
const QueryNotes = React.lazy(() => import('./components/QueryNotes'));
```

## Responsive Design

```tsx
<Grid>
    <Grid.Col span={{ base: 12, sm: 6, lg: 4 }}>
        <NoteCard note={note} />
    </Grid.Col>
</Grid>

// Media Queries in Styles
sx={(theme) => ({
    padding: theme.spacing.md,
    [theme.fn.smallerThan('sm')]: {
        padding: theme.spacing.sm,
    },
})}
``` 