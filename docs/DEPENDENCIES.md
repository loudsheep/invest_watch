# Wykaz narzędzi, bibliotek i modeli

Kompletny wykaz elementów potrzebnych do uruchomienia InvestWatch: obrazy kontenerów, modele AI, biblioteki Python i npm. Wersje i licencje bibliotek Python odczytano z zainstalowanych pakietów w kontenerach serwisów, biblioteki npm z `frontend/package-lock.json`.

## Narzędzia programistyczne

| Narzędzie | Wersja | Licencja | Rola |
|---|---|---|---|
| Docker, Docker Compose | 24+ / v2 | Apache-2.0 | uruchomienie całego stosu |
| Python | 3.12 (`python:3.12-slim`) | PSF-2.0 | serwisy api, ai-worker, scraper-worker, scheduler, migrate |
| Node.js | 22 (`node:22-alpine`), 20 dla demo-sites | MIT | frontend (Vite), demo-sites |
| uv, ruff, pip-audit | najnowsze w CI | Apache-2.0 / MIT, MIT, Apache-2.0 | instalacja, lint, audyt zależności Python |
| ESLint, TypeScript, Vite, Vitest, Playwright | wg `package-lock.json` | MIT / Apache-2.0 | build, lint i testy frontendu |
| Trivy, gitleaks | v0.36.0 (action), 8.30.1 | Apache-2.0, MIT | skanowanie obrazów i sekretów w CI |

## Obrazy kontenerów (serwisy infrastrukturalne)

| Obraz | Wersja | Licencja | Rola |
|---|---|---|---|
| `pgvector/pgvector` | pg16 (PostgreSQL 16) | PostgreSQL License | metadane, treść, wektory |
| `redis` | 7-alpine (7.4) | RSALv2 / SSPLv1 | kolejka zadań, pub/sub, cache |
| `dxflrs/garage` | v2.1.0 | AGPL-3.0 | object storage S3 (HTML, zrzuty, dowody) |
| `ollama/ollama` | latest | MIT | inferencja LLM |
| `searxng/searxng` | latest | AGPL-3.0 | metawyszukiwarka do discovery |
| `vimagick/tinyproxy` | latest (profil `proxy`) | GPL-2.0 | lokalne proxy do demonstracji rotacji |
| `curlimages/curl` | 8.11.1 | curl (MIT-like) | inicjalizacja Garage |

Serwisy na licencjach copyleft lub źródłowo-dostępnych (Redis, Garage, SearXNG, tinyproxy) działają jako osobne, niezmodyfikowane kontenery, z którymi aplikacja komunikuje się przez sieć (protokół Redis, API S3, HTTP). Kod InvestWatch ich nie linkuje ani nie modyfikuje. Każdy z nich można wymienić bez zmian w kodzie: Redis na Valkey (BSD-3-Clause), Garage na dowolny magazyn zgodny z S3, SearXNG na inne źródło wyników wyszukiwania, tinyproxy na dowolne proxy HTTP.

## Modele AI

| Model | Licencja | Rola |
|---|---|---|
| Gemma (domyślnie `gemma3:4b` w compose, na demo Gemma 4 w Ollamie) | wg karty modelu Google (Gemma Terms of Use dla Gemma 3) | LLM: cytaty, uzasadnienie, kryteria oceniane przez model |
| `intfloat/multilingual-e5-base` | MIT | embeddingi tekstu |
| Głowice klasyfikatorów (regresja logistyczna, scikit-learn) | trenowane w projekcie | klasyfikacja per moduł |

Model LLM jest wymienny przez `.env` (`LLM_MODEL`). Alternatywy na licencji Apache-2.0: Qwen, Mistral.

## Biblioteki Python (112 pakietów)

Zależności bezpośrednie są oznaczone pogrubieniem.

