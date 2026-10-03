import Icon from "./Icon.jsx";

// The row of screens: along the bottom on a phone, under the header on a wide screen.
// Left and right arrow keys move between tabs, as in any tab list.
export default function TabBar({ tabs, current, onChoose, label }) {
  function onKeyDown(event) {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    event.preventDefault();
    const index = tabs.findIndex((tab) => tab.id === current);
    const next = tabs[(index + step + tabs.length) % tabs.length];
    onChoose(next.id);
    document.getElementById(`tab-${next.id}`)?.focus();
  }

  return (
    <nav className="tabs" aria-label={label}>
      <div className="tab-list" role="tablist" onKeyDown={onKeyDown}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            type="button"
            role="tab"
            className="tab"
            aria-selected={tab.id === current}
            aria-controls="panel"
            tabIndex={tab.id === current ? 0 : -1}
            onClick={() => onChoose(tab.id)}
          >
            <Icon name={tab.icon} size={20} />
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
