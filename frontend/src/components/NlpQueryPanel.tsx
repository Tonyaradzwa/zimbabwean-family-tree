import { useState } from 'react'
import type { FormEvent } from 'react'
import { runQuery } from '../api/client'
import type { QueryResponse } from '../types'

const EXAMPLE_QUERIES = [
  "Who is Chipo to Tendai?",
  "Who is John's sekuru?",
  "Who is Mary to Tinashe's sister?",
]

export default function NlpQueryPanel() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QueryResponse | null>(null)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      setError('Please enter a question first.')
      setResult(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await runQuery({ query: trimmedQuery })
      setResult(response)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Query failed.'
      setError(message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="nlp-query-panel">
      <form className="nlp-query-form" onSubmit={onSubmit}>
        <label htmlFor="nlp-query-input">Ask a family relationship question</label>
        <textarea
          id="nlp-query-input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g. who is Tariro to Nyasha's mother?"
          rows={4}
        />

        <div className="nlp-query-actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Running query...' : 'Run query'}
          </button>
          <button
            type="button"
            className="secondary"
            disabled={loading}
            onClick={() => {
              setQuery('')
              setResult(null)
              setError(null)
            }}
          >
            Clear
          </button>
        </div>
      </form>

      <div className="nlp-query-examples">
        <h3>Try an example</h3>
        <div className="nlp-chip-list">
          {EXAMPLE_QUERIES.map((sample) => (
            <button
              key={sample}
              type="button"
              className="secondary nlp-chip"
              onClick={() => setQuery(sample)}
              disabled={loading}
            >
              {sample}
            </button>
          ))}
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      {!error && !result ? (
        <p className="tree-canvas__status">No query submitted yet.</p>
      ) : null}

      {result ? (
        <section className="nlp-query-result" aria-live="polite">
          <h3>Result</h3>
          <p>{result.answer}</p>
          <dl>
            <dt>Question</dt>
            <dd>{result.query}</dd>
            {result.subject_name ? (
              <>
                <dt>Subject</dt>
                <dd>
                  {result.subject_name}
                  {result.subject_id ? ` (ID: ${result.subject_id})` : ''}
                </dd>
              </>
            ) : null}
            {result.relationship_asked ? (
              <>
                <dt>Relationship Asked</dt>
                <dd>{result.relationship_asked}</dd>
              </>
            ) : null}
          </dl>
        </section>
      ) : null}
    </div>
  )
}