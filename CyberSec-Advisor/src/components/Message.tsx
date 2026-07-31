type Source = {
	book: string;
	page: number | string;
};

type MessageProps = {
	role: "system" | "user" | "assistant" | "error";
	text: string;
	sources?: Source[];
};

const LABEL_BY_ROLE: Record<MessageProps["role"], string> = {
	system: "system",
	user: "you",
	assistant: "advisor",
	error: "error",
};

const CONTAINER_BY_ROLE: Record<MessageProps["role"], string> = {
	system: "border-slate-800 bg-slate-900/70",
	user: "border-cyan-500/40 bg-cyan-500/10",
	assistant: "border-slate-800 bg-slate-900/90",
	error: "border-rose-500/40 bg-rose-500/10",
};

const LABEL_COLOR_BY_ROLE: Record<MessageProps["role"], string> = {
	system: "text-slate-400",
	user: "text-cyan-200",
	assistant: "text-emerald-300",
	error: "text-rose-300",
};

export default function Message({ role, text, sources }: MessageProps) {
	return (
		<article className={`rounded-2xl border p-4 sm:p-5 ${CONTAINER_BY_ROLE[role]}`}>
			<p className={`text-xs font-semibold uppercase tracking-[0.18em] ${LABEL_COLOR_BY_ROLE[role]}`}>
				{LABEL_BY_ROLE[role]}
			</p>

			<p className="mt-3 whitespace-pre-wrap leading-7 text-slate-100">{text}</p>

			{sources && sources.length > 0 ? (
				<div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-300">
					<span className="text-slate-400">Sources:</span>
					{sources.map((source, index) => (
						<span
							key={`${source.book}-${source.page}-${index}`}
							className="rounded-full border border-slate-700 bg-slate-950/60 px-3 py-1"
						>
							{source.book} p.{String(source.page)}
						</span>
					))}
				</div>
			) : null}
		</article>
	);
}
