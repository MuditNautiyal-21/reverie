import { useCallback, useRef, useState } from 'react';
import Header from './components/Header.jsx';
import AskBox from './components/AskBox.jsx';
import Examples from './components/Examples.jsx';
import Loading from './components/Loading.jsx';
import Answer from './components/Answer.jsx';
import Citations from './components/Citations.jsx';
import ErrorNote from './components/ErrorNote.jsx';
import EmptyAnswer from './components/EmptyAnswer.jsx';
import { askQuestion } from './api.js';

export default function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [asked, setAsked] = useState(false);

  const inflight = useRef(null);

  const submit = useCallback(async (textOverride) => {
    const q = (textOverride ?? question).trim();
    if (!q) return;

    if (inflight.current) inflight.current.abort();
    const ctrl = new AbortController();
    inflight.current = ctrl;

    setError('');
    setResult(null);
    setLoading(true);
    setAsked(true);

    try {
      const data = await askQuestion(q, { signal: ctrl.signal });
      setResult(data);
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError(err.message || 'Could not reach the journal.');
    } finally {
      if (inflight.current === ctrl) inflight.current = null;
      setLoading(false);
    }
  }, [question]);

  function pickExample(q) {
    setQuestion(q);
    submit(q);
  }

  const showInitial = !asked && !loading && !result && !error;
  const showEmpty = result && (!result.answer || result.answer.trim() === '');

  return (
    <div className="min-h-screen pb-24">
      <Header />

      <main className="px-5">
        <AskBox
          value={question}
          onChange={setQuestion}
          onSubmit={() => submit()}
          disabled={loading}
        />

        {showInitial && <Examples onPick={pickExample} disabled={loading} />}

        {loading && <Loading />}
        {error && <ErrorNote message={error} />}

        {!loading && !error && result && !showEmpty && (
          <>
            <Answer text={result.answer} />
            <Citations items={result.citations} />
          </>
        )}

        {!loading && !error && showEmpty && <EmptyAnswer />}
      </main>

      <footer className="mt-20 text-center">
        <p className="ui-label">a synthetic journal · answered with care</p>
      </footer>
    </div>
  );
}
