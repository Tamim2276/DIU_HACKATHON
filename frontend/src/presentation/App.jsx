import { useEffect, useState } from "react";

import { useForecast } from "../application/useForecast.js";
import { useLanguage } from "../application/useLanguage.js";
import { useSelection } from "../application/useSelection.js";
import { CONNECTING, READY as CONNECTED, useServer } from "../application/useServer.js";
import ConnectionNotice from "./components/ConnectionNotice.jsx";
import TabBar from "./components/TabBar.jsx";
import { LanguageProvider, useText } from "./language.jsx";
import Actions from "./pages/Actions.jsx";
import Ask from "./pages/Ask.jsx";
import Forecast from "./pages/Forecast.jsx";
import Home from "./pages/Home.jsx";
import ModelReport from "./pages/ModelReport.jsx";

// The five screens. They are tabs inside one page, not separate addresses,
// so a static host needs no extra rules to serve the app.
const TABS = [
  { id: "home", icon: "home" },
  { id: "forecast", icon: "forecast" },
  { id: "actions", icon: "actions" },
  { id: "ask", icon: "ask" },
  { id: "model", icon: "model" },
];

// Each language is named in its own script, whatever language the app is in.
const LANGUAGES = [
  { id: "bn", name: "বাংলা" },
  { id: "en", name: "English" },
];

// The part of the address after "#" remembers the tab, so reloading the page stays on the same screen
// and the browser's Back button returns to the screen before.
function tabInAddress() {
  const id = window.location.hash.slice(1);
  return TABS.some((tab) => tab.id === id) ? id : TABS[0].id;
}

// Everything below the tabs once the API has answered. The chosen customer and day, and the
// forecast for them, are held here so that every screen shows the same customer.
function Screens({ server, tabId, goTo }) {
  const { users, meta } = server;
  const [selection, choose] = useSelection(users, meta);
  const forecastState = useForecast(selection.userId, selection.asOf, selection.goal);

  // The actions switched on, for this customer and day only: another customer starts with none.
  const view = `${selection.userId}|${selection.asOf}`;
  const [switched, setSwitched] = useState({ view, ids: [] });
  const actionIds = switched.view === view ? switched.ids : [];
  const toggleAction = (id) =>
    setSwitched({ view, ids: actionIds.includes(id) ? actionIds.filter((other) => other !== id) : [...actionIds, id] });

  const shared = { users, meta, selection, forecastState, goTo };
  switch (tabId) {
    case "home":
      return <Home {...shared} onChoose={choose} />;
    case "forecast":
      return <Forecast {...shared} />;
    case "actions":
      return <Actions {...shared} actionIds={actionIds} onToggle={toggleAction} />;
    case "ask":
      return <Ask users={users} selection={selection} goTo={goTo} />;
    default:
      return <ModelReport meta={meta} />;
  }
}

function StatusLine({ server }) {
  const { t, f } = useText();
  if (server.status === CONNECTED) {
    return (
      <>
        <span className="dot ok" aria-hidden="true" />
        {t.frame.connected(f.number(server.users.length))}
        {server.meta.data === "synthetic" && <span className="tag">{t.frame.synthetic}</span>}
      </>
    );
  }
  const connecting = server.status === CONNECTING;
  return (
    <>
      <span className={connecting ? "dot wait" : "dot bad"} aria-hidden="true" />
      {connecting ? t.frame.connecting : t.frame.unreachable}
    </>
  );
}

function Frame({ language, onLanguage }) {
  const { t } = useText();
  const server = useServer();
  const [tabId, setTabId] = useState(tabInAddress);

  useEffect(() => {
    const follow = () => setTabId(tabInAddress());
    window.addEventListener("hashchange", follow);
    return () => window.removeEventListener("hashchange", follow);
  }, []);

  function goTo(id) {
    if (id !== tabId) window.history.pushState(null, "", `#${id}`);
    setTabId(id);
    window.scrollTo({ top: 0 });
  }

  const tabs = TABS.map((tab) => ({ ...tab, label: t.frame.tabs[tab.id] }));

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="brand-bn" lang="bn">
            আগাম
          </span>
          <span className="brand-en">Agam</span>
          <span className="tagline">{t.frame.tagline}</span>
        </div>
        <div className="segmented" role="group" aria-label={t.frame.language}>
          {LANGUAGES.map((option) => (
            <button
              key={option.id}
              type="button"
              lang={option.id}
              aria-pressed={language === option.id}
              onClick={() => onLanguage(option.id)}
            >
              {option.name}
            </button>
          ))}
        </div>
      </header>

      <TabBar tabs={tabs} current={tabId} onChoose={goTo} label={t.frame.screens} />

      <main id="panel" className="panel" role="tabpanel" aria-labelledby={`tab-${tabId}`}>
        {server.status === CONNECTED ? (
          <Screens server={server} tabId={tabId} goTo={goTo} />
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

export default function App() {
  const [language, setLanguage] = useLanguage();
  return (
    <LanguageProvider value={language}>
      <Frame language={language} onLanguage={setLanguage} />
    </LanguageProvider>
  );
}
