# 0004. Regulatory registry data and entity resolution

- Status: Accepted
- Date: 2026-11-21

## Context

All three modules depend on knowing whether an entity is an authorized investment firm: M1 identifies the advertised firm, M2 needs the publisher to be a registered firm, M3 needs the offering party to be unregistered.

## Considered options

1. Fetch registries live at startup. Fragile.
2. Static snapshot in the repository. Goes stale.
3. Snapshot as seed plus a scheduled `registry-sync` job.

## Decision

Option 3, using public sources:

- KNF registers of domestic investment firms and branches of foreign firms,
- ESMA MiFID register for EU firms passporting services into Poland,
- KNF public warnings list.

An entity resolution layer matches mentions to registry entities by fuzzy name and alias (for example "XTB" and "X-Trade Brokers DM S.A."), domain, NIP and KRS. Every finding carries an `entity` with an `authorized` flag and its source.

## Consequences

- The system works offline from the seed and stays fresh when the network is available.
- Entity resolution is the shared core of all three modules.
