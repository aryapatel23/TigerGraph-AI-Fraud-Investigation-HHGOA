# Schema Design — FraudInvestigation Graph

> Companion to `gsql/schema.gsql`
> Maps every vertex/edge back to the data dictionary fields in `docs/data-dictionary.md`.
> Judgment calls are called out explicitly in dedicated sections.

---

## Overview

The graph has **11 vertex types** and **20 directed edge types** (plus their auto-generated
reverses). The design follows three principles:

1. **Named signals are first-class attributes.** Every field the README names individually
   gets its own typed column so GSQL queries can filter, sort, and traverse on it directly.
2. **Opaque signals are blobs.** Fields with no published individual definitions (V1-V339,
   C1-C14, D1-D15, unnamed id_xx) are stored as JSON strings. The agent can retrieve and
   pass these blobs to the LLM; the LLM treats them as opaque signals and says so in evidence.
3. **The graph is the FraudCase memory.** The schema is shaped so that the agent can write its
   findings back into the same graph it reads from, enabling later investigations to retrieve
   prior cases.

---

## Vertex Types

### `Customer`

| Attribute | Source field | Notes |
|---|---|---|
| `customer_id` (PK) | `transactions.csv` → `customer_id` | Derived by TigerGraph from card issuer fields. Format: `C01234`. |
| `created_at` | synthetic | Populated at load time; not in raw data. |

**Design choice:** Customer carries almost no raw data attributes because the raw data does
not have a customer table — the customer identity is only implicit in the card fields.
All richer data (addresses, card details) lives on Card or Transaction. The Customer vertex
exists to anchor the `OWNS` edge and to group cards under one identity for R10 queries
("does the customer have two or more compromised cards?").

---

### `Card`

| Attribute | Source field | Notes |
|---|---|---|
| `card_id` (PK) | derived | Format `C01234-K1`; derived from `customer_id` + card index. |
| `card1` – `card6` | `card1`–`card6` in `transactions.csv` | See data dictionary §1. `card4` = network, `card6` = type. |
| `addr1` | `addr1` | Billing region code. Key for out-of-region detection (Pattern 4). |
| `addr2` | `addr2` | Billing country code. `87` = home country. |

**Design choice:** `addr1`/`addr2` are on Card rather than Transaction because they represent
the cardholder's registered billing address, not a per-transaction location. Each transaction
also links to a `BillingRegion` vertex (via `BILLED_IN`) to enable cross-card region queries.

---

### `Transaction`

| Attribute | Source field | Notes |
|---|---|---|
| `transaction_id` (PK) | `TransactionID` (string cast) | Disguised vs. original IEEE dataset. |
| `transaction_dt` | `TransactionDT` | Raw seconds offset; disguised. |
| `transaction_amt` | `TransactionAmt` | USD; disguised. |
| `ts` | `ts` | Real datetime; use this for all temporal queries. |
| `product_cd` | `ProductCD` | W/C/H/R/S; W = in-person. |
| `channel` | `channel` | in_person / online (derived from `ProductCD`). |
| `risk_score` | `risk_score` | Bank model score 0-1. An input, never a verdict. |
| `p_emaildomain` | `P_emaildomain` | Purchaser email domain. |
| `r_emaildomain` | `R_emaildomain` | Recipient email domain. |
| `dist1`, `dist2` | `dist1`, `dist2` | Unnamed distance signals. |
| `counts_json` | `C1`–`C14` | JSON blob (see §Judgment Call below). |
| `deltas_json` | `D1`–`D15` | JSON blob (see §Judgment Call below). |
| `match_flags_json` | `M1`–`M9` | JSON blob (see §Judgment Call below). |
| `vesta_features_json` | `V1`–`V339` | JSON blob (see §Judgment Call below). |

---

### `DeviceProfile`