| Pakiet | Wersja | Licencja | Serwisy |
|---|---|---|---|
| alembic | 1.20.1 | MIT | ai-worker, api, scheduler, scraper-worker |
| amqp | 5.4.2 | BSD | ai-worker, api, scheduler, scraper-worker |
| annotated-doc | 0.0.7 | MIT | ai-worker, api |
| annotated-types | 0.8.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| anyio | 4.16.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| argon2-cffi | 25.1.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| argon2-cffi-bindings | 26.2.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| **beautifulsoup4** | 4.15.0 | MIT License | scheduler, scraper-worker |
| bidict | 0.24.1 | MPL-2.0 | api |
| billiard | 4.3.2 | BSD | ai-worker, api, scheduler, scraper-worker |
| **celery** | 5.7.0 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| certifi | 2026.11.20 | MPL-2.0 | ai-worker, api, scheduler, scraper-worker |
| cffi | 2.1.1 | MIT-0 | ai-worker, api, scheduler, scraper-worker |
| charset-normalizer | 3.5.2 | MIT | api |
| click | 8.5.1 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| click-didyoumean | 0.3.1 | MIT | ai-worker, api, scheduler, scraper-worker |
| click-plugins | 1.1.1.2 | New BSD | ai-worker, api, scheduler, scraper-worker |
| click-repl | 0.4.1 | MIT | ai-worker, api, scheduler, scraper-worker |
| cloudpickle | 3.1.3 | BSD-3-Clause | ai-worker |
| dnspython | 2.9.2 | ISC | ai-worker, api, scheduler, scraper-worker |
| email-validator | 2.4.0 | Unlicense | ai-worker, api, scheduler, scraper-worker |
| **fastapi** | 0.165.0 | MIT | api |
| filelock | 4.2.4 | MIT | ai-worker |
| fsspec | 2026.9.0 | BSD-3-Clause | ai-worker |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | scraper-worker |
| h11 | 0.16.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| hf-xet | 1.8.0 | Apache-2.0 | ai-worker |
| httpcore | 1.0.9 | BSD-3-Clause | ai-worker, scheduler, scraper-worker |
| httpcore2 | 2.16.2 | BSD-3-Clause | ai-worker |
| httptools | 0.9.0 | MIT | api |
| **httpx** | 0.28.1 | BSD-3-Clause | ai-worker, scheduler, scraper-worker |
| httpx2 | 2.16.2 | BSD-3-Clause | ai-worker |
| huggingface_hub | 2.4.0 | Apache-2.0 | ai-worker |
| idna | 3.20 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| investwatch-ai | 0.1.0 | kod projektu InvestWatch | ai-worker |
| investwatch-api | 0.1.0 | kod projektu InvestWatch | api |
| **investwatch-common** | 0.1.0 | kod projektu InvestWatch | ai-worker, api, scheduler, scraper-worker |
| investwatch-scheduler | 0.1.0 | kod projektu InvestWatch | scheduler |
| investwatch-scraper | 0.1.0 | kod projektu InvestWatch | scraper-worker |
| Jinja2 | 3.1.6 | BSD License | ai-worker |
| **joblib** | 1.6.0 | BSD-3-Clause | ai-worker |
| kombu | 5.7.0 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| **langdetect** | 1.0.9 | MIT | ai-worker |
| Mako | 1.4.3 | MIT | ai-worker, api, scheduler, scraper-worker |
| markdown-it-py | 4.3.0 | MIT License | ai-worker |
| MarkupSafe | 3.0.4 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| mdurl | 0.1.2 | MIT License | ai-worker |
| **minio** | 7.2.20 | Apache-2.0 | api, scraper-worker |
| mpmath | 1.3.0 | BSD | ai-worker |
| narwhals | 2.29.0 | MIT | ai-worker |
| networkx | 3.7 | BSD-3-Clause | ai-worker |
| **numpy** | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | ai-worker |
| opentelemetry-api | 1.45.2 | Apache-2.0 | api |
| **packaging** | 26.3 | Apache-2.0 OR BSD-2-Clause | ai-worker, api, scheduler, scraper-worker |
| pgvector | 0.5.1 | MIT | ai-worker, api, scheduler, scraper-worker |
| pillow | 13.0.0 | MIT-CMU | api |
| pip | 25.0.1 | MIT | ai-worker, api, scheduler, scraper-worker |
| **playwright** | 1.65.2 | Apache-2.0 | scraper-worker |
| prompt_toolkit | 3.0.53 | BSD License | ai-worker, api, scheduler, scraper-worker |
| psycopg | 3.3.9 | LGPL-3.0-only | ai-worker, api, scheduler, scraper-worker |
| psycopg-binary | 3.3.9 | LGPL-3.0-only | ai-worker, api, scheduler, scraper-worker |
| pycparser | 3.12 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| pycryptodome | 4.5.0 | BSD-2-Clause AND Unlicense AND MIT | api, scraper-worker |
| **pydantic** | 2.14.4 | MIT | ai-worker, api, scheduler, scraper-worker |
| pydantic_core | 2.50.5 | MIT | ai-worker, api, scheduler, scraper-worker |
| Pygments | 2.21.0 | BSD-2-Clause | ai-worker |
| PyJWT | 2.15.1 | MIT | api |
| python-dateutil | 2.9.0.post0 | Dual License | ai-worker, api, scheduler, scraper-worker |
| python-dotenv | 1.2.4 | BSD-3-Clause | ai-worker, api, scheduler, scraper-worker |
| python-engineio | 4.15.1 | MIT | api |
| python-multipart | 0.0.34 | Apache-2.0 | api |
| python-socketio | 5.18.1 | MIT | api |
| **PyYAML** | 6.0.4 | MIT | ai-worker, api, scheduler, scraper-worker |
| **RapidFuzz** | 3.14.6 | MIT | ai-worker |
| redis | 8.1.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| regex | 2026.11.19 | Apache-2.0 AND CNRI-Python | ai-worker |
| reportlab | 5.1.0 | BSD License | api |
| rich | 15.0.0 | MIT | ai-worker |
| safetensors | 0.8.0 | Apache Software License | ai-worker |
| **scikit-learn** | 1.9.1 | BSD-3-Clause | ai-worker |
| scipy | 1.18.1 | BSD License | ai-worker |
| **sentence-transformers** | 6.3.0 | Apache-2.0 | ai-worker |
| setuptools | 78.1.0 | MIT License | ai-worker |
| shellingham | 1.5.4 | ISC License | ai-worker |
| simple-websocket | 1.1.0 | MIT License | api |
| six | 1.17.0 | MIT | ai-worker, api, scheduler, scraper-worker |
| soupsieve | 4.1.3 | MIT | scheduler, scraper-worker |
| SQLAlchemy | 2.1.9 | MIT | ai-worker, api, scheduler, scraper-worker |
| starlette | 1.10.0 | BSD-3-Clause | api |
| structlog | 26.1.0 | MIT OR Apache-2.0 | ai-worker, api, scheduler, scraper-worker |
| sympy | 1.14.0 | BSD | ai-worker |
| **tenacity** | 9.2.1 | Apache-2.0 | scraper-worker |
| threadpoolctl | 3.8.0 | BSD-3-Clause | ai-worker |
| tokenizers | 0.23.3 | Apache Software License | ai-worker |
| torch | 2.15.0+cpu | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clau | ai-worker |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | ai-worker |
| transformers | 5.24.0 | Apache 2.0 License | ai-worker |
| truststore | 0.10.5 | MIT | ai-worker |
| typer | 0.29.2 | MIT | ai-worker |
| typing_extensions | 4.16.0 | PSF-2.0 | ai-worker, api, scheduler, scraper-worker |
| typing-inspection | 0.4.5 | MIT | ai-worker, api, scheduler, scraper-worker |
| tzlocal | 5.4.5 | MIT | ai-worker, api, scheduler, scraper-worker |
| urllib3 | 2.8.0 | MIT | api, scraper-worker |
| uv | 0.13.9 | MIT OR Apache-2.0 | ai-worker, api, scheduler, scraper-worker |
| **uvicorn** | 0.54.0 | BSD-3-Clause | api |
| uvloop | 0.23.0 | MIT License | api |
| vine | 5.1.0 | BSD | ai-worker, api, scheduler, scraper-worker |
| watchfiles | 1.3.0 | MIT | api |
| wcwidth | 0.9.5 | MIT License | ai-worker, api, scheduler, scraper-worker |
| websockets | 17.4 | BSD-3-Clause | api |
| wsproto | 1.3.2 | MIT | api |
| **yt-dlp** | 2026.10.26 | Unlicense | scraper-worker |

