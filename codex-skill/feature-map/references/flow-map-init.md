# Flow Map Init

Create or extend `FEATURE-MAP.yaml` for the current repo.

1. If `FEATURE-MAP.yaml` exists, read it first and extend or correct it. Do not overwrite.
2. **Enumerate fully first, do not sample.** List EVERY entrypoint-level directory/namespace (e.g. every folder under `app/Http/Controllers/` or equivalent, every route group, every service/app in a monorepo, every top-level Livewire/screen folder). Write this list out explicitly as a working checklist before continuing — do not jump straight to the most familiar/obvious examples. Community/module groupings from code-review-graph (if available) are usually too coarse for this (one community can bundle hundreds of files across unrelated features) — use them as architecture context only, never as the candidate-flow list itself.
3. **No filtering or skipping here — every checklist item must become a flow entry.** This is the complete registry of the app's business flows, not just the most visible cross-layer ones. For each item, determine its touchpoints across whatever layers actually exist (client form/screen, backend validation/service, admin/web view, docs, db migration, event consumer) — if it genuinely only lives in one layer (e.g. pure admin CRUD with no client counterpart), write it as-is with whatever touchpoints exist; do not drop it from the registry. The only items allowed to stay undocumented are pure non-business infrastructure (generic utils/helpers, framework config, health checks) — never "less critical" or "single-layer" as a reason to skip.
4. For each flow, find concrete touchpoints with `rg` and verify each path exists. If several small modules are functionally one pipeline (e.g. multiple master-data tables that all feed one formula engine), merge them into one umbrella flow with many touchpoints instead of one flow per file.
5. Write the small supported YAML subset only. Do not use YAML anchors, multiline strings, or complex nesting.

Use this shape:

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    policy: "kebijakan bisnis yang berlaku saat ini"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form
        note: "opsional, konteks singkat"
      - path: "service/src/**/SomethingController.kt"
        role: backend-validation
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
```

If a flow's business rule turns out to be complex during this pass (several modes/variants, a
formula with multiple conditions, many exceptions) — don't try to cram it into one `invariants:`
line. Add `mechanics_doc: "docs/flows/<flow-name>.md"` and draft that companion doc with the full
narrative (see SKILL.md Core Rule 6) instead of leaving the rule under-documented.

Show the draft to the user for review before treating it as final, and include a coverage summary: total modules found in step 2's checklist vs. total flows registered — this should be 1:1 (call out any item skipped as pure infrastructure by name).
