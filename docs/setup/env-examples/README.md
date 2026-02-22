# Environment Profile Examples

These files are intended for profile-based updates of `/a0/usr/.env` in a running `evetz_zero` container.

Rules:

- Empty values are placeholders and should be skipped by profile apply tooling.
- Non-empty values are intentional profile settings and should be applied.
- API key fields are intentionally present and empty in these examples.
- Each profile includes all known `A0_SET_*` keys from runtime settings (set or empty).

Profiles included:

- `profile_balanced_production.env`
- `profile_conservative_safety.env`
- `profile_high_throughput.env`
- `profile_intentionally_tight.env`

Related docs:

- `../../guides/autonomy-overview.md`
- `../../guides/autonomy-knobs-reference.md`
- `../../guides/autonomy-testing.md`

Use from repo root:

```bash
python3 apply_settings_profile.py --profile agent-zero/docs/setup/env-examples/profile_balanced_production.env
```

Optional:

```bash
python3 apply_settings_profile.py --profile agent-zero/docs/setup/env-examples/profile_intentionally_tight.env --dry-run
```
