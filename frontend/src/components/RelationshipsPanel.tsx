import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createMarriage,
  createRelationship,
  deleteMarriage,
  deleteRelationship,
  listIndividuals,
  listMarriages,
  listRelationships,
} from '../api/client'
import type { Individual, Marriage, Relationship } from '../types'

type RelationshipFormState = {
  parent_id: string
  child_id: string
  type: string
}

type MarriageFormState = {
  partner1_id: string
  partner2_id: string
  date: string
}

const EMPTY_RELATIONSHIP_FORM: RelationshipFormState = {
  parent_id: '',
  child_id: '',
  type: 'biological',
}

const EMPTY_MARRIAGE_FORM: MarriageFormState = {
  partner1_id: '',
  partner2_id: '',
  date: '',
}

export default function RelationshipsPanel() {
  const [people, setPeople] = useState<Individual[]>([])
  const [relationships, setRelationships] = useState<Relationship[]>([])
  const [marriages, setMarriages] = useState<Marriage[]>([])

  const [relationshipForm, setRelationshipForm] = useState<RelationshipFormState>(
    EMPTY_RELATIONSHIP_FORM,
  )
  const [marriageForm, setMarriageForm] = useState<MarriageFormState>(EMPTY_MARRIAGE_FORM)

  const [loading, setLoading] = useState(true)
  const [submittingRelationship, setSubmittingRelationship] = useState(false)
  const [submittingMarriage, setSubmittingMarriage] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [peopleData, relationshipData, marriageData] = await Promise.all([
        listIndividuals(),
        listRelationships(),
        listMarriages(),
      ])
      setPeople(peopleData)
      setRelationships(relationshipData)
      setMarriages(marriageData)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  useEffect(() => {
    function handlePeopleUpdated() {
      void loadData()
    }

    window.addEventListener('people-updated', handlePeopleUpdated)
    return () => {
      window.removeEventListener('people-updated', handlePeopleUpdated)
    }
  }, [])

  function getName(id: number): string {
    const person = people.find((p) => p.id === id)
    return person ? person.name : `#${id}`
  }

  async function handleAddRelationship(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const parentId = Number(relationshipForm.parent_id)
    const childId = Number(relationshipForm.child_id)

    if (!parentId || !childId) {
      setError('Please choose both parent and child.')
      return
    }

    if (parentId === childId) {
      setError('Parent and child cannot be the same person.')
      return
    }

    setSubmittingRelationship(true)
    try {
      await createRelationship({
        parent_id: parentId,
        child_id: childId,
        type: relationshipForm.type,
      })
      setRelationshipForm(EMPTY_RELATIONSHIP_FORM)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmittingRelationship(false)
    }
  }

  async function handleAddMarriage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const partner1Id = Number(marriageForm.partner1_id)
    const partner2Id = Number(marriageForm.partner2_id)

    if (!partner1Id || !partner2Id) {
      setError('Please choose both partners.')
      return
    }

    if (partner1Id === partner2Id) {
      setError('Marriage partners cannot be the same person.')
      return
    }

    setSubmittingMarriage(true)
    try {
      await createMarriage({
        partner1_id: partner1Id,
        partner2_id: partner2Id,
        date: marriageForm.date || undefined,
      })
      setMarriageForm(EMPTY_MARRIAGE_FORM)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmittingMarriage(false)
    }
  }

  async function handleDeleteRelationship(id: number) {
    setError(null)
    try {
      await deleteRelationship(id)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  async function handleDeleteMarriage(id: number) {
    setError(null)
    try {
      await deleteMarriage(id)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <div className="relationships-panel">
      <div className="relationship-forms-grid">
        <form className="relationship-form" onSubmit={handleAddRelationship}>
          <h3>Add Parent-Child Link</h3>

          <label>
            Parent
            <select
              value={relationshipForm.parent_id}
              onChange={(event) =>
                setRelationshipForm((prev) => ({ ...prev, parent_id: event.target.value }))
              }
              required
            >
              <option value="">Select parent</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Child
            <select
              value={relationshipForm.child_id}
              onChange={(event) =>
                setRelationshipForm((prev) => ({ ...prev, child_id: event.target.value }))
              }
              required
            >
              <option value="">Select child</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Type
            <select
              value={relationshipForm.type}
              onChange={(event) =>
                setRelationshipForm((prev) => ({ ...prev, type: event.target.value }))
              }
            >
              <option value="biological">Biological</option>
              <option value="adoptive">Adoptive</option>
            </select>
          </label>

          <button type="submit" disabled={submittingRelationship}>
            {submittingRelationship ? 'Saving...' : 'Add relationship'}
          </button>
        </form>

        <form className="relationship-form" onSubmit={handleAddMarriage}>
          <h3>Add Marriage Link</h3>

          <label>
            Partner 1
            <select
              value={marriageForm.partner1_id}
              onChange={(event) =>
                setMarriageForm((prev) => ({ ...prev, partner1_id: event.target.value }))
              }
              required
            >
              <option value="">Select partner 1</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Partner 2
            <select
              value={marriageForm.partner2_id}
              onChange={(event) =>
                setMarriageForm((prev) => ({ ...prev, partner2_id: event.target.value }))
              }
              required
            >
              <option value="">Select partner 2</option>
              {people.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Date (optional)
            <input
              type="date"
              value={marriageForm.date}
              onChange={(event) =>
                setMarriageForm((prev) => ({ ...prev, date: event.target.value }))
              }
            />
          </label>

          <button type="submit" disabled={submittingMarriage}>
            {submittingMarriage ? 'Saving...' : 'Add marriage'}
          </button>
        </form>
      </div>

      <div className="relationship-lists-grid">
        <div className="relationship-list-wrap">
          <h3>Parent-Child Links</h3>
          {loading ? <p>Loading relationships...</p> : null}
          {!loading && relationships.length === 0 ? <p>No relationships yet.</p> : null}
          {!loading && relationships.length > 0 ? (
            // TODO: Add virtualized/windowed list rendering here for large relationship datasets.
            <ul className="people-list">
              {relationships.map((relation) => (
                <li key={relation.id}>
                  <div className="person-text">
                    <strong>
                      {getName(relation.parent_id)} → {getName(relation.child_id)}
                    </strong>
                    <span>{relation.type}</span>
                  </div>
                  <div className="person-actions">
                    <button
                      type="button"
                      className="danger"
                      onClick={() => void handleDeleteRelationship(relation.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="relationship-list-wrap">
          <h3>Marriages</h3>
          {loading ? <p>Loading marriages...</p> : null}
          {!loading && marriages.length === 0 ? <p>No marriages yet.</p> : null}
          {!loading && marriages.length > 0 ? (
            // TODO: Add virtualized/windowed list rendering here for large marriage datasets.
            <ul className="people-list">
              {marriages.map((marriage) => (
                <li key={marriage.id}>
                  <div className="person-text">
                    <strong>
                      {getName(marriage.partner1_id)} + {getName(marriage.partner2_id)}
                    </strong>
                    <span>{marriage.date ? `Date: ${marriage.date}` : 'No date'}</span>
                  </div>
                  <div className="person-actions">
                    <button
                      type="button"
                      className="danger"
                      onClick={() => void handleDeleteMarriage(marriage.id)}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}
    </div>
  )
}
