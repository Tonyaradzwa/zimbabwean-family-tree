import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { listIndividuals, listMarriages, listRelationships } from '../api/client'
import type { Individual, Marriage, Relationship } from '../types'

type TreeData = {
  people: Individual[]
  relationships: Relationship[]
  marriages: Marriage[]
}

type LayoutBlock = {
  members: number[]
  x: number
  width: number
}

const NODE_WIDTH = 170
const NODE_GAP = 36
const BLOCK_GAP = 84
const ROW_GAP = 170
const START_X = 80
const START_Y = 44

function average(values: number[]): number {
  if (values.length === 0) return 0
  return values.reduce((acc, value) => acc + value, 0) / values.length
}

function pairKey(a: number, b: number): string {
  return a < b ? `${a}-${b}` : `${b}-${a}`
}

function buildGenerationMap(people: Individual[], relationships: Relationship[]): Map<number, number> {
  const generationMap = new Map<number, number>()
  const parentToChildren = new Map<number, number[]>()
  const childParentCount = new Map<number, number>()

  for (const person of people) {
    childParentCount.set(person.id, 0)
  }

  for (const relation of relationships) {
    const children = parentToChildren.get(relation.parent_id) ?? []
    children.push(relation.child_id)
    parentToChildren.set(relation.parent_id, children)
    childParentCount.set(relation.child_id, (childParentCount.get(relation.child_id) ?? 0) + 1)
  }

  const queue = people
    .filter((person) => (childParentCount.get(person.id) ?? 0) === 0)
    .map((person) => person.id)

  for (const rootId of queue) {
    generationMap.set(rootId, 0)
  }

  let index = 0
  while (index < queue.length) {
    const personId = queue[index]
    index += 1

    const generation = generationMap.get(personId) ?? 0
    const children = parentToChildren.get(personId) ?? []
    for (const childId of children) {
      const nextGeneration = generation + 1
      const currentGeneration = generationMap.get(childId)
      if (currentGeneration === undefined || nextGeneration > currentGeneration) {
        generationMap.set(childId, nextGeneration)
      }
      queue.push(childId)
    }
  }

  for (const person of people) {
    if (!generationMap.has(person.id)) {
      generationMap.set(person.id, 0)
    }
  }

  return generationMap
}

function buildNodes(
  people: Individual[],
  relationships: Relationship[],
  marriages: Marriage[],
): Node[] {
  const peopleById = new Map(people.map((person) => [person.id, person]))
  const generationMap = buildGenerationMap(people, relationships)

  const spouseMap = new Map<number, number[]>()
  for (const marriage of marriages) {
    const left = spouseMap.get(marriage.partner1_id) ?? []
    left.push(marriage.partner2_id)
    spouseMap.set(marriage.partner1_id, left)

    const right = spouseMap.get(marriage.partner2_id) ?? []
    right.push(marriage.partner1_id)
    spouseMap.set(marriage.partner2_id, right)

    const alignedGeneration = Math.max(
      generationMap.get(marriage.partner1_id) ?? 0,
      generationMap.get(marriage.partner2_id) ?? 0,
    )
    generationMap.set(marriage.partner1_id, alignedGeneration)
    generationMap.set(marriage.partner2_id, alignedGeneration)
  }

  const generationBuckets = new Map<number, number[]>()
  for (const person of people) {
    const generation = generationMap.get(person.id) ?? 0
    const bucket = generationBuckets.get(generation) ?? []
    bucket.push(person.id)
    generationBuckets.set(generation, bucket)
  }

  const generations = [...generationBuckets.keys()].sort((a, b) => a - b)
  const blocksByGeneration = new Map<number, LayoutBlock[]>()
  const memberToBlock = new Map<number, LayoutBlock>()

  for (const generation of generations) {
    const members = (generationBuckets.get(generation) ?? []).sort((a, b) => {
      const aName = peopleById.get(a)?.name ?? ''
      const bName = peopleById.get(b)?.name ?? ''
      return aName.localeCompare(bName)
    })

    const blocks: LayoutBlock[] = []
    const used = new Set<number>()
    let cursorX = START_X

    for (const personId of members) {
      if (used.has(personId)) continue

      const spouseInGeneration = (spouseMap.get(personId) ?? []).find(
        (candidate) => (generationMap.get(candidate) ?? 0) === generation && !used.has(candidate),
      )

      const blockMembers = spouseInGeneration
        ? [personId, spouseInGeneration].sort((a, b) => a - b)
        : [personId]

      for (const id of blockMembers) used.add(id)

      const width = blockMembers.length * NODE_WIDTH + (blockMembers.length - 1) * NODE_GAP
      const block: LayoutBlock = { members: blockMembers, x: cursorX, width }

      blocks.push(block)
      cursorX += width + BLOCK_GAP
      for (const id of blockMembers) {
        memberToBlock.set(id, block)
      }
    }

    blocksByGeneration.set(generation, blocks)
  }

  const preferredCenters = new Map<number, number[]>()
  for (const relation of relationships) {
    const parentBlock = memberToBlock.get(relation.parent_id)
    const childBlock = memberToBlock.get(relation.child_id)
    if (!parentBlock || !childBlock) continue

    const center = parentBlock.x + parentBlock.width / 2
    const points = preferredCenters.get(relation.child_id) ?? []
    points.push(center)
    preferredCenters.set(relation.child_id, points)
  }

  for (const generation of generations) {
    const blocks = blocksByGeneration.get(generation) ?? []

    for (const block of blocks) {
      const blockPreferences = block.members
        .flatMap((member) => preferredCenters.get(member) ?? [])
        .filter((value) => Number.isFinite(value))

      if (blockPreferences.length > 0) {
        const targetCenter = average(blockPreferences)
        block.x = targetCenter - block.width / 2
      }
    }

    blocks.sort((a, b) => a.x - b.x)
    let cursor = START_X
    for (const block of blocks) {
      block.x = Math.max(block.x, cursor)
      cursor = block.x + block.width + BLOCK_GAP
    }
  }

  const nodes: Node[] = []
  for (const generation of generations) {
    const blocks = blocksByGeneration.get(generation) ?? []
    const rowY = START_Y + generation * ROW_GAP

    for (const block of blocks) {
      block.members.forEach((memberId, index) => {
        const person = peopleById.get(memberId)
        if (!person) return

        const memberX = block.x + index * (NODE_WIDTH + NODE_GAP)
        nodes.push({
          id: `person-${person.id}`,
          position: { x: memberX, y: rowY },
          data: {
            label: `${person.name}${person.gender ? ` (${person.gender})` : ''}`,
          },
          style: {
            border: '1px solid #0f766e',
            borderRadius: '10px',
            background: '#ffffff',
            color: '#0f172a',
            padding: '8px 10px',
            minWidth: `${NODE_WIDTH}px`,
          },
        })
      })
    }
  }

  return nodes
}

