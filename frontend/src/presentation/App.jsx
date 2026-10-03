import { useEffect, useState } from "react";

import { useForecast } from "../application/useForecast.js";
import { useSelection } from "../application/useSelection.js";
import { CONNECTING, READY as CONNECTED, useServer } from "../application/useServer.js";
import ConnectionNotice from "./components/ConnectionNotice.jsx";
import TabBar from "./components/TabBar.jsx";
import Actions from "./pages/Actions.jsx";
import Ask from "./pages/Ask.jsx";
import Forecast from "./pages/Forecast.jsx";
import Home from "./pages/Home.jsx";
import ModelReport from "./pages/ModelReport.jsx";

// The five screens. They are tabs inside one page, not separate addresses,
// so a static host needs no extra rules to serve the app.
const TABS = [
  { id: "home", label: "Home", icon: "home" },
  { id: "forecast", label: "Forecast", icon: "forecast" },
  { id: "actions", label: "Actions", icon: "actions" },
  { id: "ask", label: "Ask", icon: "ask" },
  { id: "model", label: "Model", icon: "model" },
];

// The part of the address after "#" remembers the tab, so reloading the page stays on the same screen.
function tabInAddress() {
  const id = window.location.hash.slice(1);
  return TABS.some((tab) => tab.id === id) ? id : TABS[0].id;
}

// Everything below the tabs once the API has answered. The chosen customer and day, and the
// forecast for them, are held here so that every screen shows the same customer.
function Screens({ server, tab, goTo }) {
  const { users, meta } = server;
  const [selection, choose] = useSelection(users, meta);
  const forecastState = useForecast(selection.userId, selection.asOf);
  const [language, setLanguage] = useState("bn"); // the Ask screen opens in Bangla

  // The actions switched on, for this customer and day only: another customer starts with none.
  const view = `${selection.userId}|${selection.asOf}`;
  const [switched, setSwitched] = useState({ view, ids: [] });
  const actionIds = switched.view === view ? switched.ids : [];
  const toggleAction = (id) =>
    setSwitched({ view, ids: actionIds.includes(id) ? actionIds.filter((other) => other !== id) : [...actionIds, id] });

  const shared = { users, meta, selection, forecastState, goTo };
  switch (tab.id) {
    case "home":
      return <Home {...shared} onChoose={choose} />;
    case "forecast":
      return <Forecast {...shared} />;
    case "actions":
      return <Actions {...shared} actionIds={actionIds} onToggle={toggleAction} />;
    case "ask":
      return <Ask users={users} selection={selection} language={language} onLanguage={setLanguage} goTo={goTo} />;
    default:
      return <ModelReport meta={meta} />;
  }
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
