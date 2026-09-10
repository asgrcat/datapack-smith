# Datapack Smith

[日本語](README.md) | [English](README.en.md)

> **NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.**

Datapack Smith is an unofficial Agent Skill for designing, implementing, and validating data packs for Minecraft: Java Edition across official releases from 1.13 through 26.2 and the bundled 26.3 development versions. It resolves the target game version exactly and selects only the commands, data formats, and directory layout available in that version.

Claude Code, Codex, and Cursor use the same [`SKILL.md`](skills/datapack-smith/SKILL.md). The skill bundles the detailed specification, release profiles, templates, and validation harness.

## Add the skill

Give your AI the repository URL and ask it to add the skill:

> Add `skills/datapack-smith` from this repository as an Agent Skill: https://github.com/asgrcat/datapack-smith

The AI can identify the active environment and place the complete skill in its supported skill location. After it is added, invoke it explicitly with:

| Environment | Invocation |
|---|---|
| Claude Code | `/datapack-smith` |
| Codex | `$datapack-smith` |
| Cursor | `/datapack-smith` |

The AI may also select the skill automatically when a request matches its description.

## Versioning

Releases use the `YYYY.MM.N` CalVer scheme. `N` is the release sequence within a month and resets to `1` when the month changes. [`skills/datapack-smith/VERSION`](skills/datapack-smith/VERSION) is the authoritative skill version, and Git tags add a `v` prefix (for example, `v2026.08.1`).

## Example requests

> Build a Java Edition 1.21.5 data pack that records a score for each participant. Use the `event` namespace and complete static validation.

> Migrate this data pack from 1.20.4 to 1.20.5 and replace item NBT with data components.

> Determine whether this feature can support both 1.21.11 and 26.1, then separate the shared and release-specific parts.

If the game version, namespace, output path, or requested validation level is missing, the AI first infers it from the existing project and asks only for values it cannot determine safely.

## Capabilities

- Exact official release or bundled development version, data pack format, and directory-layout resolution
- Release-specific `.mcfunction`, JSON, SNBT, and resource-location generation
- References for item components, predicates, advancements, loot, recipes, world generation, and other data-driven formats
- Single-release implementation, existing-pack migration, and multi-release support
- State and migration design using scoreboards, storage, and entity tags
- Static checks, official server JAR report comparison, and optional server reload checks
- Clear reporting of completed and unexecuted validation

## Safety

- Unbundled snapshots, pre-releases, release candidates, and Bedrock Edition versions are not rounded to a nearby supported Java Edition version.
- Commands, IDs, and JSON fields that cannot be confirmed for the target release are not guessed.
- Official server JAR downloads and server startup are never implicit.
- The skill does not accept the Minecraft EULA, update existing worlds, or deploy to production servers for the user.
- Static checks are never reported as successful server validation.

## Skill contents

| Path | Purpose |
|---|---|
| [`skills/datapack-smith/SKILL.md`](skills/datapack-smith/SKILL.md) | Implementation and validation workflow followed by the AI |
| [`skills/datapack-smith/docs/README.md`](skills/datapack-smith/docs/README.md) | Specification index and version-selection workflow |
| [`skills/datapack-smith/docs/versions/README.md`](skills/datapack-smith/docs/versions/README.md) | Official release and data pack format index |
| [`skills/datapack-smith/docs/snapshots/README.md`](skills/datapack-smith/docs/snapshots/README.md) | Bundled 26.3 development version and data pack format index |
| [`skills/datapack-smith/docs/ai-authoring.md`](skills/datapack-smith/docs/ai-authoring.md) | Generation decisions and reporting contract |
| [`skills/datapack-smith/templates/datapack-project.json`](skills/datapack-smith/templates/datapack-project.json) | Project configuration template |
| [`skills/datapack-smith/tools/datapack_harness.py`](skills/datapack-smith/tools/datapack_harness.py) | Profile resolution and staged validation |

The documentation and templates are sufficient for design and generation. Where the bundled harness can run, it adds profile resolution and static checking. Checks that use an official server JAR run only after the user evaluates the need and execution conditions.

## Scope

This skill covers official Java Edition releases and explicitly bundled 26.3 development versions. Bedrock Edition, mod-loader-specific behavior, resource-pack-only formats, and unbundled development versions are out of scope.

Mojang release notes and the exact release's official server JAR are authoritative. Minecraft Wiki is used to cross-check boundaries and explanations.

Datapack Smith is published and maintained by [asgrcat](https://github.com/asgrcat). Please use [GitHub Issues](https://github.com/asgrcat/datapack-smith/issues) for contact and support.

See the repository-root [`LICENSE`](LICENSE). The skill distribution includes the same canonical file at [`skills/datapack-smith/LICENSE`](skills/datapack-smith/LICENSE).
