import { useMemo, useState } from "react";
import ChatArea from "./components/ChatArea";
import ChatInput from "./components/ChatInput";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

type Source = {
  book: string;
  page: number | string;
};

type Message = {
  id: string;
  role: "system" | "user" | "assistant" | "error";
  text: string;
  sources?: Source[];
};

type AskResponse = {
  answer: string;
  sources: Source[];
};

type ErrorResponse = {
  error?: string;
};

const INITIAL_MESSAGE: Message = {
  id: "system-ready",
  role: "system",
  text:
    "Ready. Ask about offensive tradecraft, defensive operations, architecture, or secure development. Answers are grounded in your ingested book library where relevant, with citations.",
};

function createMessage(role: Message["role"], text: string, sources?: Source[]): Message {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    sources,
  };
}

function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);

  const canSend = useMemo(() => !isLoading, [isLoading]);

  const sendQuestion = async (question: string) => {
    setMessages((prev) => [...prev, createMessage("user", question)]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const errorPayload = (await response.json()) as ErrorResponse;
        setMessages((prev) => [
          ...prev,
          createMessage("error", errorPayload.error || "Something went wrong."),
        ]);
        return;
      }

      const payload = (await response.json()) as AskResponse;
      setMessages((prev) => [
        ...prev,
        createMessage("assistant", payload.answer, payload.sources),
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      setMessages((prev) => [
        ...prev,
        createMessage("error", `Could not reach the server: ${message}`),
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    setIsLoading(true);
    try {
      await fetch("/api/reset", { method: "POST" });
    } catch {
      // Even if reset fails, we still clear UI state for a fresh chat view.
    } finally {
      setMessages([
        createMessage("system", "New conversation started. Previous context has been cleared."),
      ]);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-slate-950 text-slate-100">
      <Sidebar onNewChat={resetConversation} isBusy={isLoading} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar isBusy={isLoading} />
        <ChatArea messages={messages} isLoading={isLoading} />
        <ChatInput onSend={sendQuestion} canSend={canSend} />
      </div>
    </div>
  );
}

export default App;
