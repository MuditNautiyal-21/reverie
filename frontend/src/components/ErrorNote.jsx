export default function ErrorNote({ message }) {
  if (!message) return null;
  return (
    <div className="mx-auto mt-10 max-w-reading">
      <div className="rounded-lg border border-accent/30 bg-accent/5 px-5 py-4">
        <p className="ui-label text-accent">something went wrong</p>
        <p className="mt-1 font-serif italic text-ink-700">{message}</p>
      </div>
    </div>
  );
}
