import React from 'react';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TextInput, Button, Stack, Paper, Title, Textarea, Alert } from '@mantine/core';
import { notesApi, CreateNoteData } from '../api/notes';

export function CreateNote() {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: notesApi.createNote,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notes'] });
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
                <Stack gap="md">
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
                        loading={mutation.isPending}
                        disabled={!title || !content || mutation.isPending}
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