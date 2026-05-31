const EXAMPLES = [
  'What happened with Maya?',
  'How did the job offer feel?',
  'When did I sound happiest?',
  'What was I worried about with money?',
];

export default function Examples({ onPick, disabled }) {
  return (
    <div className="mx-auto mt-10 max-w-reading">
      <div className="flex items-center gap-3">
        <div className="quiet-divider" />
        <span className="ui-label">try asking</span>
        <div className="quiet-divider" />
      </div>

      <ul className="mt-5 grid gap-2 sm:grid-cols-2">
        {EXAMPLES.map((q) => (
          <li key={q}>
            <button
              type="button"
              onClick={() => onPick(q)}
              disabled={disabled}
              className={
                'group w-full rounded-lg border border-paper-200 bg-paper-100/40 ' +
                'px-4 py-3 text-left font-serif text-[15px] italic text-ink-700 ' +
                'transition hover:border-accent/30 hover:bg-paper-100 hover:text-ink-900 ' +
                'disabled:cursor-not-allowed disabled:opacity-50'
              }
            >
              <span className="mr-2 text-accent/60 transition group-hover:text-accent">“</span>
              {q}
              <span className="ml-1 text-accent/60 transition group-hover:text-accent">”</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
