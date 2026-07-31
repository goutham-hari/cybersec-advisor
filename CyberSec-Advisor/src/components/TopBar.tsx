type TopBarProps = {
  isBusy: boolean;
};

export default function TopBar({ isBusy }: TopBarProps) {
  return (
    <header className="border-b border-slate-800 bg-slate-950 px-4 py-4 sm:px-6 md:px-8">
      <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white sm:text-xl">AI Cyber Security Assistant</h2>
          <p className="mt-1 text-sm text-slate-400">Grounded answers from your local knowledge base.</p>
        </div>

        <div className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300">
          <span className={`mr-2 inline-block h-2 w-2 rounded-full ${isBusy ? "bg-amber-400" : "bg-emerald-400"}`} />
          {isBusy ? "thinking" : "ready"}
        </div>
      </div>
    </header>
  );
}