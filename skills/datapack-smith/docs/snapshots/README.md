# 26.3 開発バージョンプロファイル一覧

このディレクトリは Java Edition 26.3 のsnapshot、pre-release、release candidateを、Mojang 公式 version manifest の ID へ完全一致させて扱います。開発バージョンは仕様変更・削除や world 破損の可能性があるため、正式リリースの [`../versions/README.md`](../versions/README.md) とは分離しています。version manifestではいずれも`type: snapshot`です。

各ファイルは直前のプロファイルを `inherits` し、その開発バージョンでの累積仕様を解決できます。`release_date` はこのディレクトリでは対象開発バージョンの公開日を表します。

| launcher ID | 公開日 | data pack format | 継承元 |
|---|---:|---:|---|
| [`26.3-snapshot-1`](26.3-snapshot-1.md) | 2026-06-23 | 108.0 | 26.2 |
| [`26.3-snapshot-2`](26.3-snapshot-2.md) | 2026-06-30 | 109.0 | 26.3-snapshot-1 |
| [`26.3-snapshot-3`](26.3-snapshot-3.md) | 2026-07-07 | 110.0 | 26.3-snapshot-2 |
| [`26.3-snapshot-4`](26.3-snapshot-4.md) | 2026-07-16 | 111.0 | 26.3-snapshot-3 |
| [`26.3-snapshot-5`](26.3-snapshot-5.md) | 2026-07-21 | 112.0 | 26.3-snapshot-4 |
| [`26.3-snapshot-6`](26.3-snapshot-6.md) | 2026-07-28 | 113.0 | 26.3-snapshot-5 |
| [`26.3-snapshot-7`](26.3-snapshot-7.md) | 2026-08-04 | 115.0 | 26.3-snapshot-6 |
| [`26.3-snapshot-8`](26.3-snapshot-8.md) | 2026-08-12 | 116.0 | 26.3-snapshot-7 |
| [`26.3-snapshot-9`](26.3-snapshot-9.md) | 2026-08-17 | 117.0 | 26.3-snapshot-8 |
| [`26.3-snapshot-10`](26.3-snapshot-10.md) | 2026-08-25 | 118.0 | 26.3-snapshot-9 |
| [`26.3-pre-1`](26.3-pre-1.md) | 2026-09-01 | 119.0 | 26.3-snapshot-10 |
| [`26.3-pre-2`](26.3-pre-2.md) | 2026-09-04 | 120.0 | 26.3-pre-1 |
| [`26.3-pre-3`](26.3-pre-3.md) | 2026-09-08 | 121.0 | 26.3-pre-2 |
| [`26.3-rc-1`](26.3-rc-1.md) | 2026-09-10 | 121.0 | 26.3-pre-3 |
| [`26.3-rc-2`](26.3-rc-2.md) | 2026-09-11 | 121.0 | 26.3-rc-1 |
| [`26.3-rc-3`](26.3-rc-3.md) | 2026-09-14 | 121.0 | 26.3-rc-2 |

## 使用上の制約

- `26.3`、`26.3-snapshot-10`、`26.3-pre-1`、`26.3-pre-2`、`26.3-pre-3`、`26.3-rc-1`、`26.3-rc-2`、`26.3-rc-3`を別のlauncher IDとして扱う
- 既存 world、本番 server、正式リリース用 pack の上書き検証に使わない
- `pack.mcmeta` は対象開発バージョンの format へ厳密に固定する
- 次の開発バージョンへ移るたびに公式 server JAR の report、reload、機能テストをやり直す
- 26.3 正式リリース後は、正式リリースプロファイルを新規作成し、開発バージョンの値をそのまま確定仕様にしない

## 出典

- [Mojang 公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Java Edition 26.3](https://minecraft.wiki/w/Java_Edition_26.3)
