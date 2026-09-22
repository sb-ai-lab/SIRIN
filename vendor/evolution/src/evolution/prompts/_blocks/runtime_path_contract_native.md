## Runtime Path Contract

- This evidence comes from a native framework runtime, not the neutral body-injection solver.
- The agent or tool process executes with its current working directory set to the workspace root.
- Workspace snapshots and file previews are shown relative to that workspace root.
- File previews carry a `solver_read_path_from_workspace_root` field; that is the exact path form native solver code or file tools should use for reads.
- In native solver code or tool calls, read workspace-root inputs by their plain relative path, such as `environment/data/input.json`.
- Write each requested deliverable to `output/<filename>` beneath the workspace root.
- Do not teach `../...` input paths or current-directory output writes for this native runtime.
- If you keep any concrete path guidance, preserve these workspace-root forms (plain relative reads, `output/...` writes) — never neutral-solver `../...` reads or `./...` writes.
