import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import pl from "../i18n/pl.json";
import ModuleBadge from "../components/ModuleBadge";
import { api } from "../lib/api";
import { MODULES } from "../lib/modules";

const BARS = [1, 1, 2, 1, 2, 2, 2, 3, 3, 4, 5, 5, 7, 8, 9, 12, 14, 18, 24, 30, 36, 46, 56, 64, 70, 58, 42, 30];
const HIGH_FROM = 20;

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
      <section className="login__brand">
        <span className="wordmark wordmark--light">
          <span className="wordmark__mark" aria-hidden="true" />
          investwatch
        </span>
        <div>
          <h1 className="login__title">{pl["login.tagline.title"]}</h1>
          <p className="login__lede">{pl["login.lede"]}</p>
          <ul className="login__modules">
            {MODULES.map((m) => (
              <li key={m.id}>
                <ModuleBadge module={m.id} /> <span>{m.name}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="login__bars" aria-hidden="true">
          {BARS.map((height, i) => (
            <span key={i} className={i >= HIGH_FROM ? "login__bar login__bar--high" : "login__bar"} style={{ height }} />
          ))}
        </div>
      </section>

      <section className="login__side">
        <form className="panel login__form" onSubmit={handleSubmit}>
          <h2 className="login__form-title">Zaloguj się</h2>
          <p className="muted">Dostęp tylko dla analityków i administratorów.</p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <label className="field">
            <span className="field__label">{pl["login.username"]}</span>
            <input
              className="input input--mono"
              value={username}
              autoComplete="username"
              autoFocus
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="field">
            <span className="field__label">{pl["login.password"]}</span>
            <input
              className={`input input--mono${error ? " input--error" : ""}`}
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button className="btn btn--primary" type="submit" disabled={busy || !username || !password}>
            {pl["login.submit"]}
          </button>
          <p className="muted login__note">Uwierzytelnianie gotowe na podmianę na OIDC przy wdrożeniu w UKNF.</p>
        </form>
      </section>
    </div>
  );
}
