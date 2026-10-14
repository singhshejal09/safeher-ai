# Verified rights knowledge records

`rights_knowledge.json` is the reviewed seed corpus for India. Each record keeps a stable ID, topic, classifier categories, keywords for English/Hindi/Hinglish retrieval, a short summary in all three languages, jurisdiction, source name and official URL, review date, source type, and verification status.

The curated source set uses only official India Code, NALSA, Ministry of Women and Child Development, and Ministry of Home Affairs cybercrime portal domains. The summaries are paraphrases of those sources, not legal opinions. `knowledge_base.py` checks the verification status, jurisdiction, review date, HTTPS scheme, and allowlisted official host before retrieval.

The dataset was reviewed on 2026-09-30 for this demo. Re-check the source pages before production use and update `reviewed_at` after a substantive review. Admin CRUD accepts rights records only from the curated government-domain allowlist when they are marked verified.
