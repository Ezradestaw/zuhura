import React, { useEffect, useRef, useState } from 'react';
import { ExternalLink, Loader2, MessageSquare, RotateCcw, Send, X } from 'lucide-react';
import { useAIStore, type ChatMessage } from '../store/aiStore';
import { useGlobeStore } from '../store/globeStore';
import { useLayerStore } from '../store/layerStore';

const EVIDENCE_TAGS = 'MEASURED|OBSERVED|INTERPRETED|HYPOTHESIS|LIMITATION|UNAVAILABLE|DERIVED';
const EVIDENCE_TAG = new RegExp(`^\`?\\[(${EVIDENCE_TAGS})\\]\`?$`);
const INLINE_PATTERN = new RegExp(`(\`?\\[(?:${EVIDENCE_TAGS})\\]\`?|\`[^\`]+\`|\\*\\*[^*]+\\*\\*)`, 'g');

function renderInline(text: string): React.ReactNode[] {
  return text.split(INLINE_PATTERN).map((part, i) => {
    if (!part) return null;
    const tag = part.match(EVIDENCE_TAG);
    if (tag) {
      return (
        <span key={i} className="mr-1 text-[10px] font-medium uppercase text-ink-muted">
          {tag[1].toLowerCase()}
        </span>
      );
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="rounded bg-surface-muted px-1 font-mono text-[12px]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

/** Removes LaTeX wrappers the model occasionally emits, e.g. "$-1,731\\text{ m}$" -> "-1,731 m". */
function stripLatex(text: string): string {
  return text
    .replace(/\\text\{([^}]*)\}/g, '$1')
    .replace(/\\(pm|approx|times|circ|deg)\b/g, (_, cmd: string) => ({ pm: '±', approx: '≈', times: '×', circ: '°', deg: '°' })[cmd] ?? '')
    .replace(/\$([^$\n]+)\$/g, '$1');
}

function renderMarkdown(text: string): React.ReactNode {
  return stripLatex(text).split('\n').map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={i} className="h-2" />;
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) return null;
    const heading = trimmed.match(/^#{1,4}\s+(.*)$/);
    if (heading) {
      return (
        <p key={i} className="pt-1 font-semibold">
          {renderInline(heading[1])}
        </p>
      );
    }
    const bullet = trimmed.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      return (
        <div key={i} className="flex gap-2 pl-1">
          <span aria-hidden="true">•</span>
          <span>{renderInline(bullet[1])}</span>
        </div>
      );
    }
    return <p key={i}>{renderInline(trimmed)}</p>;
  });
}

const Message: React.FC<{ message: ChatMessage }> = ({ message }) => {
  if (message.sender === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-lg rounded-br-sm bg-brand-700 px-3 py-2 text-sm text-white">
          {message.text}
        </div>
      </div>
    );
  }

  if (message.isPending) {
    return (
      <div className="flex items-center gap-2 text-sm text-ink-muted">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        Thinking…
      </div>
    );
  }

  return (
    <div className={`space-y-1 text-sm leading-relaxed ${message.isError ? 'text-danger' : 'text-ink'}`}>
      {renderMarkdown(message.text)}
      {message.citations && message.citations.length > 0 && (
        <div className="mt-2 border-t border-line pt-2">
          <p className="mb-1 text-xs font-medium text-ink-muted">Sources</p>
          <ul className="space-y-0.5">
            {message.citations.map((c) => (
              <li key={c.dataset_id}>
                <a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline"
                >
                  {c.title}
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export const AIPanel: React.FC = () => {
  const { isOpen, toggleOpen, messages, isQuerying, sendQuery, clearConversation } = useAIStore();
  const { cameraLat, cameraLon, cameraAlt } = useGlobeStore();
  const { layers } = useLayerStore();
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!isOpen) return null;

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || isQuerying) return;
    setInput('');
    sendQuery(prompt, {
      lat: cameraLat,
      lon: cameraLon,
      alt: cameraAlt,
      activeLayers: layers.filter((l) => l.visible).map((l) => l.id),
    });
  };

  return (
    <section
      className="fixed right-4 top-16 z-[25] flex h-[calc(100vh-80px)] w-[400px] max-w-[calc(100vw-32px)] flex-col overflow-hidden rounded-lg border border-line bg-white font-sans text-ink shadow-panel"
      aria-label="Ask Zuhura"
    >
      <header className="flex items-center justify-between bg-brand-700 px-4 py-2.5 text-white">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <MessageSquare className="h-4 w-4 text-accent" aria-hidden="true" />
          Ask Zuhura
        </h2>
        <div className="flex items-center gap-0.5 text-brand-100">
          <button
            type="button"
            onClick={() => clearConversation()}
            title="New conversation"
            aria-label="New conversation"
            className="rounded p-1.5 transition-colors hover:bg-brand-600 hover:text-white"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={toggleOpen}
            title="Close"
            aria-label="Close"
            className="rounded p-1.5 transition-colors hover:bg-brand-600 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="flex items-center gap-2 border-t border-line p-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question"
          aria-label="Question"
          className="flex-1 rounded border border-line-strong px-3 py-2 text-sm placeholder-ink-faint focus:border-brand-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || isQuerying}
          aria-label="Send"
          className="rounded bg-brand-700 p-2 text-white transition-colors hover:bg-brand-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </section>
  );
};
