import { useEffect, useRef, useState } from 'react';

// Pixel height above which the input is considered multiline. Below this,
// the submit button sits vertically centered; above, it pins to the bottom.
const SINGLE_LINE_THRESHOLD = 64;

export default function AskBox({ value, onChange, onSubmit, disabled }) {
  const taRef = useRef(null);
  const [multiline, setMultiline] = useState(false);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const next = Math.min(el.scrollHeight, 240);
    el.style.height = `${next}px`;
    setMultiline(next > SINGLE_LINE_THRESHOLD);
  }, [value]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  }

  return (
    <form
      className="mx-auto max-w-reading"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim() && !disabled) onSubmit();
      }}
    >
      <div
        className={
          'group relative flex items-center rounded-xl border border-paper-200 bg-paper-100/70 shadow-[0_1px_0_rgba(0,0,0,0.02)] ' +
          'transition focus-within:border-accent/40 focus-within:shadow-[0_2px_24px_-12px_rgba(138,58,47,0.35)]'
        }
      >
        <textarea
          ref={taRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your memories…"
          rows={1}
          className={
            'no-scrollbar w-full resize-none bg-transparent px-5 py-4 pr-28 ' +
            'font-serif text-lg leading-relaxed text-ink-900 placeholder:text-ink-400 ' +
            'focus:outline-none'
          }
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className={
            'absolute right-2.5 rounded-md px-3.5 py-1.5 ' +
            'font-sans text-xs uppercase tracking-wide2 ' +
            'border border-accent/30 text-accent ' +
            'transition hover:bg-accent hover:text-paper-50 ' +
            'disabled:cursor-not-allowed disabled:border-paper-200 disabled:text-ink-400 disabled:hover:bg-transparent ' +
            (multiline ? 'bottom-2.5' : 'top-1/2 -translate-y-1/2')
          }
        >
          {disabled ? 'reading' : 'ask'}
        </button>
      </div>
      <p className="ui-label mt-2 px-1">Press enter to ask. Shift + enter for a new line.</p>
    </form>
  );
}
