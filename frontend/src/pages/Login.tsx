import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import { api } from "../lib/api";
import { MODULES } from "../lib/modules";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const queryClient = useQueryClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.login(username, password);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    } catch (err) {
      const rejected = err instanceof Error && err.message.startsWith("401");
      setError(rejected ? pl["login.invalid"] : pl["login.unreachable"]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <section className="login__intro">
        <span className="brand">InvestWatch</span>
        <h1 className="login__title">{pl["login.tagline"]}</h1>
        <p className="lede">{pl["login.lede"]}</p>
        <ul className="legend">
          {MODULES.map((m) => (
            <li key={m.id} className="legend__item">
              <span className="legend__swatch" style={{ background: m.color }} />
              <strong>{m.short}</strong> {m.name}
            </li>
          ))}
        </ul>
      </section>

      <form className="login__form" onSubmit={handleSubmit}>
        <label className="field">
          <span className="field__label">{pl["login.username"]}</span>
          <input
            className="input"
            value={username}
            autoComplete="username"
            autoFocus
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="field">
          <span className="field__label">{pl["login.password"]}</span>
          <input
            className="input"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="btn" type="submit" disabled={busy || !username || !password}>
          {pl["login.submit"]}
        </button>
      </form>
    </div>
  );
}
