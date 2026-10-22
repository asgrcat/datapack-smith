# Repository guide

- Start with `skills/datapack-smith/docs/README.md`; documentation is written in Japanese.
- Keep one Java Edition release per `skills/datapack-smith/docs/versions/<version>.md`.
- Treat Mojang release notes as primary and Minecraft Wiki as a cross-check.
- Preserve the shared headings and update indexes whenever version data changes.
- Treat `skills/datapack-smith` as the only source of skill documentation, templates, schemas, tools, `VERSION`, and `LICENSE`.
- Keep `SKILL.md` portable across Claude Code, Codex, and Cursor; use only shared Agent Skills frontmatter fields.
- Run the skill validator, profile check, and unit tests after changing public skill content.
- After pushing a Datapack Smith update, run `npx skills update datapack-smith --global --yes` to refresh the locally installed skill from GitHub, and report any update failure. Use a Node.js-enabled environment; the current installation is global.
- Before running npm/npx, verify that Node.js is a supported release with current security fixes. The October 21, 2026 fixes require at least 22.23.4, 24.22.1, or 26.12.1 within their respective release lines; consult newer official advisories as they appear. In this environment, use `mise exec node@24 -- node --version` to check and `mise exec node@24 -- npx skills update datapack-smith --global --yes` to update. Upgrade an outdated runtime before use; do not reuse old hard-coded Node.js paths from earlier sessions.
