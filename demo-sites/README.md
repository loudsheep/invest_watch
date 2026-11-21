# demo-sites

Fictional pages used for a deterministic demo and E2E tests (ADR-0017). All entity names are made up.

Routes have no `.html` extension (see `server.js`).

| Page | Module | What it demonstrates |
|---|---|---|
| `/finfluencer-aurum` | M1 | Blogger promoting a firm with a promo code and referral link, no risk information |
| `/landing-aurum-cfd` | M2 | Firm landing page with a large profit headline and a small risk disclaimer |
| `/shadow-advisory-pwm` | M3 | Unauthorized "family office" offering investment advice and guaranteed returns |

## Addresses

From the host (browser):

- http://localhost:47080/finfluencer-aurum
- http://localhost:47080/landing-aurum-cfd
- http://localhost:47080/shadow-advisory-pwm

From inside the Docker network (use these in "Skanuj URL", the scraper runs in a container):

- http://demo-sites:8080/finfluencer-aurum
- http://demo-sites:8080/landing-aurum-cfd
- http://demo-sites:8080/shadow-advisory-pwm
