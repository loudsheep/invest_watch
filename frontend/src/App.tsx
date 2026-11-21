import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import pl from "./i18n/pl.json";
import { api } from "./lib/api";
import { socket } from "./lib/socket";
import ModuleTag from "./components/ModuleTag";
import Overview from "./pages/Overview";
import Findings from "./pages/Findings";
import FindingDetail from "./pages/FindingDetail";
import Calibration from "./pages/Calibration";
import Cases from "./pages/Cases";
import SystemHealth from "./pages/SystemHealth";
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

  const me = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false, staleTime: Infinity });

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
  if (me.isError) {
    return <Login />;
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar__inner">
          <span className="brand">InvestWatch</span>
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
          </nav>
          <div className="topbar__user">
            <span
              className={`live${connected ? " live--on" : ""}`}
              title={connected ? pl["live.on"] : pl["live.off"]}
              role="status"
            >
              <span className="visually-hidden">{connected ? pl["live.on"] : pl["live.off"]}</span>
            </span>
            <span className="user">
              {me.data.username}
              <span className="user__role">{me.data.role}</span>
            </span>
            <button className="btn btn--quiet" onClick={handleLogout}>
              {pl["nav.logout"]}
            </button>
          </div>
        </div>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/findings/:id" element={<FindingDetail />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/scan" element={<ScanNow />} />
          <Route path="/system" element={<SystemHealth />} />
        </Routes>
      </main>

      {alert && (
        <button
          className="alert"
          role="alert"
          onClick={() => {
            navigate(`/findings/${alert.id}`);
            setAlert(null);
          }}
        >
          <span className="alert__stamp">{pl["toast.highRisk"]}</span>
          <span className="alert__body">
            <ModuleTag module={alert.module} /> {alert.document_title || pl["toast.untitled"]}
          </span>
        </button>
      )}
    </div>
  );
}
