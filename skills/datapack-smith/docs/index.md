---
okf_version: "0.2"
---

# Datapack Smith knowledge

<!-- tools/okf_index.py で生成。本文とmetadataの正本は各concept文書。 -->

## 更新履歴

- [更新履歴](log.md) - この範囲のknowledge更新記録。

## ディレクトリ

- [json-parameters](json-parameters/index.md) - JSON family別の値の意味とバージョン境界。
- [reference](reference/index.md) - データ種別ごとの配置、field、値型、参照関係。
- [snapshots](snapshots/index.md) - 明示指定時に使う開発バージョンの完全一致プロファイル。
- [versions](versions/index.md) - 正式リリースの完全一致プロファイルとdata pack format。

## Example

- [完全例: player別の入力とcooldown](worked-example.md) - 1.21.5向けのplayer別cooldown packの全ファイルと機能test。

## Playbook

- [AI データパック生成契約](ai-authoring.md) - project設定から対象仕様を解決し、データパックを生成・検証する決定手順。
- [互換性と複数バージョン対応](compatibility.md) - 後方互換、前方互換、overlayと複数バージョンへの移行方針。
- [Datapack Smith仕様リファレンス](guide.md) - 対象バージョンの選択、仕様の参照順序、実装と検証の進め方。
- [実行ハーネス](harness.md) - プロファイル解決、JAR取得、report生成、静的検査とserver検証の実行手順。
- [実装設計と受入条件](implementation-contract.md) - 要件、入口、状態、resource依存、運用と受入条件を決定する手順。
- [読み込み・実行失敗の診断](troubleshooting.md) - load、実行、移行の症状から原因と確認方法を特定する手順。
- [対象バージョンでの生成と検証](validation.md) - 対象バージョンの公式JARからcommand tree、registry、vanilla JSONを検証する方法。

## Reference

- [進捗とplayer event](advancements.md) - advancementのcriteria、requirements、rewardとplayer eventの設計。
- [`.mcfunction` とコマンド仕様](commands.md) - mcfunctionの字句規則、コマンド引数、実行文脈とバージョン境界。
- [追加コンテンツとデータパック活用](content-hooks.md) - block、entity、itemをデータパックから観測・制御する手段と制約。
- [コマンド実行モデル](execution-model.md) - executor、位置、分岐、functionの結果、load・tick・scheduleの挙動。
- [複合gameplay要件の可否判定](gameplay-requirements.md) - 複合gameplay要件の実現可否、状態遷移、競合とcleanupの設計。
- [実装パターン](implementation-patterns.md) - 状態機械、timer、event queue、API、性能とtestの実装パターン。
- [JSON、SNBT、データ種別](json-formats.md) - pack.mcmeta、データ種別の配置、JSONとSNBTの基本構造。
- [OKF knowledgeの構造と参照方法](okf.md) - Datapack SmithのOKF v0.2バンドル、metadata、索引と更新手順。
- [資料と検証方針](sources.md) - Mojangの一次資料、公式JAR、Minecraft Wikiの優先順位と検証方針。
- [状態管理](state-management.md) - scoreboard、storage、entity tagによる永続状態とmigration。