| Attribute | Source field | Notes |
|---|---|---|
| `device_profile_id` (PK) | synthetic composite | `"<DeviceInfo>|<id_30>|<id_31>|<id_33>"` — the fingerprint string. |
| `device_type` | `DeviceType` | mobile / desktop. |
| `device_info` | `DeviceInfo` | Full device/platform string. |
| `os` | `id_30` | e.g. `Android 7.0`. |
| `browser` | `id_31` | e.g. `samsung browser 6.2`. |
| `screen` | `id_33` | e.g. `2220x1080`. |
| `match_status` | `id_34` | e.g. `match_status:2`. |

**Design choice:** The README explicitly defines DeviceProfile as `DeviceInfo + OS + browser
+ screen` and states: *"A device profile or a billing region shared across many cards in a
short window is worth a look."* This is the primary cross-card linkage vertex. A single
DeviceProfile vertex is shared by all transactions from the same fingerprint — this is what
makes ring detection possible with a single 1-hop traversal. `id_34` (match status) is
included here because it is a property of the device-account relationship rather than
a session-level signal.

---

### `IdentityRecord`

| Attribute | Source field | Notes |
|---|---|---|
| `identity_id` (PK) | = `transaction_id` | 1:1 join with Transaction. |
| `id_15` | `id_15` | Device status: New / Found. Named by README. |
| `id_23` | `id_23` | Proxy type: transparent / anonymous / hidden. Named by README. |
| `id_28` | `id_28` | Device status variant. Observed values: New / NotFound. |
| `id_30`–`id_31`, `id_33`–`id_34` | `id_30`, `id_31`, `id_33`, `id_34` | Duplicated from DeviceProfile for session-level reference. |
| `ratings_json` | `id_01`–`id_11` | Encoded rating blob (see §Judgment Call). |
| `identity_cat_json` | unnamed id_12-id_38 | Unnamed categorical/flag blob. |

**Design choice:** Named identity fields are explicit attributes so GSQL queries can filter
on them directly (e.g. `WHERE id_15 == "New" AND id_23 == "hidden"`). The unnamed remainder
goes into blobs. The IdentityRecord is a separate vertex from DeviceProfile because it holds
session-level signals (per-transaction proxy state, login counts, time-on-page) while
DeviceProfile holds device-level signals that persist across sessions.

---

### `BillingRegion`

| Attribute | Source field | Notes |
|---|---|---|
| `region_code` (PK) | `addr1` (string cast) | Anonymized numeric region code. |
| `addr2` | `addr2` | Country code; same for all cards in one region. |

**Design choice:** This vertex enables Pattern 4 (out-of-region use) detection with a simple
graph query: find all cards that have `BILLED_IN` this region and compare to their `Card.addr1`.
Without a BillingRegion vertex, this requires scanning all transactions numerically.

---

### `EmailDomain`

| Attribute | Source field | Notes |
|---|---|---|
| `domain` (PK) | `P_emaildomain` or `R_emaildomain` | e.g. `gmail.com`. |
| `domain_type` | synthetic | "purchaser" / "recipient" — distinguishes the two roles. |

**Design choice:** Shared email domain is a ring signal (Policy R6). A vertex allows
*"find all cards that used recipient domain X in a time window"* as a 2-hop query rather
than a full table scan.

---

### `FraudPattern`

| Attribute | Source field | Notes |
|---|---|---|
| `pattern_code` (PK) | `pattern` enum | card_testing / card_not_present_fraud / card_not_present_new_device / out_of_region_use / account_takeover / undocumented / none |
| `description` | README §5.2 | Human-readable signature. |
| `policy_rules` | README §Policy | Applicable rule codes, e.g. "R5" or "R1,R2,R3,R4". |

**Design choice:** Making FraudPattern a vertex (rather than just a string attribute on FraudCase)
allows the graph to answer "which cases share this pattern?" with a single edge traversal,
and allows the agent to retrieve the pattern description via graph query rather than
hard-coding it in the prompt.

---

### `FraudCase` ← Key design vertex

