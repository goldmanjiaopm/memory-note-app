import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Grid, Paper, Stack, Title, Group, Badge, Text, Button } from '@mantine/core';
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { notesApi } from '../api/notes';
import { NoteCard } from './NoteCard';

function LoadingSkeleton() {
    return (
        <Stack gap="xl">
            <Title order={2}>Loading...</Title>
            <Grid>
                {Array(4).fill(0).map((_, i) => (
                    <Grid.Col key={i} span={6}>
                        <Paper p="xl" withBorder>
                            <Stack gap="md">
                                <Title order={3}>Loading...</Title>
                                <Text>Loading content...</Text>
                            </Stack>
                        </Paper>
                    </Grid.Col>
                ))}
            </Grid>
        </Stack>
    );
}

export function NoteList() {
    const [showAll, setShowAll] = useState(false);

    const { data: notes, isLoading, error } = useQuery({
        queryKey: ['notes'],
        queryFn: notesApi.getNotes
    });

    if (isLoading) return <LoadingSkeleton />;
    if (error) {
        console.error('Error details:', error);
        return (
            <Paper>
                <Stack gap="md">
                    <Text c="red">Error loading notes</Text>
                    <Text size="sm" c="dimmed">
                        {error instanceof Error ? error.message : 'Unknown error occurred'}
                    </Text>
                </Stack>
            </Paper>
        );
    }
    if (!notes?.length) {
        return (
            <Paper style={{ textAlign: 'center', padding: '2rem' }}>
                <Text c="dimmed" size="lg">
                    No notes found. Create your first note to get started!
                </Text>
            </Paper>
        );
    }

    const displayedNotes = showAll ? notes : notes.slice(0, 6);
    const hasMoreNotes = notes.length > 6;

    const toggleShowAll = () => setShowAll(!showAll);

    return (
        <Paper>
            <Stack gap="xl">
                <Group justify="space-between">
                    <Title order={2}>Your Notes</Title>
                    <Badge size="lg" variant="light">
                        {notes.length} {notes.length === 1 ? 'Note' : 'Notes'}
                    </Badge>
                </Group>

                <Grid>
                    {displayedNotes.map((note) => (
                        <Grid.Col key={note.id} span={6}>
                            <NoteCard note={note} />
                        </Grid.Col>
                    ))}
                </Grid>

                {hasMoreNotes && (
                    <Button
                        variant="subtle"
                        color="gray"
                        onClick={toggleShowAll}
                        rightSection={showAll ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                        fullWidth
                    >
                        {showAll ? 'Show Less' : `Show ${notes.length - 6} More Notes...`}
                    </Button>
                )}
            </Stack>
        </Paper>
    );
} 