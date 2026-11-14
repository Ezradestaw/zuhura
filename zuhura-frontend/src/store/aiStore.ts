import { create } from 'zustand';

const API_BASE = import.meta.env.VITE_API_URL || '';

export interface Citation {
  dataset_id: string;
  title: string;
  provider: string;
  instrument?: string;
  mission?: string;
  spatial_resolution?: string;
  url: string;
  doi?: string | null;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  isPending?: boolean;
  isError?: boolean;
}

export interface MapContext {
  lat: number;
  lon: number;
  alt: number;
  activeLayers: string[];
}

interface AIState {
  sessionId: string;
  messages: ChatMessage[];
  isQuerying: boolean;
  isOpen: boolean;
  toggleOpen: () => void;
  setIsOpen: (open: boolean) => void;
  sendQuery: (prompt: string, context?: MapContext) => Promise<void>;
  clearConversation: () => Promise<void>;
}

const WELCOME: ChatMessage = {
  id: 'welcome',
  sender: 'assistant',
  text: 'Ask a question about Mars or about the area you are viewing. Answers list the datasets they are based on.',
};

const newSessionId = () => `session-${Math.random().toString(36).slice(2, 9)}`;

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') return body.detail;
  } catch {
    // Body was not JSON.
  }
  return `The assistant could not answer (HTTP ${response.status}).`;
}

export const useAIStore = create<AIState>((set, get) => ({
  sessionId: newSessionId(),
  messages: [WELCOME],
  isQuerying: false,
  isOpen: false,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setIsOpen: (open) => set({ isOpen: open }),

  sendQuery: async (prompt, context) => {
    const id = Date.now().toString(36);
    const pendingId = `assistant-${id}`;

    set((state) => ({
      isQuerying: true,
      messages: [
        ...state.messages,
        { id: `user-${id}`, sender: 'user', text: prompt },
        { id: pendingId, sender: 'assistant', text: '', isPending: true },
      ],
    }));

    const resolve = (update: Partial<ChatMessage>) =>
      set((state) => ({
        isQuerying: false,
        messages: state.messages.map((m) => (m.id === pendingId ? { ...m, ...update, isPending: false } : m)),
      }));

    try {
      const response = await fetch(`${API_BASE}/api/v1/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          session_id: get().sessionId,
          map_context: context && {
            camera_lat: context.lat,
            camera_lon: context.lon,
            camera_altitude_m: context.alt,
            active_layers: context.activeLayers,
          },
        }),
      });

      if (!response.ok) {
        resolve({ text: await readErrorMessage(response), isError: true });
        return;
      }

      const data = await response.json();
      resolve({ text: data.answer ?? '', citations: data.citations ?? [] });
    } catch {
      resolve({ text: 'The assistant could not be reached. Check that the backend is running.', isError: true });
    }
  },

  clearConversation: async () => {
    const { sessionId } = get();
    try {
      await fetch(`${API_BASE}/api/v1/ai/conversations/${sessionId}`, { method: 'DELETE' });
    } catch {
      // The session may not exist on the server yet.
    }
    set({ sessionId: newSessionId(), messages: [WELCOME], isQuerying: false });
  },
}));