| Attribute | Source | Notes |
|---|---|---|
| `case_id` (PK) | `case_id` in both CSVs | `CC-NNNN` for historical; `HHG-NNN` for benchmark. |
| `case_source` | synthetic discriminator | `"historical"` / `"benchmark"` / `"agent"` |
| `customer_id`, `card_id` | both CSVs | Back-reference strings (also via edges). |
| `opened_at`, `closed_at` | both CSVs | Datetime. `closed_at` empty on open cases. |
| `status` | answer format | open / closed_fraud / closed_legitimate / escalated |
| `outcome` | `closed_cases_history.csv` | **Only set when `case_source = "historical"`.** |
| `pattern_code` | both CSVs | Pattern enum value. |
| `first_fraud_txn_id`, `txn_ids`, `n_txns`, `exposure_usd`, `connected_card_ids` | history CSV | Episode data. |
| `actions_taken`, `report_filed`, `analyst_notes` | history CSV | Operational/narrative fields. `analyst_notes` loaded into vector store. |
| `trigger_type`, `trigger_text`, `flagged_txn_id`, `trigger_risk_score` | case_pack CSV | Benchmark-only fields. |
| `agent_verdict`, `agent_fraud_probability`, etc. | answer format | Written by agent after investigation. |

#### Discriminating historical vs. benchmark cases (Requirement 3)

The `case_source` attribute is the guard:

- `"historical"`: loaded from `closed_cases_history.csv`. `outcome` is ground truth.
  Agent queries MUST NOT write to `outcome` on these vertices.
- `"benchmark"`: loaded from `case_pack.csv`. `outcome` is always `""`.
  These are the 20 exam cases. The agent fills `agent_verdict` / `agent_fraud_probability`.
- `"agent"`: created by the agent during live investigation. `outcome` set only when agent closes.

Every GSQL loading job and agent query should check `case_source` before reading `outcome`.
This prevents the agent from accidentally treating a benchmark FraudCase's empty `outcome` as
"cleared" and prevents it from overwriting historical outcomes.

---

### `Evidence`

Maps directly to the `evidence` list items in the answer format:

| Attribute | Answer format field |
|---|---|
| `claim` | `claim` |
| `source` | `source` (graph / document / customer / external) |
| `ref` | `ref` (query name, document section, request id) |
| `entity_ids` | `entity_ids` (pipe-separated) |

**Design choice:** Evidence is a vertex (not a JSON blob on FraudCase) so the agent can query
*"which evidence items mention entity X across all cases?"* — useful for finding prior cases
that reference the same device, card, or merchant.

---

### `Decision`

Maps to the `next_best_actions` items in the answer format:

| Attribute | Answer format field |
|---|---|
| `action` | `action` (policy action name) |
| `route` | `route` (auto / L1 / L2) |
| `reason` | `reason` (policy rule citation) |
| `phase` | `initial` or `final` |
| `executed` | whether the auto action was actually executed |

---

## Edge Types

| Edge | From → To | Purpose |
|---|---|---|
| `OWNS` / `OWNED_BY` | Customer → Card | Links cardholder to all their cards. |
| `MADE` / `MADE_BY` | Card → Transaction | The card made this transaction. |
| `FROM_DEVICE` / `DEVICE_USED_IN` | Transaction → DeviceProfile | Online session device fingerprint. |
| `HAS_IDENTITY` / `IDENTITY_FOR` | Transaction → IdentityRecord | Full identity row for this transaction. |
| `BILLED_IN` / `HAS_TRANSACTION` | Transaction → BillingRegion | Where the transaction was billed (from `addr1`). |
| `USES_EMAIL_DOMAIN` / `EMAIL_DOMAIN_USED_IN` | Transaction → EmailDomain | Purchaser or recipient domain (role on edge). |
| `NEXT_TXN` | Transaction → Transaction | Temporal ordering within a card; needed for card-testing sequence detection. |
| `INVOLVES_TXN` / `TXN_IN_CASE` | FraudCase → Transaction | Which transactions are part of this FraudCase (role: flagged / affected / first_fraud). |
| `ON_CARD` / `CARD_IN_CASE` | FraudCase → Card | The primary card under investigation. |
| `CONNECTED_TO_CARD` / `CARD_CONNECTED_IN_CASE` | FraudCase → Card | Connected cards in the same ring (from `connected_card_ids`). |
| `INVOLVES_CUSTOMER` / `CUSTOMER_IN_CASE` | FraudCase → Customer | The customer under investigation. |
| `LINKED_DEVICE` / `DEVICE_IN_CASE` | FraudCase → DeviceProfile | Device profiles cited as evidence in this FraudCase. |
| `MATCHES_PATTERN` / `PATTERN_MATCHED_IN` | FraudCase → FraudPattern | Which pattern this FraudCase identified. |
| `HAS_EVIDENCE` / `EVIDENCE_FOR_CASE` | FraudCase → Evidence | Evidence items belonging to this FraudCase. |
| `HAS_DECISION` / `DECISION_FOR_CASE` | FraudCase → Decision | Recommended actions for this FraudCase. |
| `SIMILAR_TO_CASE` | FraudCase → FraudCase | This FraudCase retrieved a prior FraudCase as memory (similar_prior_cases). |

