# Flow Map Init

Create or extend `FEATURE-MAP.yaml` for the current repo.

1. If `FEATURE-MAP.yaml` exists, read it first and extend or correct it. Do not overwrite.
2. Explore README, docs, architecture notes, routes, controllers, screens, services, migrations, and API docs.
3. Identify business flows implemented across more than one layer/service/app.
4. Start with 3 to 5 critical flows.
5. Find concrete touchpoints with `rg` and verify each path exists.
6. Write the small supported YAML subset only. Do not use YAML anchors, multiline strings, or complex nesting.

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

Show the draft to the user for review before treating it as final.
