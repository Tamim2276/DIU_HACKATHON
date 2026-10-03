// What a screen shows while its figures are on the way, and when they could not be loaded.

export function Loading({ heights = [320, 200], label = "Loading" }) {
  return (
    <div className="stack" aria-busy="true" aria-label={label}>
      {heights.map((height, index) => (
        <div key={index} className="skeleton" style={{ height }} />
      ))}
    </div>
  );
}

export function Failed({ title, error, onRetry }) {
  return (
    <section className="card notice" role="alert">
      <h1>{title}</h1>
      <p className="card-text">{error}</p>
      <button type="button" className="button" onClick={onRetry}>
        Try again
      </button>
    </section>
  );
}
