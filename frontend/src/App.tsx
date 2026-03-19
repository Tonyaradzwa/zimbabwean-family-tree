import PeoplePanel from './components/PeoplePanel'
import RelationshipsPanel from './components/RelationshipsPanel'
import FamilyTreeCanvas from './components/FamilyTreeCanvas'

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>Zimbabwean Family Tree</h1>
        <p>Frontend preview workspace (separate from backend)</p>
      </header>

      <main className="layout">
        <section className="panel wide">
          <h2>People</h2>
          <PeoplePanel />
        </section>

        <section className="panel wide">
          <h2>Relationships</h2>
          <RelationshipsPanel />
        </section>

        <section className="panel wide">
          <h2>Family Tree Canvas</h2>
          <FamilyTreeCanvas />
        </section>

        <section className="panel">
          <h2>Kinship Lookup</h2>
          <p>Resolve English and Shona kinship terms.</p>
        </section>

        <section className="panel">
          <h2>NLP Query</h2>
          <p>Ask natural language family questions.</p>
        </section>
      </main>
    </div>
  )
}
