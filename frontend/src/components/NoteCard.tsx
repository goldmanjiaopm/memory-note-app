import React from 'react';
import { Card, Text, Title, Group, ActionIcon, Modal, Button, Stack } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconTrash } from '@tabler/icons-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Note, notesApi } from '../api/notes';

interface NoteCardProps {
    note: Note;
}

export function NoteCard({ note }: NoteCardProps) {
    const [opened, { open, close }] = useDisclosure(false);
    const queryClient = useQueryClient();

    const deleteMutation = useMutation({
        mutationFn: notesApi.deleteNote,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['notes'] });
            close();
        },
    });

    const handleDelete = () => {
        deleteMutation.mutate(note.id);
    };

    return (
        <>
            <Card shadow="sm" p="lg" radius="md" withBorder>
                <Group justify="space-between" mb="xs">
                    <Title order={3} size="h4">
                        {note.title}
                    </Title>
                    <ActionIcon
                        color="red"
                        variant="subtle"
                        onClick={open}
                        disabled={deleteMutation.isPending}
                    >
                        <IconTrash size={18} />
                    </ActionIcon>
                </Group>
                <Text lineClamp={3} c="dimmed" size="sm">
                    {note.content}
                </Text>
            </Card>

            <Modal
                opened={opened}
                onClose={close}
                title="Delete Note"
                centered
                size="sm"
            >
                <Stack gap="md">
                    <Text size="sm">
                        Are you sure you want to delete "{note.title}"? This action cannot be undone.
                    </Text>
                    <Group justify="flex-end">
                        <Button variant="default" onClick={close} disabled={deleteMutation.isPending}>
                            Cancel
                        </Button>
                        <Button
                            color="red"
                            onClick={handleDelete}
                            loading={deleteMutation.isPending}
                        >
                            Delete
                        </Button>
                    </Group>
                </Stack>
            </Modal>
        </>
    );
} 