function buildEdges(relationships: Relationship[], marriages: Marriage[]): Edge[] {
  const marriageSet = new Set<string>()
  for (const marriage of marriages) {
    marriageSet.add(pairKey(marriage.partner1_id, marriage.partner2_id))
  }

  const edges: Edge[] = []

  const relationshipsByChild = new Map<number, Relationship[]>()
  for (const relation of relationships) {
    const list = relationshipsByChild.get(relation.child_id) ?? []
    list.push(relation)
    relationshipsByChild.set(relation.child_id, list)
  }

  for (const [childId, childRelations] of relationshipsByChild.entries()) {
    const parentIds = [...new Set(childRelations.map((relation) => relation.parent_id))].sort(
      (a, b) => a - b,
    )

    let collapsedPair: [number, number] | null = null
    for (let i = 0; i < parentIds.length; i += 1) {
      for (let j = i + 1; j < parentIds.length; j += 1) {
        if (marriageSet.has(pairKey(parentIds[i], parentIds[j]))) {
          collapsedPair = [parentIds[i], parentIds[j]]
          break
        }
      }
      if (collapsedPair) break
    }

    const collapsedParents = new Set<number>(collapsedPair ?? [])

    if (collapsedPair) {
      const [sourceParentId] = collapsedPair
      edges.push({
        id: `rel-pair-${collapsedPair[0]}-${collapsedPair[1]}-child-${childId}`,
        source: `person-${sourceParentId}`,
        target: `person-${childId}`,
        type: 'smoothstep',
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#0369a1', strokeWidth: 1.5 },
      })
    }

    for (const relation of childRelations) {
      if (collapsedParents.has(relation.parent_id)) continue

      edges.push({
        id: `rel-${relation.id}`,
        source: `person-${relation.parent_id}`,
        target: `person-${relation.child_id}`,
        type: 'smoothstep',
        label: relation.type,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#0369a1', strokeWidth: 1.5 },
        labelStyle: { fill: '#0f172a', fontSize: 11 },
      })
    }
  }

  const marriageEdges: Edge[] = marriages.map((marriage) => ({
    id: `mar-${marriage.id}`,
    source: `person-${marriage.partner1_id}`,
    target: `person-${marriage.partner2_id}`,
    type: 'straight',
    style: { stroke: '#be185d', strokeDasharray: '6 4', strokeWidth: 1.5 },
  }))

  return [...edges, ...marriageEdges]
}

export default function FamilyTreeCanvas() {
  const [treeData, setTreeData] = useState<TreeData>({
    people: [],
    relationships: [],
    marriages: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function refreshTree() {
    try {
      const [people, relationships, marriages] = await Promise.all([
        listIndividuals(),
        listRelationships(),
        listMarriages(),
      ])
      setTreeData({ people, relationships, marriages })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshTree()

    const id = window.setInterval(() => {
      void refreshTree()
    }, 3000)

    return () => {
      window.clearInterval(id)
    }
  }, [])

  const nodes = useMemo(
    () => buildNodes(treeData.people, treeData.relationships, treeData.marriages),
    [treeData.people, treeData.relationships, treeData.marriages],
  )
  const edges = useMemo(
    () => buildEdges(treeData.relationships, treeData.marriages),
    [treeData.relationships, treeData.marriages],
  )

  if (loading) {
    return <p className="tree-canvas__status">Loading family tree...</p>
  }

  if (error) {
    return <p className="tree-canvas__status error">{error}</p>
  }

  if (nodes.length === 0) {
    return <p className="tree-canvas__status">No people to display yet.</p>
  }

  return (
    <div className="tree-canvas__surface">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap />
        <Controls />
        <Background gap={16} size={1} />
      </ReactFlow>
    </div>
  )
}
