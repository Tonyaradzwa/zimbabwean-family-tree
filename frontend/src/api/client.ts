import { API_BASE_URL } from '../config'
import type {
  Individual,
  IndividualCreate,
  KinshipResult,
  Marriage,
  MarriageCreate,
  QueryRequest,
  QueryResponse,
  Relationship,
  RelationshipCreate,
} from '../types'

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const bodyText = await response.text()
    throw new Error(`API ${response.status} ${response.statusText}: ${bodyText}`)
  }

  // Endpoints in this API return JSON even for delete success messages.
  return response.json() as Promise<T>
}

// Individuals
export const listIndividuals = (): Promise<Individual[]> =>
  apiRequest<Individual[]>('/individuals/')

export const getIndividual = (id: number): Promise<Individual> =>
  apiRequest<Individual>(`/individuals/${id}`)

export const createIndividual = (payload: IndividualCreate): Promise<Individual> =>
  apiRequest<Individual>('/individuals/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateIndividual = (id: number, payload: IndividualCreate): Promise<Individual> =>
  apiRequest<Individual>(`/individuals/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })

export const deleteIndividual = (id: number): Promise<{ message: string }> =>
  apiRequest<{ message: string }>(`/individuals/${id}`, {
    method: 'DELETE',
  })

// Relationships
export const listRelationships = (): Promise<Relationship[]> =>
  apiRequest<Relationship[]>('/relationships/')

export const getRelationship = (id: number): Promise<Relationship> =>
  apiRequest<Relationship>(`/relationships/${id}`)

export const createRelationship = (payload: RelationshipCreate): Promise<Relationship> =>
  apiRequest<Relationship>('/relationships/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const deleteRelationship = (id: number): Promise<{ message: string }> =>
  apiRequest<{ message: string }>(`/relationships/${id}`, {
    method: 'DELETE',
  })

// Marriages
export const listMarriages = (): Promise<Marriage[]> =>
  apiRequest<Marriage[]>('/marriages/')

export const getMarriage = (id: number): Promise<Marriage> =>
  apiRequest<Marriage>(`/marriages/${id}`)

export const createMarriage = (payload: MarriageCreate): Promise<Marriage> =>
  apiRequest<Marriage>('/marriages/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const deleteMarriage = (id: number): Promise<{ message: string }> =>
  apiRequest<{ message: string }>(`/marriages/${id}`, {
    method: 'DELETE',
  })

// Kinship
export const getKinship = (personId: number, relativeId: number): Promise<KinshipResult> =>
  apiRequest<KinshipResult>(`/kinship/?person_id=${personId}&relative_id=${relativeId}`)

// NLP query
export const runQuery = (payload: QueryRequest): Promise<QueryResponse> =>
  apiRequest<QueryResponse>('/query/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
