## Runtime Path Contract

- The solver executes generated Python with its current working directory set to `<workspace>/output`.
- Workspace snapshots and file previews are shown relative to the workspace root, one directory above that working directory.
- File previews carry a `solver_read_path_from_output_cwd` field; that is the exact path form solver code should use for reads.
- In solver code, read workspace-root inputs with `../<path>` and write requested deliverables to `./<filename>`.
- Do not teach workspace-root input paths as if they were directly openable from the solver's working directory.
- If you keep any concrete path guidance, preserve these solver-cwd forms (`../...` for reads, `./...` for writes) — never corpus, storage, or workspace-root paths.
