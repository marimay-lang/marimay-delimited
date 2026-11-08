# Findings, limitations and decisions

| Observation | Class / owner | Outcome |
|---|---|---|
| `text.substring` created a full suffix before copying a field; 512 KiB CSV exhausted the 64 MiB VM string pool | Library + typed MIR/text VM/native | Fixed with a shared range operation, retaining both UTF-8 checks, an owned result and errors. The regression repeatedly extracts short ranges from 512 KiB. |
| A scanner with 428 blocks/674 registers exceeded the bytecode-verifier budget | Toolchain / bytecode must-analysis | Fixed with an RPO-initialized queue. Budget, meet and invalidation were not relaxed. |
| First execution of a new native file exceeds 100 ms | Shared startup/host boundary; exact system cause unestablished | Open acceptance blocker. Repeated samples do not replace the first execution; no security or warmup workaround. |
| Whole input up to 1 MiB, JSON up to 1 MiB | Explicit application and standard-API boundary | Sufficient for the defined dialect; arbitrary-size file processing is outside the claim. |

The CSV state machine and source-lint contexts differ; shared `support.my`
contains only CLI handling, limits and reading/writing. `mmay_acceptance.py` v1
was reused unchanged. Business-record fields use `std/json` rather than a
handwritten serializer. This record preserves historical findings, not a new
verification of the current compiler.

The parser assembles escaped fragments through `text.join`; the writer uses a
builder. No CSV-specific runtime path was added. Source tests and independent
Python csv oracles check quoting, CR/LF and exact byte offsets on synthetic
valid tables; the malformed-input dialect is defined explicitly by the source
and acceptance tests.
