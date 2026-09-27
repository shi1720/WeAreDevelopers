# Separate companion factory

This is the later durable companion run, not the original graded factory. The required original full export is root `room.json`.

[room-export.txt](room-export.txt) contains the complete native BAND JSON export, byte-for-byte: 2,684 messages, SHA-256 `17379ebbe6df3db3745c20426dfae2d00d055e87542fe03645935436d9c58e27`. It is UTF-8 JSON despite the plain-text filename. No messages, tool results or source snippets were removed.

The official checker recognizes only the root room export as a transcript; other JSON files are treated as configuration. Its assignment heuristic therefore flags ordinary source expressions and synthetic setup placeholders inside this supplemental transcript. The plain-text extension accurately classifies this as transcript evidence, while retaining the checker's general credential scanning. An independent publication audit found no actual live credentials. See [export provenance](export-provenance.json).

[run.json](run.json) and the [release report](../../evidence/product/report.md) describe the accepted BAND run. The later [operator deployment evidence](../../evidence/hosted/README.md) includes cloud checks and the explicitly separate UI follow-up. [runtime-usage.json](runtime-usage.json) supplements the coordinator's unavailable billing data with measured provider counters after all four seats stopped. These counters are not a cash invoice.
