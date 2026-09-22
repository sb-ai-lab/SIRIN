## Generality Rules (a skill is a procedure for a task CLASS)

A skill is a focused, reusable procedure for a whole CLASS of tasks, not the answer to one instance. The task instruction and evidence you are shown describe ONE example of that class; the skill must still work on unseen instances of the same kind that you never see.

- Write the procedure so a separate solver can follow it directly on a new instance of the class.
- Write for the solver you actually observe in the evidence — a separate, often weaker model: give it the explicit steps, APIs, and safe patterns it needs, and do not assume reasoning, libraries, or steps the traces do not show it performing.
- Show imports, API calls, and steps as general patterns parameterized over the inputs, not as the concrete moves for this one example.
- Capture only generalizable procedure — the transferable "how", never the specific answer, value, or filename of the example in front of you.
