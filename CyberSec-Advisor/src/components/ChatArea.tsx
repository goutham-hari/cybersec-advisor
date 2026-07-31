import { Bot } from "lucide-react";
import { useEffect, useRef } from "react";
import Message from "./Message";

type Source = {
  book: string;
  page: number | string;
};

type ChatMessage = {
  id: string;
  role: "system" | "user" | "assistant" | "error";
  text: string;
  sources?: Source[];
};

type ChatAreaProps = {
  messages: ChatMessage[];
  isLoading: boolean;
};

export default function ChatArea({ messages, isLoading }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  return (
    <main className="flex min-h-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 md:px-8">
      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4">
        {messages.length === 1 && messages[0].role === "system" ? (
          <div className="mb-3 rounded-2xl border border-slate-800 bg-slate-900/60 px-5 py-6 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-cyan-500/20">
              <Bot className="text-cyan-300" size={30} />
            </div>
            <h1 className="text-2xl font-bold text-white sm:text-3xl">CyberSec Advisor</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400 sm:text-base">
              Ask technical cybersecurity questions and get answers grounded in your ingested books.
            </p>
          </div>
        ) : null}

        {messages.map((message) => (
          <Message
            key={message.id}
            role={message.role}
            text={message.text}
            sources={message.sources}
          />
        ))}

        {isLoading ? <Message role="system" text="thinking..." /> : null}
        <div ref={bottomRef} />
      </div>
    </main>
  );
}