# Deploy produkcyjny na Coolify

Poradnik wdrożenia InvestWatch na serwerze z Coolify v4. Decyzje stojące za tym układem: [ADR-0022](adr/0022-production-deployment-coolify.md).

## Co jest inne niż lokalnie

| | Lokalnie (`docker-compose.yml`) | Produkcja (`docker-compose.coolify.yml`) |
|---|---|---|
| LLM | Ollama w compose (`ollama`, `ollama-init`) | zewnętrzna Ollama `http://10.21.36.10:11434/v1`, model `gemma4:12b` |
| Frontend | Vite dev server | zbudowany statycznie, serwowany przez nginx |
| Konfiguracja (`config/`, `data/`, `init.sql`, `garage.toml`, SearXNG) | bind mounty | wbudowana w obrazy |
| Dostęp z zewnątrz | porty na hoście | domeny przez proxy Coolify (Traefik) z HTTPS |
| Proxy (`proxy-1`, `proxy-2`) | profil `proxy` | brak |

Embeddingi (`intfloat/multilingual-e5-base`) liczy lokalnie `ai-worker`, więc zewnętrzny serwer potrzebny jest tylko do czatu (LLM).

## Adresy

| Serwis | Domena | Port w kontenerze |
|---|---|---|
| `frontend` | `https://investwatch.b.solvro.pl` | 80 |
| `api` | `https://investwatch-api.b.solvro.pl` | 8000 |
| `demo-sites` | `https://investwatch-demo.b.solvro.pl` | 8080 |

Pozostałe serwisy (Postgres, Redis, Garage, SearXNG, workery) nie mają domen i są dostępne tylko w sieci wewnętrznej compose.

## 1. Wymagania

- Serwer z Coolify v4 i działającym proxy (Traefik).
- DNS: `investwatch.b.solvro.pl`, `investwatch-api.b.solvro.pl` i `investwatch-demo.b.solvro.pl` wskazują na serwer (wildcard `*.b.solvro.pl` wystarczy). Sprawdzenie:
  ```bash
  dig +short investwatch.b.solvro.pl
  ```
- Serwer Coolify widzi Ollamę i ma na niej model `gemma4:12b`. Sprawdzenie z serwera:
  ```bash
  curl -s http://10.21.36.10:11434/v1/models | grep -o '"gemma4:12b"'
  ```
- Zasoby (szacunkowo): ~8 GB wolnego RAM i ~25 GB dysku. Obrazy `ai-worker` (PyTorch CPU) i `scraper-worker` (Chromium) są duże, a pierwszy build trwa kilkanaście minut.

## 2. Sekrety

Wygeneruj komplet sekretów lokalnie i zachowaj wynik, np. w menedżerze haseł:

```bash
cat <<EOF
POSTGRES_PASSWORD=$(openssl rand -hex 24)
REDIS_PASSWORD=$(openssl rand -hex 24)
JWT_SECRET=$(openssl rand -hex 32)
ANALYST_PASSWORD=$(openssl rand -hex 12)
ADMIN_PASSWORD=$(openssl rand -hex 12)
S3_ACCESS_KEY=GK$(openssl rand -hex 12)
S3_SECRET_KEY=$(openssl rand -hex 32)
GARAGE_RPC_SECRET=$(openssl rand -hex 32)
GARAGE_ADMIN_TOKEN=$(openssl rand -hex 32)
SEARXNG_SECRET=$(openssl rand -hex 32)
EOF
```

Formaty wymagane przez Garage: `S3_ACCESS_KEY` to `GK` + 24 znaki hex, a `S3_SECRET_KEY` i `GARAGE_RPC_SECRET` to 64 znaki hex. Wszystko jest w hex, więc hasła można bezpiecznie wstawiać do URL-i (`DATABASE_URL`, `REDIS_URL`).

`POSTGRES_PASSWORD`, `ANALYST_PASSWORD` i `ADMIN_PASSWORD` są używane tylko przy pierwszym utworzeniu bazy. Późniejsza zmiana w Coolify nie zmieni haseł w istniejącym wolumenie.

## 3. Utworzenie zasobu w Coolify

1. Projekt, potem **+ New** i **Public Repository**.
2. Repository URL: `https://github.com/loudsheep/invest_watch`, branch: `main`.
3. Build Pack: **Docker Compose**.
4. Docker Compose Location: `/docker-compose.coolify.yml` (Base Directory: `/`).
5. Zapisz. Coolify wczyta compose i pokaże listę serwisów.
6. Auto-deploy zostaw wyłączony, deploy uruchamiasz ręcznie.

## 4. Zmienne środowiskowe

W zakładce **Environment Variables** (tryb Developer view pozwala wkleić całość naraz) ustaw sekrety z kroku 2 oraz:

```env
LLM_BASE_URL=http://10.21.36.10:11434/v1
LLM_MODEL=gemma4:12b
LLM_API_KEY=

CORS_ORIGINS=https://investwatch.b.solvro.pl
VITE_API_URL=https://investwatch-api.b.solvro.pl
```

- `VITE_API_URL` trafia do frontendu w czasie **buildu** (build arg). Po zmianie trzeba zrobić redeploy, żeby front przebudować.
- `CORS_ORIGINS` to dokładny origin frontu: z `https://`, bez ukośnika na końcu.
- Opcjonalne: `S3_BUCKET` (domyślnie `investwatch-evidence`) i `PROXY_URLS` (puste oznacza połączenie bezpośrednie).

