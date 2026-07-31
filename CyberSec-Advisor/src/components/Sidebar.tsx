import { MessageSquare, Plus, Settings, Shield } from "lucide-react";

type SidebarProps = {
  onNewChat: () => Promise<void>;
  isBusy: boolean;
};

export default function Sidebar({ onNewChat, isBusy }: SidebarProps) {
  return (
    <aside className="hidden w-72 flex-col border-r border-slate-800 bg-slate-900 lg:flex">
      <div className="flex items-center gap-3 border-b border-slate-800 p-5">
        <div className="rounded-xl bg-cyan-500 p-2">
          <Shield size={22} />
        </div>

        <div>
          <h1 className="text-xl font-bold text-white">CyberSec Advisor</h1>
          <p className="text-xs text-slate-400">AI Security Assistant</p>
        </div>
      </div>

      <div className="p-4">
        <button
          onClick={() => {
            void onNewChat();
          }}
          disabled={isBusy}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 py-3 font-semibold transition hover:bg-cyan-600 disabled:cursor-not-allowed disabled:bg-slate-700"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      <nav className="space-y-2 px-3">
        <button className="flex w-full items-center gap-3 rounded-xl bg-slate-800/90 px-4 py-3 transition">
          <MessageSquare size={18} />
          Chats
        </button>
      </nav>

      <div className="flex-1 px-4 pt-6">
        <p className="mb-3 text-sm text-slate-400">Suggested prompts</p>

        <div className="space-y-2">
          {["OWASP Top 10", "SQL Injection", "Zero Trust Architecture"].map((chat) => (
            <div
              key={chat}
              className="rounded-lg bg-slate-800 p-3 text-sm transition hover:bg-slate-700"
            >
              {chat}
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-slate-800 p-4">
        <button className="flex w-full items-center gap-3 rounded-xl px-4 py-3 transition hover:bg-slate-800">
          <Settings size={18} />
          Local Mode
        </button>
      </div>
    </aside>
  );
}
