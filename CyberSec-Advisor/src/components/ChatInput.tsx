import { Send } from "lucide-react";
import { useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";

type ChatInputProps = {
  onSend: (question: string) => Promise<void>;
  canSend: boolean;
};

export default function ChatInput({ onSend, canSend }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !canSend) {
      return;
    }

    setQuestion("");
    await onSend(trimmed);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-slate-800 bg-slate-950 px-4 py-4 sm:px-6 md:px-8">
      <div className="mx-auto flex w-full max-w-4xl items-end gap-3 rounded-2xl border border-slate-700 bg-slate-900 p-3 shadow-lg">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Ask a technical cybersecurity question..."
          className="max-h-40 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-white placeholder-slate-500 outline-none"
          disabled={!canSend}
        />

        <button
          type="submit"
          className="rounded-xl bg-cyan-500 p-3 transition hover:bg-cyan-600 disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={!canSend || !question.trim()}
          aria-label="Send question"
        >
          <Send size={18} />
        </button>
      </div>
    </form>
  );
}
