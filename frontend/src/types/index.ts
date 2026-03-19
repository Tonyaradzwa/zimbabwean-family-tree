export interface Individual {
  id: number
  name: string
  gender: string
  birth_date?: string
}

export interface IndividualCreate {
  name: string
  gender: string
  birth_date?: string
}

export interface Relationship {
  id: number
  parent_id: number
  child_id: number
  type: string
}

export interface RelationshipCreate {
  parent_id: number
  child_id: number
  type?: string
}

export interface Marriage {
  id: number
  partner1_id: number
  partner2_id: number
  date?: string
}

export interface MarriageCreate {
  partner1_id: number
  partner2_id: number
  date?: string
}

export interface KinshipResult {
  person_id: number
  relative_id: number
  english_relationship: string
  shona_relationship: string
}

export interface QueryRequest {
  query: string
}

export interface QueryResponse {
  query: string
  subject_name?: string
  subject_id?: number
  relationship_asked?: string
  answer: string
}
