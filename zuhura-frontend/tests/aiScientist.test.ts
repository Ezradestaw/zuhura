import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAIStore } from '../src/store/aiStore';

const context = { lat: 18.38, lon: 77.58, alt: 50000, activeLayers: ['mola'] };

describe('Assistant store', () => {
  beforeEach(async () => {
    vi.restoreAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    await useAIStore.getState().clearConversation();
  });

  it('starts closed with a single welcome message', () => {
    const state = useAIStore.getState();
    expect(state.isOpen).toBe(false);
    expect(state.isQuerying).toBe(false);
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].sender).toBe('assistant');
  });

  it('toggles the panel', () => {
    const { toggleOpen } = useAIStore.getState();
    const initial = useAIStore.getState().isOpen;
    toggleOpen();
    expect(useAIStore.getState().isOpen).toBe(!initial);
    toggleOpen();
    expect(useAIStore.getState().isOpen).toBe(initial);
  });

  it('sends the question with map context and shows the answer and sources', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        answer: 'The crater floor is about -2,600 m.',
        citations: [{ dataset_id: 'zuhura-mola-megdr-128', title: 'MOLA MEGDR', provider: 'NASA PDS', url: 'https://pds-geosciences.wustl.edu/' }],
      }),
    });
    global.fetch = fetchMock;

    await useAIStore.getState().sendQuery('Elevation here?', context);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/ai/chat');
    const body = JSON.parse(init.body);
    expect(body.prompt).toBe('Elevation here?');
    expect(body.map_context.camera_lat).toBe(18.38);

    const messages = useAIStore.getState().messages;
    const answer = messages[messages.length - 1];
    expect(answer.text).toContain('-2,600 m');
    expect(answer.citations?.[0].dataset_id).toBe('zuhura-mola-megdr-128');
    expect(answer.isError).toBeFalsy();
    expect(useAIStore.getState().isQuerying).toBe(false);
  });

  it('shows the server explanation when the assistant is unavailable, without inventing an answer', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'The assistant is not configured. Set GEMINI_API_KEY on the server to enable it.' }),
    });

    await useAIStore.getState().sendQuery('Elevation here?', context);

    const messages = useAIStore.getState().messages;
    const answer = messages[messages.length - 1];
    expect(answer.isError).toBe(true);
    expect(answer.text).toContain('GEMINI_API_KEY');
    expect(answer.citations).toBeUndefined();
  });

  it('reports a network failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('offline'));

    await useAIStore.getState().sendQuery('Hello', context);

    const messages = useAIStore.getState().messages;
    expect(messages[messages.length - 1].isError).toBe(true);
  });

  it('clears the conversation back to the welcome message', async () => {
    await useAIStore.getState().sendQuery('Hello', context);
    await useAIStore.getState().clearConversation();
    expect(useAIStore.getState().messages).toHaveLength(1);
  });
});
