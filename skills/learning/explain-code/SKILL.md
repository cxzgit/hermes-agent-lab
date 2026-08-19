---
name: explain-code
description: Explain unfamiliar code from execution flow to important details.
---

# Explain Code

When the user asks about code, follow this order:

1. If the user names a project file, read its complete contents with `read_file` first.
2. State the code's overall responsibility in one sentence.
3. Trace inputs, important transformations, and outputs.
4. Explain unfamiliar language or library concepts in plain language.
5. Give one small concrete example using representative values.
6. End with the most useful breakpoint or experiment for the learner.

Read `references/checklist.md` only when a more detailed review checklist is needed.
