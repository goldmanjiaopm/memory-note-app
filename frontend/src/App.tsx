import { Container, Stack } from "@mantine/core";
import { CreateNote } from "./components/CreateNote";
import { NoteList } from "./components/NoteList";
import { QueryNotes } from "./components/QueryNotes";

function App() {
  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        <CreateNote />
        <NoteList />
        <QueryNotes />
      </Stack>
    </Container>
  );
}

export default App;