---

## Judgment Call: Opaque Columns (V1-V339, C1-C14, D1-D15, M1-M9, id_01-id_11)

### The problem

- `V1`–`V339`: 339 columns, no individual definitions exist (Vesta never published them).
- `C1`–`C14`: 14 columns, group meaning only ("counts").
- `D1`–`D15`: 15 columns, group meaning only ("time deltas in days").
- `M1`–`M9`: 9 columns, group meaning only ("match flags").
- `id_01`–`id_11`: 11 columns, group meaning only ("encoded ratings").
- Unnamed `id_12`–`id_38`: most have no individual definitions.

Total: ~388 opaque columns if modeled individually.

### Option A: Individual attributes (rejected)

Creating 388 typed schema columns would work technically, but:
- Schema becomes unreadable; loading jobs become unmaintainable.
- GSQL has no meaningful query that would filter on `V127 > 0.5` because we
  don't know what V127 means.
- README explicitly says: *"Say so in your evidence rather than pretending to know
  what V127 means."* — individual named attributes would encourage pretending.

### Option B: JSON blobs (chosen)

Each group stored as a compact JSON string attribute:

| Attribute | Contains | Example value |
|---|---|---|
| `vesta_features_json` | V1-V339 | `{"V1":0.0,"V2":1.0,...,"V339":null}` |
| `counts_json` | C1-C14 | `{"C1":1.0,"C2":2.0,...}` |
| `deltas_json` | D1-D15 | `{"D1":0.0,"D2":14.5,...}` |
| `match_flags_json` | M1-M9 | `{"M1":"T","M2":"F",...}` |

Benefits:
- All signal values are preserved and retrievable by the agent.
- The agent can pass the full blob to the LLM for inspection without schema changes.
- Schema stays readable; loading jobs stay maintainable.
- Honest about what the data is: an opaque blob, not named features.

Trade-off: individual blob fields cannot be indexed or used as graph traversal predicates.
This is acceptable because the opaque features are signals for the LLM to reason over,
not graph structure predicates. All structurally meaningful fields (risk_score, channel,
product_cd, addr1, device status, proxy flag, etc.) are explicit attributes.

---

## Judgment Call: IdentityRecord vs. DeviceProfile split

The data dictionary shows `identity.csv` contains both:
- Device fingerprint fields (`DeviceInfo`, `id_30`, `id_31`, `id_33`, `id_34`) — stable
  across sessions by the same device.
- Session/connection signals (`id_01`–`id_11`: ratings, proxy, login counts) — vary
  per transaction.

Storing everything in one vertex would conflate two different granularities. The split:

- `DeviceProfile` = the fingerprint (device, OS, browser, screen). One vertex per unique
  combination, shared across all transactions from that device. This enables ring queries.
- `IdentityRecord` = the session signals (per-transaction, 1:1 with Transaction). Agent
  retrieves these for a specific transaction's context.

Named fields duplicated in both (`id_30`, `id_31`, `id_33`, `id_34`) because an analyst
querying an IdentityRecord needs the OS/browser without a second hop to DeviceProfile.

---

## Judgment Call: Single `FraudCase` vertex type for historical and benchmark

Requirement 3 asks for discrimination between historical (closed) and benchmark (exam) cases.
Two options:

