export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>Zimbabwean Family Tree</h1>
        <p>Frontend preview workspace (separate from backend)</p>
      </header>

      <main className="layout">
        <section className="panel">
          <h2>People</h2>
          <p>Add and manage individuals here.</p>
        </section>

        <section className="panel">
          <h2>Relationships</h2>
          <p>Link parent-child and marriage relationships.</p>
        </section>

        <section className="panel wide">
          <h2>Family Tree Canvas</h2>
          <p>
            Graph view placeholder. Once API wiring is added, this will render
            people as nodes and relationships as edges.
          </p>
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
