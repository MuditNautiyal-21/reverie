const BASE_URL =
  (import.meta.env && import.meta.env.VITE_API_BASE_URL) || 'http://127.0.0.1:8000';

export async function askQuestion(question, { topK = 5, signal } = {}) {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
    signal,
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  return res.json();
}
