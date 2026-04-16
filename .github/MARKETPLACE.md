# Publishing COG to Claude Code Marketplaces

This guide covers the packaging metadata and release checks for publishing COG.

## Packaged Metadata

COG ships marketplace metadata in two files:

- **`.claude-plugin/plugin.json`** — canonical manifest for the packaged Claude Code surface
- **`marketplace-entry.json`** — lightweight catalog entry for marketplace maintainers

Current packaged version: **3.4.1**

## Surface Model

COG is a **multi-agent package**, not a single-surface plugin:

| Surface | Coverage |
|---|---:|
| Claude Code (`.claude/skills/`) | 17 native skills |
| Universal docs (`AGENTS.md`) | 17 documented commands |
| Kiro (`.kiro/powers/`) | 7 core powers |
| Gemini CLI (`.gemini/commands/`) | 7 core commands |

For the detailed contract, see [`docs/AGENT-SUPPORT.md`](../docs/AGENT-SUPPORT.md).

## Before You Publish

Run the packaging validator from the repo root:

```bash
./scripts/validate-agent-surface.sh
```

This catches the most common release mistakes:
- invalid JSON in manifests
- skill paths listed in the manifest but missing on disk
- plugin skill counts drifting from `.claude/skills/`
- `AGENTS.md` missing commands that the manifest claims to ship
- wrong `AGENTS.md` filename casing in packaging docs
- version mismatches across `COG-VERSION`, `plugin.json`, and `marketplace-entry.json`

## Manual Validation Commands

If you want extra spot checks:

```bash
python3 -m json.tool .claude-plugin/plugin.json > /dev/null
python3 -m json.tool marketplace-entry.json > /dev/null
find .claude/skills -name SKILL.md | wc -l
find .kiro/powers -name POWER.md | wc -l
find .gemini/commands -type f | wc -l
```

## Installation Guidance for Marketplace Descriptions

Preferred install flow:

```bash
git clone https://github.com/huytieu/COG-second-brain.git
cd COG-second-brain
# Open in Claude Code, Kiro, Gemini CLI, Codex, or another AGENTS-compatible agent
```

Do **not** describe installation as copying only `.claude/` into another folder — COG is a full vault/repo layout, not just a loose skill pack.

## Release Checklist

1. Bump `COG-VERSION`
2. Update `.claude-plugin/plugin.json`
3. Update `marketplace-entry.json`
4. Update `CHANGELOG.md`
5. Add any new framework files to `FRAMEWORK_FILES` in `cog-update.sh`
6. Run `./scripts/validate-agent-surface.sh`
7. Smoke test onboarding from a clean clone

## Support Links

- Issues: https://github.com/huytieu/COG-second-brain/issues
- Discussions: https://github.com/huytieu/COG-second-brain/discussions
- Setup guide: https://github.com/huytieu/COG-second-brain/blob/main/SETUP.md
