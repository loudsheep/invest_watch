import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import pl from "./i18n/pl.json";
import QueryError from "./components/QueryError";
import { ApiError, api } from "./lib/api";
import { socket } from "./lib/socket";
import AlertsPanel, { useHighRiskAlerts } from "./components/AlertsPanel";
import ModuleBadge from "./components/ModuleBadge";
import RiskCell from "./components/RiskCell";
import Overview from "./pages/Overview";
import Findings from "./pages/Findings";
import FindingDetail from "./pages/FindingDetail";
import Calibration from "./pages/Calibration";
import Cases from "./pages/Cases";
import SystemHealth from "./pages/SystemHealth";
import FindingScreenshot from "./pages/FindingScreenshot";
import Settings from "./pages/Settings";
import ScanNow from "./pages/ScanNow";
import Login from "./pages/Login";

interface HighRiskAlert {
  id: number;
  module: string;
  score: number;
  document_title: string | null;
}

function useSocketStatus() {
  const [connected, setConnected] = useState(socket.connected);
  useEffect(() => {
    const on = () => setConnected(true);
    const off = () => setConnected(false);
    socket.on("connect", on);
    socket.on("disconnect", off);
    return () => {
      socket.off("connect", on);
      socket.off("disconnect", off);
    };
  }, []);
  return connected;
}

export default function App() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [alert, setAlert] = useState<HighRiskAlert | null>(null);
  const connected = useSocketStatus();
  const [panelOpen, setPanelOpen] = useState(false);
  const [readIds, setReadIds] = useState<Set<number>>(new Set());
  const me = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    retry: (count, error) => !(error instanceof ApiError && error.status === 401) && count < 3,
    staleTime: Infinity,
  });
  const signedIn = !!me.data;
  const alerts = useHighRiskAlerts(signedIn);
  const unreadCount = (alerts.data ?? []).filter((f) => !readIds.has(f.id)).length;
  const markRead = (ids: number[]) => setReadIds((prev) => new Set([...prev, ...ids]));

  useEffect(() => {
    if (signedIn) socket.connect();
    else socket.disconnect();
  }, [signedIn]);

  useEffect(() => {
    function onHighRisk(payload: HighRiskAlert) {
      setAlert(payload);
      queryClient.invalidateQueries({ queryKey: ["findings"] });
      queryClient.invalidateQueries({ queryKey: ["counters"] });
      queryClient.invalidateQueries({ queryKey: ["trend"] });
    }
    socket.on("high_risk_finding", onHighRisk);
    return () => {
      socket.off("high_risk_finding", onHighRisk);
    };
  }, [queryClient]);

  useEffect(() => {
    if (!alert) return;
    const timer = window.setTimeout(() => setAlert(null), 9000);
    return () => window.clearTimeout(timer);
  }, [alert]);

  async function handleLogout() {
    await api.logout();
    queryClient.clear();
    await queryClient.invalidateQueries({ queryKey: ["me"] });
  }

  if (me.isPending) {
    return <p className="boot">{pl["common.loading"]}</p>;
  }
  if (me.data === null || (me.error instanceof ApiError && me.error.status === 401)) {
    return <Login />;
  }
  if (!me.data) {
    return <QueryError onRetry={() => me.refetch()} />;
  }

  const initials = me.data.username.slice(0, 2).toUpperCase();

  return (
    <div className="shell">
      <header className="topbar">
        <span className="wordmark">
          <span className="wordmark__mark" aria-hidden="true" />
          investwatch
        </span>
        <nav className="tabs" aria-label="Główna nawigacja">
          <NavLink to="/" end className="tabs__link">
            {pl["nav.overview"]}
          </NavLink>
          <NavLink to="/findings" className="tabs__link">
            {pl["nav.findings"]}
          </NavLink>
          <NavLink to="/cases" className="tabs__link">
            {pl["nav.cases"]}
          </NavLink>
          <NavLink to="/calibration" className="tabs__link">
            {pl["nav.calibration"]}
          </NavLink>
          <NavLink to="/scan" className="tabs__link">
            {pl["nav.scan"]}
          </NavLink>
          <NavLink to="/system" className="tabs__link">
            {pl["nav.system"]}
          </NavLink>
          <NavLink to="/settings" className="tabs__link">
            {pl["nav.settings"]}
          </NavLink>
        </nav>
        <span className="topbar__spacer" />
        <span className={`live${connected ? " live--on" : ""}`} role="status">
          <span className="live__dot" aria-hidden="true" />
          {connected ? pl["live.label.on"] : pl["live.label.off"]}
        </span>
        <div className="alerts-wrap">
          <button className="alerts-btn" aria-expanded={panelOpen} onClick={() => setPanelOpen(!panelOpen)}>
            {pl["nav.alerts"]}
            {unreadCount > 0 && <span className="count-badge">{unreadCount}</span>}
          </button>
          {panelOpen && <AlertsPanel readIds={readIds} onMarkRead={markRead} onClose={() => setPanelOpen(false)} />}
        </div>
        <button className="user" onClick={handleLogout} title={pl["nav.logout"]}>
          <span className="user__avatar">{initials}</span>
          <span>
            <span className="user__name">{me.data.username}</span>
            <span className="user__role">{me.data.role}</span>
          </span>
        </button>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/findings/:id" element={<FindingDetail />} />
          <Route path="/findings/:id/screenshot" element={<FindingScreenshot />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/scan" element={<ScanNow />} />
          <Route path="/system" element={<SystemHealth />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>

      {alert && (
        <div className="alert" role="alert">
          <span className="alert__head">
            <span className="alert__stamp">{pl["toast.highRisk"]}</span>
            <ModuleBadge module={alert.module} />
          </span>
          <span className="alert__title">{alert.document_title || pl["toast.untitled"]}</span>
          <span className="alert__foot">
            <RiskCell score={alert.score} />
            <button
              className="linkbtn"
              onClick={() => {
                navigate(`/findings/${alert.id}`);
                setAlert(null);
              }}
            >
              Otwórz finding →
            </button>
          </span>
        </div>
      )}
    </div>
  );
}
