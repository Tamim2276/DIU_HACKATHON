import { useEffect, useState } from "react";

import { useForecast } from "../application/useForecast.js";
import { useSelection } from "../application/useSelection.js";
import { CONNECTING, READY as CONNECTED, useServer } from "../application/useServer.js";
import ConnectionNotice from "./components/ConnectionNotice.jsx";
import TabBar from "./components/TabBar.jsx";
import Home from "./pages/Home.jsx";

// The five screens. They are tabs inside one page, not separate addresses,
// so a static host needs no extra rules to serve the app.
const TABS = [
  { id: "home", label: "Home", icon: "home", title: "Home", shows: "" },
  {
    id: "forecast",
    label: "Forecast",
    icon: "forecast",
    title: "Forecast",
    shows: "The 30-day chart with its range and cushion line, and the regular payments coming up.",
  },
  {
    id: "actions",
    label: "Actions",
    icon: "actions",
    title: "Actions",
    shows: "Suggested actions with switches. The chart updates as they are switched on and off.",
  },
  {
    id: "ask",
    label: "Ask",
    icon: "ask",
    title: "Ask",
    shows: "The explanation in Bangla or English, and a box for follow-up questions.",
  },
  {
    id: "model",
    label: "Model",
    icon: "model",
    title: "Model report",
    shows: "Test results against the simple baselines, the results per persona, and the assumptions behind the data.",
  },
];

// The part of the address after "#" remembers the tab, so reloading the page stays on the same screen.
function tabInAddress() {
  const id = window.location.hash.slice(1);
  return TABS.some((tab) => tab.id === id) ? id : TABS[0].id;
}

function NotBuiltYet({ tab }) {
  return (
    <section className="card empty">
      <p className="label">Not built yet</p>
      <h1>{tab.title}</h1>
      <p className="card-text">{tab.shows}</p>
    </section>
  );
}

// Everything below the tabs once the API has answered. The chosen customer and day, and the
// forecast for them, are held here so that every screen shows the same customer.
function Screens({ server, tab, goTo }) {
  const [selection, choose] = useSelection(server.users, server.meta);
  const forecastState = useForecast(selection.userId, selection.asOf);

  if (tab.id === "home") {
    return (
      <Home
        users={server.users}
        meta={server.meta}
        selection={selection}
        onChoose={choose}
        forecastState={forecastState}
        goTo={goTo}
      />
    );
  }
  return <NotBuiltYet tab={tab} />;
}

function StatusLine({ server }) {
  if (server.status === CONNECTED) {
    return (
      <>
        <span className="dot ok" aria-hidden="true" />
        API connected · {server.users.length} users
      </>
    );
  }
  const connecting = server.status === CONNECTING;
  return (
    <>
      <span className={connecting ? "dot wait" : "dot bad"} aria-hidden="true" />
      {connecting ? "Connecting to the API" : "API not reachable"}
    </>
  );
}

export default function App() {
  const server = useServer();
  const [tabId, setTabId] = useState(tabInAddress);

  useEffect(() => {
    const follow = () => setTabId(tabInAddress());
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  function goTo(id) {
    setTabId(id);
    window.history.replaceState(null, "", `#${id}`);
    window.scrollTo({ top: 0 });
  }

  const tab = TABS.find((candidate) => candidate.id === tabId);

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="brand-bn" lang="bn">
            আগাম
          </span>
          <span className="brand-en">Agam</span>
          <span className="tagline">See a shortfall before it happens</span>
        </div>
        {server.meta?.data === "synthetic" && <span className="tag">Synthetic data</span>}
      </header>

      <TabBar tabs={TABS} current={tabId} onChoose={goTo} />

      <main id="panel" className="panel" role="tabpanel" aria-labelledby={`tab-${tab.id}`}>
        {server.status === CONNECTED ? (
          <Screens server={server} tab={tab} goTo={goTo} />
        ) : (
          <ConnectionNotice server={server} />
        )}
      </main>

      <footer className="foot" role="status">
        <StatusLine server={server} />
      </footer>
    </div>
  );
}
