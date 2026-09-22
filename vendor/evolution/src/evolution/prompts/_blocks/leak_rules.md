## Split Integrity Rules

The hard boundary is the held-out split. Training traces may expose training tests, training outputs, verifier messages, and source artifacts when the run is in TRAIN_EVIDENCE mode. Held-out validation/test tasks and their verifier evidence must never influence skill evolution, stopping, or edit selection.

Do not copy any of the following into the skill body:

- Held-out task instructions, test or verifier code, pytest node ids, failed-test names, assertion expressions, expected values, output values, filenames, schemas, or artifacts.
- Private, benchmark, corpus, or storage file paths unrelated to the solver runtime contract.
- Path hacks or any workaround whose only effect is to access hidden/held-out material.

For TRAIN_EVIDENCE runs, train-specific details are allowed evidence. Prefer a reusable procedure when possible, but it is acceptable to specialize to train evidence when the run is explicitly optimizing train performance. For blind/general runs, treat literal task values and assertion details as unavailable and do not infer them.
