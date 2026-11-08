# Historical verification — 2026-09-09, macOS arm64

This translates the original record; it does not report a new run. Compiler:
candidate after `0567634`, SHA-256
`7da536ea73bfdec7809ee6369bc4839133fb99aff4adfc167635d47287c8b0be`. CP42 language evidence relates the exact compiler commit to this
candidate; JSON source hashes identify the application.

- Source tests: **5**, `mmay test . --engine both`.
- **45** process cases plus help in VM/native Debug/Release; **3** closed stdout cases.
- Managed heap: **64 MiB**; large synthetic inputs: **512 KiB**.
- Raw [acceptance](evidence/acceptance.json) and
  [measurements](evidence/measurements.json) include commands, input/output
  hashes, executable/source identity and all samples.

| Dataset | Engine | First sample, ms | Repeated range, ms | Peak RSS, MiB |
|---|---|---:|---:|---:|
| small | native | 391.97 | 7.00–11.49 | 1.98 |
| small | vm | 266.45 | 254.86–255.89 | 27.34 |
| stateful-256k-v1 | native | 110.36 | 112.94–112.94 | 65.69 |
| stateful-256k-v1 | vm | 2730.44 | 2751.17–2751.17 | 91.02 |
| stateful-512k-v1 | native | 249.12 | 216.93–216.93 | 79.41 |
| stateful-512k-v1 | vm | 7908.85 | 7886.65–7886.65 | 105.28 |

Repeated test-both: **0.524 s**, budget 2 s.

Processes were measured sequentially; full C/ASan checks did not run during
measurement. The first native execution followed build with no application
warmup. The new native artifact exceeded 100 ms; the precise host/startup
cause remained unestablished. This remained an acceptance blocker and the
budget was unchanged.

Large-workload and RSS results met preliminary limits, and functional checks
passed locally. Full CP42, other Tier 1 platforms, Linux LeakSanitizer and
broader platform acceptance remained open. This was not public-release status.
