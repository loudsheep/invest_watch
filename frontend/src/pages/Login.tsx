import { useState } from "react";
import { useNavigate } from "react-router-dom";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.login(username, password);
      navigate("/");
    } catch {
      setError("Nieprawidłowe dane logowania");
    }
  }

  return (
    <div className="card" style={{ maxWidth: 360 }}>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1rem" }}>
          <label>{pl["login.username"]}</label>
          <br />
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>{pl["login.password"]}</label>
          <br />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p style={{ color: "#991b1b" }}>{error}</p>}
        <button className="btn" type="submit">
          {pl["login.submit"]}
        </button>
      </form>
    </div>
  );
}