Brak wymaganej zmiennej zatrzymuje deploy z błędem `required variable ... is missing a value`.

## 5. Domeny

W widoku zasobu, przy każdym serwisie, w polu **Domains** wpisz:

| Serwis | Wartość pola Domains |
|---|---|
| `frontend` | `https://investwatch.b.solvro.pl` |
| `api` | `https://investwatch-api.b.solvro.pl:8000` |
| `demo-sites` | `https://investwatch-demo.b.solvro.pl:8080` |

Sufiks `:8000` / `:8080` oznacza port w kontenerze, na który Coolify kieruje ruch. Publicznie i tak działa zwykłe HTTPS na 443. Pozostałym serwisom zostaw pole puste. Socket.io (WebSocket) przechodzi przez Traefik bez dodatkowej konfiguracji.

## 6. Pierwszy deploy

Kliknij **Deploy**. Coolify buduje obrazy, a potem uruchamia `docker compose up -d`. Kolejność wynika z `depends_on`:

1. `postgres`, `redis`, `garage`, `searxng`, `demo-sites`.
2. `migrate` (migracje Alembic + seed rejestru i kont) oraz `garage-init` (layout, klucz, bucket). Oba kończą pracę i mają status `exited (0)`, to normalne. Mają `exclude_from_hc: true`, więc nie psują statusu zasobu.
3. `api`, `scraper-worker`, `ai-worker`, `scheduler`, `frontend`.

Przy pierwszym skanie `ai-worker` pobiera model embeddingów z HuggingFace (~1 GB) do wolumenu `ai_models`. Pierwszy skan trwa przez to dłużej, kolejne starty korzystają z cache.

## 7. Weryfikacja

1. API:
   ```bash
   curl https://investwatch-api.b.solvro.pl/health
   ```
2. LLM z wnętrza `ai-worker` (Coolify: serwis `ai-worker`, zakładka **Terminal**):
   ```bash
   python -c "import httpx, os; r = httpx.post(os.environ['LLM_BASE_URL'] + '/chat/completions', json={'model': os.environ['LLM_MODEL'], 'messages': [{'role': 'user', 'content': 'Odpowiedz jednym słowem: działa?'}]}, timeout=60); print(r.status_code, r.json()['choices'][0]['message']['content'])"
   ```
   Oczekiwany wynik: `200` i krótka odpowiedź modelu.
3. Dashboard: otwórz `https://investwatch.b.solvro.pl` i zaloguj się jako `analyst` albo `admin` hasłem z kroku 2.
4. Skan testowy: w dashboardzie uruchom skan adresu `http://demo-sites:8080/landing-aurum-cfd`. Etapy `fetch`, `embed`, `classify` i `llm` powinny przejść do `done`.
5. Demo-sites w przeglądarce: `https://investwatch-demo.b.solvro.pl/landing-aurum-cfd`.

## 8. Typowe problemy

| Objaw | Przyczyna i rozwiązanie |
|---|---|
| Front wysyła requesty na `http://localhost:47800` | Front zbudowany bez `VITE_API_URL`. Ustaw zmienną i zrób redeploy. |
| W konsoli przeglądarki błąd CORS | `CORS_ORIGINS` różni się od adresu frontu (protokół, ukośnik, literówka). Popraw i zrestartuj `api`. |
| Błąd `Mixed Content` | `VITE_API_URL` zaczyna się od `http://`. Musi być `https://`. |
| Etap `llm` kończy się błędem lub timeoutem | Sprawdź test z kroku 7.2. Timeouty są stałe (60-90 s). Ollama jest współdzielona z innymi aplikacjami, więc przy obciążeniu odpowiedzi zwalniają. |
| `ai-worker` nie łączy się z `10.21.36.10` | Sieć Dockera na serwerze nie ma trasy do Ollamy. Sprawdź `curl` z hosta (krok 1), a potem z terminala kontenera. |
| `api` lub workery nie startują, `migrate` / `garage-init` z kodem różnym od 0 | Logi tego serwisu w Coolify. Najczęściej zły format kluczy Garage (krok 2) albo hasło Postgres zmienione po utworzeniu wolumenu. |
| Skan `demo-sites` odrzucony przez SSRF guard | Host spoza `FETCH_ALLOWED_PRIVATE_HOSTS` (`demo-sites`, `nordik-brokr-demo.local`). Do skanów testowych używaj tych nazw. |
| Logowanie nie przyjmuje nowego hasła | Hasła kont seeduje się tylko przy tworzeniu bazy (krok 2). |

## 9. Aktualizacja

1. Wypchnij zmiany na `main`.
2. W Coolify kliknij **Redeploy**. Wolumeny (baza, dowody w Garage, model embeddingów) zostają.
3. Nowe migracje Alembic uruchomią się same w serwisie `migrate`.

Zmiany w `config/` i `data/` też wymagają redeployu, bo są wbudowane w obrazy.

Pełny reset danych: zatrzymaj zasób i usuń jego wolumeny w Coolify (**Persistent Storage**). Ta operacja jest nieodwracalna.
