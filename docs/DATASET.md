# Dataset z pendrive'a

Wrzuć pliki do `data/dataset/` (katalog jest w `.gitignore`) i uruchom źródło `dataset` w zakładce Ustawienia ("Uruchom teraz"). Powtórne uruchomienie jest bezpieczne: duplikaty są pomijane po hashu treści.

## Obsługiwane formaty

`*.jsonl` (obiekt na linię), `*.json` (obiekt lub tablica), `*.csv` (nagłówek w pierwszym wierszu). Można mieszać formaty.

## Pola

Nazwy pól są rozpoznawane bez względu na wielkość liter. Aliasy są w `FIELD_ALIASES` w `services/scraper/app/collectors/dataset.py`, więc inny eksport wymaga dopisania jednego aliasu.

| Pole | Aliasy | Wymagane |
|---|---|---|
| `content` | text, body, tekst, tresc, description, opis | tak (albo `html`) |
| `url` | link, adres, href | nie, brak daje `dataset://...` |
| `title`, `author`, `platform`, `published_at`, `html`, `id` | polskie i angielskie odpowiedniki | nie |
| `label` | etykieta, ground_truth, violation, naruszenie | nie |

## Etykiety

`label` może być `true` / `false` (dla csv także `tak` / `nie`) albo obiektem per moduł: `{"m1": true, "m2": false, "m3": false}`. Przy utworzeniu findingu etykieta trafia do tabeli `labels`, więc panel Kalibracja liczy precision, recall, FP i FN od pierwszego skanu. Zalecany jest obiekt per moduł: pojedyncze `true` zostanie przypisane każdemu modułowi, który utworzy finding dla tego dokumentu.

Dokument, dla którego żaden moduł nie utworzy findingu (trafność poniżej progu), nie daje etykiety, więc nie trafia do FN.
