import re
import math
from typing import List, Dict, Any

# Curated knowledge base from docs/data-dictionary.md and README.md
POLICY_AND_PATTERN_DOCS = [
    {
        "doc_id": "pattern_card_testing",
        "title": "Pattern 1 — Card Testing (Policy R5)",
        "category": "pattern",
        "keywords": ["card_testing", "tiny", "small", "authorization", "sequence", "under $5", "rapid", "larger purchase", "r5"],
        "content": (
            "Pattern 1 — card_testing: A stolen card number is validated before use. "
            "Signature: Three or more tiny online authorizations (often under $5) on one card within a short window "
            "(approximately one hour), followed by a larger purchase (> $15). The sequence itself is confirmation. "
            "Policy R5 mandates DECLINE_TRANSACTION + STEP_UP_AUTH. If purchase over $100 already cleared, BLOCK_CARD."
        )
    },
    {
        "doc_id": "pattern_cnp_fraud",
        "title": "Pattern 2 — Card-Not-Present Fraud (Policy R1-R4)",
        "category": "pattern",
        "keywords": ["card_not_present_fraud", "cnp", "online", "burst", "unusual amount", "48 hours", "r1", "r2", "r3", "r4"],
        "content": (
            "Pattern 2 — card_not_present_fraud: The card number is used for online purchases without physical card present. "
            "Signature: Amounts and product codes inconsistent with the cardholder's history, typically in a burst of "
            "2-4 transactions within 48 hours. Distinguished from Pattern 3 by the device NOT being flagged as new. "
            "A single unusual online purchase is ambiguous: verify before blocking under Policy R1."
        )
    },
    {
        "doc_id": "pattern_cnp_new_device",
        "title": "Pattern 3 — Card-Not-Present Fraud from New Device",
        "category": "pattern",
        "keywords": ["card_not_present_new_device", "new device", "id_15", "id_28", "proxy", "id_23", "anonymous", "hidden"],
        "content": (
            "Pattern 3 — card_not_present_new_device: Online purchases inconsistent with history where the identity record "
            "marks the device as New for this account (id_15 = New or id_28 = New), often combined with an anonymous/hidden "
            "proxy (id_23). Stronger signal than Pattern 2, but requires corroboration since cardholders buy new devices."
        )
    },
    {
        "doc_id": "pattern_out_of_region",
        "title": "Pattern 4 — Out-of-Region Use (Policy R2, R3)",
        "category": "pattern",
        "keywords": ["out_of_region_use", "in_person", "card_present", "addr1", "billing region", "concurrent", "simultaneous", "home region"],
        "content": (
            "Pattern 4 — out_of_region_use: Card-present (in_person, ProductCD=W) purchases in a billing region (addr1) the "
            "cardholder has no transaction history in, while normal activity continues at home. "
            "Several days of purchases in one new region may indicate legitimate travel; simultaneous activity in two different "
            "regions within 48 hours is the smoking gun of card cloning."
        )
    },
    {
        "doc_id": "pattern_account_takeover",
        "title": "Pattern 5 — Account Takeover",
        "category": "pattern",
        "keywords": ["account_takeover", "ato", "credentials", "mixed channel", "device sharing", "match status", "id_34"],
        "content": (
            "Pattern 5 — account_takeover: Mixed-channel activity inconsistent with cardholder history, accompanied by device anomalies, "
            "match-flag anomalies (id_34), or multiple cards linked to the same device fingerprint. Points to stolen account credentials "
            "rather than simply a compromised card number. Often involves rapid high-risk transactions across multiple channels."
        )
    },
    {
        "doc_id": "pattern_undocumented",
        "title": "Novel / Undocumented Pattern (Policy R9)",
        "category": "pattern",
        "keywords": ["undocumented", "novel", "coordinated", "unusual", "r9", "emerging fraud"],
        "content": (
            "Undocumented Pattern: Confirmed fraud that matches none of the 5 standard typologies. "
            "Policy R9 dictates: For undocumented patterns with coordinated or repeated abuse across customers, "
            "CREATE_CASE + FILE_REPORT + ESCALATE_TO_ANALYST. Describe the pattern in own words; do not force into known categories."
        )
    },
    {
        "doc_id": "policy_r1",
        "title": "Policy Rule R1 — Weak Signal Verification",
        "category": "policy",
        "keywords": ["r1", "weak signal", "verify", "step_up_auth", "verify_with_customer", "low confidence", "uncertain"],
        "content": (
            "Policy R1: Verify before blocking on a weak signal. If fraud probability < 0.70 and only one suspicious signal exists, "
            "the agent must use VERIFY_WITH_CUSTOMER or STEP_UP_AUTH before executing any card or transaction block."
        )
    },
    {
        "doc_id": "policy_r2",
        "title": "Policy Rule R2 — Customer Dispute & Denial",
        "category": "policy",
        "keywords": ["r2", "customer denies", "dispute", "block_card", "create_case", "file_report", "exposure > $1000"],
        "content": (
            "Policy R2: If customer denies the transaction, immediately execute BLOCK_CARD and CREATE_CASE. "
            "Add FILE_REPORT (SAR) if exposure > $1,000 or if the case connects to a shared device or multi-card fraud ring."
        )
    },
    {
        "doc_id": "policy_r3",
        "title": "Policy Rule R3 — Customer Confirmed Legitimate",
        "category": "policy",
        "keywords": ["r3", "customer confirms", "legitimate", "close_no_fraud", "cleared", "false alarm"],
        "content": (
            "Policy R3: If customer confirms the transaction was legitimate, execute CLOSE_NO_FRAUD. Record confirmation notes in case file."
        )
    },
    {
        "doc_id": "policy_r4",
        "title": "Policy Rule R4 — Unresponsive Customer Window",
        "category": "policy",
        "keywords": ["r4", "no reply", "24 hours", "monitor_card", "decline_transaction", "exposure > $500"],
        "content": (
            "Policy R4: If no customer reply is received within 24 hours, apply MONITOR_CARD and DECLINE_TRANSACTION for pending "
            "authorizations. Escalate to fraud analyst if exposure exceeds $500."
        )
    },
    {
        "doc_id": "policy_r5",
        "title": "Policy Rule R5 — Card Testing Intervention",
        "category": "policy",
        "keywords": ["r5", "card testing action", "decline_transaction", "step_up_auth", "block_card", "rapid auths"],
        "content": (
            "Policy R5: On card testing sequence (3+ small online auths in an hour followed by larger attempt): "
            "Execute DECLINE_TRANSACTION + STEP_UP_AUTH. If an authorization over $100 has already cleared, immediately BLOCK_CARD."
        )
    },
    {
        "doc_id": "policy_r6",
        "title": "Policy Rule R6 — Shared Origin & Multi-Card Rings",
        "category": "policy",
        "keywords": ["r6", "shared origin", "shared device", "device sharing", "shared email", "monitor_connected_cards", "ring"],
        "content": (
            "Policy R6: Shared origin across cards (same device fingerprint, billing region, or recipient email): "
            "Execute CREATE_CASE + FILE_REPORT + MONITOR_CONNECTED_CARDS for every connected card caught in the cluster."
        )
    },
    {
        "doc_id": "policy_r8",
        "title": "Policy Rule R8 — Escalation on Uncertainty",
        "category": "policy",
        "keywords": ["r8", "uncertain", "escalate_to_analyst", "conflicting evidence", "exposure > $500", "ambiguous"],
        "content": (
            "Policy R8: When verdict is uncertain and exposure exceeds $500, or when graph evidence conflicts with customer/model signals: "
            "Execute ESCALATE_TO_ANALYST for human review."
        )
    },
    {
        "doc_id": "policy_stopping_criteria",
        "title": "Investigation Stopping Criteria",
        "category": "policy",
        "keywords": ["stopping criteria", "stop investigation", "confidence", "defensible", "evidence threshold", ">= 0.85", "<= 0.15"],
        "content": (
            "Investigation Stopping Criteria: Stop investigation when fraud probability is >= 0.85 (confirm fraud) or "
            "<= 0.15 (clear legitimate), supported by at least two independent pieces of evidence from the graph. "
            "If between 0.15 and 0.85, mark needs_more_evidence = True and request specific step-up authentication or customer verification."
        )
    }
]

