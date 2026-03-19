import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createIndividual,
  deleteIndividual,
  listIndividuals,
  updateIndividual,
} from '../api/client'
import type { Individual, IndividualCreate } from '../types'

type FormState = {
  name: string
  gender: string
  birth_date: string
}

const EMPTY_FORM: FormState = {
  name: '',
  gender: 'female',
  birth_date: '',
}

export default function PeoplePanel() {
  const [people, setPeople] = useState<Individual[]>([])
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isEditing = editingId !== null

  const submitLabel = useMemo(() => {
    if (submitting) return isEditing ? 'Updating...' : 'Adding...'
    return isEditing ? 'Update person' : 'Add person'
  }, [isEditing, submitting])

  async function refreshPeople() {
    setLoading(true)
    setError(null)
    try {
      const data = await listIndividuals()
      setPeople(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshPeople()
  }, [])

  function resetForm() {
    setForm(EMPTY_FORM)
    setEditingId(null)
  }

  function toPayload(currentForm: FormState): IndividualCreate {
    return {
      name: currentForm.name.trim(),
      gender: currentForm.gender,
      birth_date: currentForm.birth_date.trim() || undefined,
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!form.name.trim()) {
      setError('Name is required.')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const payload = toPayload(form)
      if (editingId === null) {
        await createIndividual(payload)
      } else {
        await updateIndividual(editingId, payload)
      }
      resetForm()
      await refreshPeople()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    setError(null)
    try {
      await deleteIndividual(id)
      if (editingId === id) {
        resetForm()
      }
      await refreshPeople()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  function beginEdit(person: Individual) {
    setEditingId(person.id)
    setForm({
      name: person.name,
      gender: person.gender,
      birth_date: person.birth_date ?? '',
    })
  }

  return (
    <div className="people-panel">
      <form className="people-form" onSubmit={handleSubmit}>
        <h3>{isEditing ? 'Edit person' : 'Add person'}</h3>

        <label>
          Name
          <input
            value={form.name}
            onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
            placeholder="Full name"
            required
          />
        </label>

        <label>
          Gender
          <select
            value={form.gender}
            onChange={(event) => setForm((prev) => ({ ...prev, gender: event.target.value }))}
          >
            <option value="female">Female</option>
            <option value="male">Male</option>
          </select>
        </label>

        <label>
          Birth date (optional)
          <input
            type="date"
            value={form.birth_date}
            onChange={(event) => setForm((prev) => ({ ...prev, birth_date: event.target.value }))}
          />
        </label>

        <div className="people-form-actions">
          <button type="submit" disabled={submitting}>
            {submitLabel}
          </button>
          {isEditing ? (
            <button type="button" className="secondary" onClick={resetForm}>
              Cancel
            </button>
          ) : null}
        </div>
      </form>

      <div className="people-list-wrap">
        <h3>People</h3>

        {loading ? <p>Loading people...</p> : null}

        {!loading && people.length === 0 ? <p>No people added yet.</p> : null}

        {!loading && people.length > 0 ? (
          <ul className="people-list">
            {people.map((person) => (
              <li key={person.id}>
                <div className="person-text">
                  <strong>{person.name}</strong>
                  <span>
                    {person.gender}
                    {person.birth_date ? ` | ${person.birth_date}` : ''}
                  </span>
                </div>

                <div className="person-actions">
                  <button type="button" className="secondary" onClick={() => beginEdit(person)}>
                    Edit
                  </button>
                  <button type="button" className="danger" onClick={() => void handleDelete(person.id)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        {error ? <p className="error">{error}</p> : null}
      </div>
    </div>
  )
}
