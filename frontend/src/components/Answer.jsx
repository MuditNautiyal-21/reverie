export default function Answer({ text }) {
  if (!text) return null;
  // Split on blank lines so multi-paragraph answers breathe.
  const paragraphs = text.split(/\n\s*\n/).filter(Boolean);

  return (
    <section className="mx-auto mt-12 max-w-reading animate-fade-up">
      <div className="flex items-center gap-3">
        <div className="quiet-divider" />
        <span className="ui-label">what i found</span>
        <div className="quiet-divider" />
      </div>

      <div className="mt-6 space-y-5">
        {paragraphs.map((p, i) => (
          <p
            key={i}
            className="font-serif text-[20px] leading-[1.7] text-ink-900 first-letter:text-accent first-letter:font-medium"
            style={i === 0 ? undefined : { textIndent: 0 }}
          >
            {p}
          </p>
        ))}
      </div>
    </section>
  );
}
