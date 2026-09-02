# Repository guide

- Start with `skills/datapack-smith/docs/README.md`; documentation is written in Japanese.
- Keep one Java Edition release per `skills/datapack-smith/docs/versions/<version>.md`.
- Treat Mojang release notes as primary and Minecraft Wiki as a cross-check.
- Preserve the shared headings and update indexes whenever version data changes.
- Treat `skills/datapack-smith` as the only source of skill documentation, templates, schemas, tools, `VERSION`, and `LICENSE`.
- Keep `SKILL.md` portable across Claude Code, Codex, and Cursor; use only shared Agent Skills frontmatter fields.
- Run the skill validator, profile check, and unit tests after changing public skill content.
