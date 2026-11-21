import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import pl from "./i18n/pl.json";
import { socket } from "./lib/socket";
import Overview from "./pages/Overview";
import Findings from "./pages/Findings";
import FindingDetail from "./pages/FindingDetail";
import Calibration from "./pages/Calibration";
import Cases from "./pages/Cases";
import ScanNow from "./pages/ScanNow";
import Login from "./pages/Login";

interface HighRiskAlert {
  id: number;
  module: string;
  score: number;
  document_title: string | null;
}

export default function App() {
  const [alert, setAlert] = useState<HighRiskAlert | null>(null);

  useEffect(() => {
    function onHighRisk(payload: HighRiskAlert) {
      setAlert(payload);
      window.setTimeout(() => setAlert(null), 6000);
    }
    socket.on("high_risk_finding", onHighRisk);
    return () => {
      socket.off("high_risk_finding", onHighRisk);
    };
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>InvestWatch</h1>
        <nav>
          <NavLink to="/" end>
            {pl["nav.overview"]}
          </NavLink>
          <NavLink to="/findings">{pl["nav.findings"]}</NavLink>
          <NavLink to="/cases">{pl["nav.cases"]}</NavLink>
          <NavLink to="/calibration">{pl["nav.calibration"]}</NavLink>
          <NavLink to="/scan">{pl["nav.scan"]}</NavLink>
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/login" element={<Login />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/findings/:id" element={<FindingDetail />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/scan" element={<ScanNow />} />
        </Routes>
      </main>
      {alert && (
        <div className="toast">
          <strong>Wysokie ryzyko ({alert.module})</strong>
          <div>{alert.document_title || "Nowy finding"}</div>
        </div>
      )}
    </div>
  );
}
