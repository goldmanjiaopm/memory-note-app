import React from 'react';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
    TextInput,
    Button,
    Stack,
    Paper,
    Text,
    Title,
    Alert,
    Box,
    Collapse,
    Group,
    Badge,
} from '@mantine/core';
import { IconSearch, IconBrain, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { notesApi, GenerateResponse } from '../api/notes';

export function QueryNotes() {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState<GenerateResponse | null>(null);
    const [showSources, setShowSources] = useState(false);

    const mutation = useMutation({
        mutationFn: notesApi.generateResponse,
        onSuccess: (data) => {
            setResponse(data);
            setShowSources(false);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        mutation.mutate(query);
    };

    return (
        <Paper>
            <Stack gap="md">
                <Title order={2}>Query Notes</Title>
                <Text size="sm" c="dimmed">
                    Ask questions about your notes using AI
                </Text>

                <form onSubmit={handleSubmit}>
                    <Stack gap="md">
                        <TextInput
                            required
                            label="Your Question"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g., What did I write about machine learning?"
                            size="md"
                            leftSection={<IconBrain size={16} />}
                        />
                        <Button
                            type="submit"
                            loading={mutation.isPending}
                            disabled={!query}
                            leftSection={<IconSearch size={16} />}
                            size="md"
                        >
                            Search Notes
                        </Button>
                    </Stack>
                </form>

                {response && (
                    <Box mt="md">
                        <Alert
                            color="indigo"
                            variant="light"
                            radius="md"
                        >
                            <Text size="md" style={{ lineHeight: 1.6 }}>
                                {response.response}
                            </Text>
                        </Alert>

                        {response.sources.length > 0 && (
                            <Paper withBorder mt="md" radius="md" p="md">
                                <Button
                                    variant="subtle"
                                    color="gray"
                                    fullWidth
                                    onClick={() => setShowSources(!showSources)}
                                    rightSection={
                                        showSources ? (
                                            <IconChevronUp size={16} />
                                        ) : (
                                            <IconChevronDown size={16} />
                                        )
                                    }
                                >
                                    {showSources ? 'Hide Sources' : 'Show Sources'}
                                </Button>
                                <Collapse in={showSources}>
                                    <Stack gap="md" mt="md">
                                        {response.sources.map((source, index) => (
                                            <Paper
                                                key={index}
                                                withBorder
                                                p="sm"
                                                radius="sm"
                                            >
                                                <Group justify="space-between" mb="xs">
                                                    <Badge size="sm" variant="light">
                                                        {source.metadata.title}
                                                    </Badge>
                                                </Group>
                                                <Text size="sm" c="dimmed">
                                                    {source.content}
                                                </Text>
                                            </Paper>
                                        ))}
                                    </Stack>
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