class LocalPolicyRAG:
    """
    Lightweight GraphRAG indexer for Fraud Policies and Typologies.
    Uses TF-IDF vectorization with BM25 term weighting and keyword boosting.
    Requires no external dependencies and runs in <2ms.
    """
    def __init__(self, docs: List[Dict[str, Any]] = None):
        self.docs = docs or POLICY_AND_PATTERN_DOCS
        self.doc_freq = {}
        self.doc_lengths = []
        self.doc_tokens = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9_\$]", " ", text.lower())
        return [tok for tok in cleaned.split() if len(tok) > 1]

    def _build_index(self):
        n_docs = len(self.docs)
        for d in self.docs:
            combined_text = f"{d['title']} {' '.join(d.get('keywords', []))} {d['content']}"
            tokens = self._tokenize(combined_text)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

        self.avg_doc_len = sum(self.doc_lengths) / max(1, n_docs)
        self.idf = {
            t: math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            for t, df in self.doc_freq.items()
        }

    def retrieve(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query_text)
        scores = []
        k1 = 1.5
        b = 0.75

        for idx, d in enumerate(self.docs):
            doc_len = self.doc_lengths[idx]
            tokens = self.doc_tokens[idx]
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            score = 0.0
            matched_terms = []
            for qt in query_tokens:
                if qt in token_counts:
                    tf = token_counts[qt]
                    idf_val = self.idf.get(qt, 0.5)
                    # BM25 formula
                    num = tf * (k1 + 1)
                    denom = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
                    score += idf_val * (num / denom)
                    matched_terms.append(qt)

            # Keyword direct match boost
            for kw in d.get("keywords", []):
                if kw in query_text.lower():
                    score += 3.0
                    matched_terms.append(kw)

            if score > 0:
                scores.append({
                    "doc_id": d["doc_id"],
                    "title": d["title"],
                    "category": d["category"],
                    "content": d["content"],
                    "relevance_score": round(score, 3),
                    "matched_keywords": list(set(matched_terms))[:5]
                })

        # Rank descending
        scores.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_results = scores[:top_k]

        # Generate user-friendly summaries of relevance
        for item in top_results:
            reason = f"Matches evidence signals: {', '.join(item['matched_keywords'])}" if item['matched_keywords'] else "Relevant baseline policy"
            item["summary"] = f"{item['title']} (Score {item['relevance_score']}): {reason}"

        return top_results

# Global retriever instance
policy_retriever = LocalPolicyRAG()
