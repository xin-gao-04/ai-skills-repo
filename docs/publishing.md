# Publishing Skills To Codex

These scripts publish repository-managed skills into the live Codex skills directory by combining:

- `shared/`
- `codex/`

The result is written to `~/.codex/skills/<skill-name>` on macOS and `%USERPROFILE%\.codex\skills\<skill-name>` on Windows.

Skills may live directly under `skills/` or inside one category layer such as `skills/investing-cn/<skill-name>` or `skills/engineering/<skill-name>`.

## Windows

Publish one skill:

```powershell
pwsh -File .\scripts\publish-to-codex.ps1 -SkillName stock-technical-trade-advisor
```

Publish all skills:

```powershell
pwsh -File .\scripts\publish-to-codex.ps1 -All
```

Custom destination:

```powershell
pwsh -File .\scripts\publish-to-codex.ps1 -SkillName stock-technical-trade-advisor -DestinationRoot C:\Users\<you>\.codex\skills
```

## macOS

Publish one skill:

```bash
chmod +x ./scripts/publish-to-codex.sh
./scripts/publish-to-codex.sh --skill stock-technical-trade-advisor
```

Publish all skills:

```bash
./scripts/publish-to-codex.sh --all
```

Custom destination:

```bash
./scripts/publish-to-codex.sh --skill stock-technical-trade-advisor --dest-root "$HOME/.codex/skills"
```

## Behavior

- `shared/` files are copied first
- `codex/` adapter files are copied second
- the target skill directory is replaced atomically via a temporary folder
- `claude/` files are not published into the Codex runtime folder
- the installed skill name is always the skill directory basename, regardless of category

## After Publishing

Restart Codex so it reloads the updated skills.