**Option A: Two separate vertex types** — `HistoricalCase` and `BenchmarkCase`.
Pro: structurally impossible to confuse.
Con: queries that retrieve similar past cases (the core `similar_prior_cases` workflow)
must union across two vertex types; edges must be duplicated for each type.

**Option B: One vertex type with a `case_source` discriminator** (chosen).
Pro: a single `SIMILAR_TO_CASE` edge connects any two cases regardless of source; retrieval
queries are uniform; loading and agent code treat all cases the same except for the guard
on `outcome`.
Con: requires discipline — every reader of `outcome` must check `case_source` first.

The guard is enforced by convention in loading jobs and agent queries. The schema comment
documents this contract explicitly. A future loading job can set `outcome = ""` for all
benchmark rows at load time as an additional safeguard.

---

## Mapping: answer format fields → graph writes

| Answer format field | Graph write |
|---|---|
| `FraudCase.status` | `FraudCase.status` |
| `FraudCase.verdict` | `FraudCase.agent_verdict` |
| `FraudCase.fraud_probability` | `FraudCase.agent_fraud_probability` |
| `FraudCase.pattern` | `FraudCase.pattern_code` + `MATCHES_PATTERN` edge |
| `FraudCase.pattern_description` | `FraudCase.agent_pattern_description` |
| `FraudCase.affected_txn_ids` | `INVOLVES_TXN` edges with role="affected" |
| `FraudCase.first_suspicious_txn_id` | `INVOLVES_TXN` edge with role="first_fraud" |
| `FraudCase.connected_card_ids` | `CONNECTED_TO_CARD` edges |
| `FraudCase.connected_device_profiles` | `LINKED_DEVICE` edges |
| `FraudCase.exposure_usd` | `FraudCase.exposure_usd` |
| `FraudCase.evidence[i]` | `Evidence` vertex + `HAS_EVIDENCE` edge |
| `FraudCase.similar_prior_cases` | `SIMILAR_TO_CASE` edges |
| `FraudCase.summary` | `FraudCase.agent_summary` |
| `FraudCase.written_to_graph` | `FraudCase.written_to_graph` (set to TRUE after write) |
| `next_best_actions.initial[i]` | `Decision` vertex (phase="initial") + `HAS_DECISION` |
| `next_best_actions.final[i]` | `Decision` vertex (phase="final") + `HAS_DECISION` |

---

## Deployment

The `FraudInvestigation` schema is deployed, verified, and fully populated with data on a local TigerGraph Community Edition instance via Docker.

- **Deployment Date:** September 22, 2026
- **Data Load Date:** September 22, 2026
- **Database Target:** Local Docker Community Edition (`tigergraph/community:4.2.2`)
- **Container Name:** `tigergraph-hhgoa`
- **Persistent Volume:** `tg-hhgoa-data` (mounted to `/home/tigergraph/tigergraph/data`)
- **Raw Data Path in Container:** `/home/tigergraph/tigergraph/data/hhgoa_raw/`
- **Ports Mapped:**
  - `14240`: GraphStudio, REST++ API, GSQL interface
  - `9000`: RESTPP
  - `14022`: Container SSH (port 22)
- **Schema Status:** Successfully applied with all 11 vertex types and 20 edge types (16 forward directed + reverse pairs).
- **Data Ingestion Status:** Completed cleanly with 0 errors across all 4 CSV datasets via `agent/scripts/load_data.py` and `gsql/loading_jobs.gsql`.

### Final Graph Counts Verification

#### Vertex Counts