## Biblioteki npm - frontend (252 pakietów)

Zależności bezpośrednie są oznaczone pogrubieniem. `dev` oznacza narzędzie używane tylko przy budowaniu i testach.

| Pakiet | Wersja | Licencja | Typ |
|---|---|---|---|
| @babel/runtime | 7.29.15 | MIT | runtime |
| @emnapi/core | 2.0.0-beta.2 | MIT | dev |
| @emnapi/runtime | 2.0.0-beta.2 | MIT | dev |
| @emnapi/wasi-threads | 2.2.0 | MIT | dev |
| @eslint-community/eslint-utils | 4.10.1 | MIT | dev |
| @eslint-community/regexpp | 4.12.3 | MIT | dev |
| @eslint/eslintrc | 2.1.4 | MIT | dev |
| @eslint/js | 8.57.1 | MIT | dev |
| @humanwhocodes/config-array | 0.13.0 | Apache-2.0 | dev |
| @humanwhocodes/module-importer | 1.0.1 | Apache-2.0 | dev |
| @humanwhocodes/object-schema | 2.0.3 | BSD-3-Clause | dev |
| @isaacs/nonrecursive-glob-match | 1.1.0 | BlueOak-1.0.0 | dev |
| @jridgewell/resolve-uri | 3.1.3 | MIT | dev |
| @jridgewell/sourcemap-codec | 1.6.0 | MIT | dev |
| @jridgewell/trace-mapping | 0.3.31 | MIT | dev |
| @napi-rs/wasm-runtime | 1.2.6 | MIT | dev |
| @nodelib/fs.scandir | 2.1.5 | MIT | dev |
| @nodelib/fs.stat | 2.0.5 | MIT | dev |
| @nodelib/fs.walk | 1.2.8 | MIT | dev |
| @oxc-project/types | 0.156.0 | MIT | dev |
| **@playwright/test** | 1.65.1 | Apache-2.0 | dev |
| @rolldown/binding-android-arm-eabi | 1.2.19 | MIT | dev |
| @rolldown/binding-android-arm64 | 1.2.19 | MIT | dev |
| @rolldown/binding-darwin-arm64 | 1.2.19 | MIT | dev |
| @rolldown/binding-darwin-x64 | 1.2.19 | MIT | dev |
| @rolldown/binding-freebsd-x64 | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-arm-gnueabihf | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-arm64-gnu | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-arm64-musl | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-ppc64-gnu | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-s390x-gnu | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-x64-gnu | 1.2.19 | MIT | dev |
| @rolldown/binding-linux-x64-musl | 1.2.19 | MIT | dev |
| @rolldown/binding-openharmony-arm64 | 1.2.19 | MIT | dev |
| @rolldown/binding-wasm32-wasi | 1.2.19 | MIT | dev |
| @rolldown/binding-win32-arm64-msvc | 1.2.19 | MIT | dev |
| @rolldown/binding-win32-x64-msvc | 1.2.19 | MIT | dev |
| @rolldown/pluginutils | 1.1.1 | MIT | dev |
| @socket.io/component-emitter | 3.1.2 | MIT | runtime |
| @tanstack/query-core | 5.108.2 | MIT | runtime |
| **@tanstack/react-query** | 5.108.2 | MIT | runtime |
| **@tanstack/react-table** | 8.21.3 | MIT | runtime |
| @tanstack/table-core | 8.21.3 | MIT | runtime |
| @tybys/wasm-util | 0.10.5 | MIT | dev |
| @types/chai | 5.2.3 | MIT | dev |
| @types/d3-array | 3.2.2 | MIT | runtime |
| @types/d3-color | 3.1.3 | MIT | runtime |
| @types/d3-ease | 3.0.2 | MIT | runtime |
| @types/d3-interpolate | 3.0.4 | MIT | runtime |
| @types/d3-path | 3.1.1 | MIT | runtime |
| @types/d3-scale | 4.0.9 | MIT | runtime |
| @types/d3-shape | 3.2.0 | MIT | runtime |
| @types/d3-time | 3.0.4 | MIT | runtime |
| @types/d3-timer | 3.0.2 | MIT | runtime |
| @types/deep-eql | 4.0.2 | MIT | dev |
| @types/estree | 1.0.10 | MIT | dev |
| @types/prop-types | 15.7.15 | MIT | runtime |
| **@types/react** | 18.3.31 | MIT | runtime |
| **@types/react-dom** | 18.3.7 | MIT | dev |
| **@typescript-eslint/eslint-plugin** | 8.73.0 | MIT | dev |
| **@typescript-eslint/parser** | 8.73.0 | MIT | dev |
| @typescript-eslint/project-service | 8.73.0 | MIT | dev |
| @typescript-eslint/scope-manager | 8.73.0 | MIT | dev |
| @typescript-eslint/tsconfig-utils | 8.73.0 | MIT | dev |
| @typescript-eslint/type-utils | 8.73.0 | MIT | dev |
| @typescript-eslint/types | 8.73.0 | MIT | dev |
| @typescript-eslint/typescript-estree | 8.73.0 | MIT | dev |
| @typescript-eslint/utils | 8.73.0 | MIT | dev |
| @typescript-eslint/visitor-keys | 8.73.0 | MIT | dev |
| @ungap/structured-clone | 1.4.0 | ISC | dev |
| **@vitejs/plugin-react** | 6.3.0 | MIT | dev |
| @vitest/mocker | 5.1.1 | MIT | dev |
| @vitest/spy | 5.1.1 | MIT | dev |
| acorn | 8.19.0 | MIT | dev |
| acorn-jsx | 5.3.2 | MIT | dev |
| ajv | 6.15.0 | MIT | dev |
| ansi-regex | 5.0.1 | MIT | dev |
| ansi-styles | 4.3.0 | MIT | dev |
| argparse | 2.0.1 | Python-2.0 | dev |
| assertion-error | 2.0.1 | MIT | dev |
| balanced-match | 1.0.2 | MIT | dev |
| balanced-match | 4.0.4 | MIT | dev |
| brace-expansion | 1.1.22 | MIT | dev |
| brace-expansion | 5.0.13 | MIT | dev |
| callsites | 3.1.0 | MIT | dev |
| chai | 6.3.0 | MIT | dev |
| chalk | 4.1.2 | MIT | dev |
| clsx | 2.1.1 | MIT | runtime |
| color-convert | 2.0.1 | MIT | dev |
| color-name | 1.1.4 | MIT | dev |
| concat-map | 0.0.1 | MIT | dev |
| cookie | 1.1.1 | MIT | runtime |
| cross-spawn | 7.0.6 | MIT | dev |
| csstype | 3.2.4 | MIT | runtime |
| d3-array | 3.2.5 | ISC | runtime |
| d3-color | 3.1.1 | ISC | runtime |
| d3-ease | 3.0.2 | BSD-3-Clause | runtime |
| d3-format | 3.1.3 | ISC | runtime |
| d3-interpolate | 3.0.2 | ISC | runtime |
| d3-path | 3.1.1 | ISC | runtime |
| d3-scale | 4.0.3 | ISC | runtime |
| d3-shape | 3.2.1 | ISC | runtime |
| d3-time | 3.1.1 | ISC | runtime |
| d3-time-format | 4.1.1 | ISC | runtime |
| d3-timer | 3.0.2 | ISC | runtime |
| debug | 4.4.3 | MIT | runtime |
| decimal.js-light | 2.5.1 | MIT | runtime |
| deep-is | 0.1.4 | MIT | dev |
| detect-libc | 2.1.2 | Apache-2.0 | dev |
| doctrine | 3.0.0 | Apache-2.0 | dev |
| dom-helpers | 5.2.1 | MIT | runtime |
| engine.io-client | 6.6.8 | MIT | runtime |
| engine.io-parser | 5.2.3 | MIT | runtime |
| es-module-lexer | 2.3.2 | MIT | dev |
| escape-string-regexp | 4.0.0 | MIT | dev |
| **eslint** | 8.57.1 | MIT | dev |
| **eslint-plugin-react-hooks** | 4.6.2 | MIT | dev |
| eslint-scope | 7.2.2 | BSD-2-Clause | dev |
| eslint-visitor-keys | 5.0.1 | Apache-2.0 | dev |
| eslint-visitor-keys | 3.4.3 | Apache-2.0 | dev |
| espree | 9.6.1 | BSD-2-Clause | dev |
| esquery | 1.7.0 | BSD-3-Clause | dev |
| esrecurse | 4.3.0 | BSD-2-Clause | dev |
| estraverse | 5.3.0 | BSD-2-Clause | dev |
| estree-walker | 3.0.3 | MIT | dev |
| esutils | 2.0.3 | BSD-2-Clause | dev |
| eventemitter3 | 4.0.7 | MIT | runtime |
| expect-type | 1.4.0 | Apache-2.0 | dev |
| fast-deep-equal | 3.1.3 | MIT | dev |
| fast-equals | 5.4.5 | MIT | runtime |
| fast-json-stable-stringify | 2.1.0 | MIT | dev |
| fast-levenshtein | 2.0.6 | MIT | dev |
| fastq | 1.20.3 | ISC | dev |
| fdir | 6.5.0 | MIT | dev |
| file-entry-cache | 6.0.1 | MIT | dev |
| find-up | 5.0.0 | MIT | dev |
| flat-cache | 3.2.0 | MIT | dev |
| flatted | 3.4.4 | ISC | dev |
| fs.realpath | 1.0.0 | ISC | dev |
| fsevents | 2.3.3 | MIT | dev |
| glob | 7.2.3 | ISC | dev |
| glob-parent | 6.0.2 | ISC | dev |
| globals | 13.24.0 | MIT | dev |
| graphemer | 1.4.0 | MIT | dev |
| has-flag | 4.0.0 | MIT | dev |
| ignore | 5.3.2 | MIT | dev |
| ignore | 7.0.16 | MIT | dev |
| import-fresh | 3.3.1 | MIT | dev |
| imurmurhash | 0.1.4 | MIT | dev |
| inflight | 1.0.6 | ISC | dev |
| inherits | 2.0.4 | ISC | dev |
| internmap | 2.0.3 | ISC | runtime |
| is-extglob | 2.1.1 | MIT | dev |
| is-glob | 4.0.3 | MIT | dev |
| is-path-inside | 3.0.3 | MIT | dev |
| isexe | 2.0.0 | ISC | dev |
| js-tokens | 4.0.0 | MIT | runtime |
| js-yaml | 4.3.2 | MIT | dev |
| json-buffer | 3.0.1 | MIT | dev |
| json-schema-traverse | 0.4.1 | MIT | dev |
| json-stable-stringify-without-jsonify | 1.0.1 | MIT | dev |
| keyv | 4.5.4 | MIT | dev |
| levn | 0.4.1 | MIT | dev |
| lightningcss | 1.33.0 | MPL-2.0 | dev |
| lightningcss-android-arm64 | 1.33.0 | MPL-2.0 | dev |
| lightningcss-darwin-arm64 | 1.33.0 | MPL-2.0 | dev |
| lightningcss-darwin-x64 | 1.33.0 | MPL-2.0 | dev |
| lightningcss-freebsd-x64 | 1.33.0 | MPL-2.0 | dev |
| lightningcss-linux-arm-gnueabihf | 1.33.0 | MPL-2.0 | dev |
| lightningcss-linux-arm64-gnu | 1.33.0 | MPL-2.0 | dev |
| lightningcss-linux-arm64-musl | 1.33.0 | MPL-2.0 | dev |
| lightningcss-linux-x64-gnu | 1.33.0 | MPL-2.0 | dev |
| lightningcss-linux-x64-musl | 1.33.0 | MPL-2.0 | dev |
| lightningcss-win32-arm64-msvc | 1.33.0 | MPL-2.0 | dev |
| lightningcss-win32-x64-msvc | 1.33.0 | MPL-2.0 | dev |
| locate-path | 6.0.0 | MIT | dev |
| lodash | 4.18.1 | MIT | runtime |
| lodash.merge | 4.6.2 | MIT | dev |
| loose-envify | 1.4.0 | MIT | runtime |
| magic-string | 1.4.5 | MIT | dev |
| minimatch | 3.1.5 | ISC | dev |
| minimatch | 11.0.9 | BlueOak-1.0.0 | dev |
| ms | 2.1.3 | MIT | runtime |
| nanoid | 3.3.20 | MIT | dev |
| natural-compare | 1.4.0 | MIT | dev |
| object-assign | 4.1.1 | MIT | runtime |
| obug | 3.0.0 | MIT | dev |
| once | 1.4.0 | ISC | dev |
| optionator | 0.9.4 | MIT | dev |
| p-limit | 3.1.0 | MIT | dev |
| p-locate | 5.0.0 | MIT | dev |
| parent-module | 1.0.1 | MIT | dev |
| path-exists | 4.0.0 | MIT | dev |
| path-is-absolute | 1.0.1 | MIT | dev |
| path-key | 3.1.1 | MIT | dev |
| picocolors | 1.1.1 | ISC | dev |
| picomatch | 4.0.7 | MIT | dev |
| playwright | 1.65.1 | Apache-2.0 | dev |
| playwright-core | 1.65.1 | Apache-2.0 | dev |
| postcss | 8.5.33 | MIT | dev |
| prelude-ls | 1.2.1 | MIT | dev |
| prop-types | 15.8.1 | MIT | runtime |
| punycode | 2.3.1 | MIT | dev |
| queue-microtask | 1.2.3 | MIT | dev |
| **react** | 18.3.1 | MIT | runtime |
| **react-dom** | 18.3.1 | MIT | runtime |
| react-is | 16.13.1 | MIT | runtime |
| react-is | 18.3.1 | MIT | runtime |
| react-router | 7.18.6 | MIT | runtime |
| **react-router-dom** | 7.18.6 | MIT | runtime |
| react-smooth | 4.0.4 | MIT | runtime |
| react-transition-group | 4.4.5 | BSD-3-Clause | runtime |
| **recharts** | 2.15.4 | MIT | runtime |
| recharts-scale | 0.4.5 | MIT | runtime |
| resolve-from | 4.0.0 | MIT | dev |
| reusify | 1.1.0 | MIT | dev |
| rimraf | 3.0.2 | ISC | dev |
| rolldown | 1.2.19 | MIT | dev |
| run-parallel | 1.2.0 | MIT | dev |
| scheduler | 0.23.2 | MIT | runtime |
| semver | 7.8.6 | ISC | dev |
| set-cookie-parser | 2.7.3 | MIT | runtime |
| shebang-command | 2.0.0 | MIT | dev |
| shebang-regex | 3.0.0 | MIT | dev |
| **socket.io-client** | 4.8.4 | MIT | runtime |
| socket.io-parser | 4.2.7 | MIT | runtime |
| source-map-js | 1.2.4 | BSD-3-Clause | dev |
| std-env | 4.3.0 | MIT | dev |
| strip-ansi | 6.0.1 | MIT | dev |
| strip-json-comments | 3.1.1 | MIT | dev |
| supports-color | 7.2.0 | MIT | dev |
| text-table | 0.2.0 | MIT | dev |
| tiny-invariant | 1.3.3 | MIT | runtime |
| tinybench | 6.2.4 | MIT | dev |
| tinyexec | 1.3.1 | MIT | dev |
| tinyglobby | 0.2.17 | MIT | dev |
| ts-api-utils | 2.5.0 | MIT | dev |
| tslib | 2.9.1 | 0BSD | dev |
| type-check | 0.4.0 | MIT | dev |
| type-fest | 0.20.2 | (MIT OR CC0-1.0) | dev |
| **typescript** | 5.9.3 | Apache-2.0 | dev |
| uri-js | 4.4.1 | BSD-2-Clause | dev |
| victory-vendor | 36.9.2 | MIT AND ISC | runtime |
| **vite** | 8.3.8 | MIT | dev |
| **vitest** | 5.1.1 | MIT | dev |
| which | 2.0.2 | ISC | dev |
| why-is-node-running | 3.2.1 | MIT | dev |
| word-wrap | 1.2.5 | MIT | dev |
| wrappy | 1.0.2 | ISC | dev |
| ws | 8.21.3 | MIT | runtime |
| xmlhttprequest-ssl | 2.1.2 | MIT | runtime |
| yocto-queue | 0.1.0 | MIT | dev |

## Licencje copyleft

Wśród bibliotek nie ma pakietów na licencji GPL ani AGPL. Występują wyłącznie licencje ze słabym copyleftem:

- `psycopg`, `psycopg-binary` (LGPL-3.0): sterownik PostgreSQL używany bez modyfikacji, linkowany dynamicznie, co LGPL dopuszcza w zamkniętym lub przekazywanym kodzie.
- `certifi`, `bidict`, `tqdm` (Python) oraz `lightningcss` (npm, tylko przy budowaniu) (MPL-2.0): copyleft dotyczy wyłącznie zmodyfikowanych plików tych bibliotek; projekt ich nie modyfikuje.

Serwisy infrastrukturalne na licencjach copyleft opisano w sekcji o obrazach kontenerów.
