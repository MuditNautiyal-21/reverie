import { formatLong } from '../util/date.js';

export default function Citations({ items }) {
  if (!items || items.length === 0) return null;

  return (
    <section className="mx-auto mt-14 max-w-reading animate-fade-up">
      <div className="flex items-center gap-3">
        <div className="quiet-divider" />
        <span className="ui-label">from your journal</span>
        <div className="quiet-divider" />
      </div>

      <ul className="mt-6 space-y-4">
        {items.map((c) => (
          <li
            key={c.id}
            className="rounded-lg border border-paper-200 bg-paper-100/60 p-5 transition hover:border-paper-300"
          >
            <div className="mb-2 flex items-baseline justify-between gap-3">
              <time className="font-sans text-xs uppercase tracking-wide2 text-ink-500">
                {formatLong(c.date)}
              </time>
              <span className="font-sans text-[11px] italic text-ink-400">
                {c.mood}
              </span>
            </div>
            <p className="font-serif text-[15.5px] leading-[1.7] text-ink-700 whitespace-pre-wrap">
              {c.text}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