| Vertex Type | Loaded Count | Expected / Source | Reconciliation Notes |
|---|---|---|---|
| `Transaction` | 590,742 | 590,742 (`transactions.csv`) | Exact 1:1 match (test artifacts cleaned up) |
| `IdentityRecord` | 144,432 | 144,432 (`identity.csv`) | Exact 1:1 match |
| `FraudCase` | 5,585 | 5,585 (5,565 + 20) | Exact match: 5,565 historical cases (`closed_cases_history.csv`) + 20 benchmark cases (`case_pack.csv`) |
| `Customer` | 13,564 | Derived (`customer_id`) | Deduplicated distinct customers |
| `Card` | 13,944 | Derived (`customer_id-K1`) | Deduplicated distinct cards |
| `DeviceProfile` | 9,705 | Derived fingerprint | Deduplicated distinct `DeviceInfo\|id_30\|id_31\|id_33` fingerprints |
| `BillingRegion` | 332 | Derived (`addr1`) | Distinct billing region codes |
| `EmailDomain` | 60 | Derived (`P_emaildomain`, `R_emaildomain`) | Distinct email domains |
| `FraudPattern` | 7 | Reference seed | 7 fraud pattern definitions (card_testing, account_takeover, etc.) |
| `Evidence` | 0 | Dynamic | Created at runtime by agent investigations |
| `Decision` | 0 | Dynamic | Created at runtime by agent investigations |

#### Edge Counts

| Edge Type | Loaded Count | Target Vertex Relationship | Notes |
|---|---|---|---|
| `MADE` / `MADE_BY` | 590,742 | `Card` → `Transaction` | Exactly 1 card link per transaction |
| `HAS_IDENTITY` / `IDENTITY_FOR` | 144,432 | `Transaction` → `IdentityRecord` | Exactly 1 identity link per identity record |
| `FROM_DEVICE` / `DEVICE_USED_IN` | 140,784 | `Transaction` → `DeviceProfile` | Non-empty device fingerprints in identity data |
| `BILLED_IN` / `HAS_TRANSACTION` | 525,003 | `Transaction` → `BillingRegion` | Transactions with non-null `addr1` |
| `USES_EMAIL_DOMAIN` / `EMAIL_DOMAIN_USED_IN` | 531,106 | `Transaction` → `EmailDomain` | Transactions with non-null email domains (purchaser / recipient) |
| `OWNS` / `OWNED_BY` | 13,553 | `Customer` → `Card` | Cardholder ownership link |
| `MATCHES_PATTERN` / `PATTERN_MATCHED_IN` | 5,565 | `FraudCase` → `FraudPattern` | Links for all historical cases (benchmark cases have no outcome/pattern) |
| `ON_CARD` / `CARD_IN_CASE` | 5,596 | `FraudCase` → `Card` | Primary card under investigation across cases |
| `INVOLVES_CUSTOMER` / `CUSTOMER_IN_CASE` | 5,596 | `FraudCase` → `Customer` | Customer under investigation across cases |
| `INVOLVES_TXN` / `TXN_IN_CASE` | 4,696 | `FraudCase` → `Transaction` | Flagged or first fraud transaction links |
| `NEXT_TXN` | 0 | `Transaction` → `Transaction` | Sequence edges computed dynamically / as needed |
| `CONNECTED_TO_CARD` | 0 | `FraudCase` → `Card` | Ring cards linked dynamically / via agent |
| `LINKED_DEVICE` | 0 | `FraudCase` → `DeviceProfile` | Cited devices linked by agent |
| `HAS_EVIDENCE` / `HAS_DECISION` | 0 | `FraudCase` → `Evidence`/`Decision` | Populated during agent case closure |
| `SIMILAR_TO_CASE` | 0 | `FraudCase` → `FraudCase` | Populated during memory retrieval |

### How to Restart if the Container Stops
If the host machine reboots or Docker Desktop restarts, TigerGraph services do not auto-start by default:

1. **Start the container:**
   ```bash
   docker start tigergraph-hhgoa
   ```
2. **Start TigerGraph internal services:**
   ```bash
   docker exec tigergraph-hhgoa /home/tigergraph/tigergraph/app/cmd/gadmin start all
   ```
3. **Verify services are online:**
   ```bash
   docker exec tigergraph-hhgoa /home/tigergraph/tigergraph/app/cmd/gadmin status
   ```

### How to Re-apply Schema or Re-run Data Ingestion
- **Re-apply schema:**
  ```bash
  .\.venv\Scripts\python agent/scripts/apply_schema.py
  ```
- **Re-run data ingestion & count verification:**
  ```bash
  .\.venv\Scripts\python agent/scripts/load_data.py
  ```


