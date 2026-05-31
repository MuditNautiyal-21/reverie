const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function parseISO(iso) {
  if (!iso || typeof iso !== 'string') return null;
  const [y, m, d] = iso.split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

export function formatLong(iso) {
  const d = parseISO(iso);
  if (!d) return iso;
  return `${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
}

export function formatShort(iso) {
  const d = parseISO(iso);
  if (!d) return iso;
  return `${MONTHS[d.getMonth()].slice(0, 3)} ${d.getDate()}`;
}
