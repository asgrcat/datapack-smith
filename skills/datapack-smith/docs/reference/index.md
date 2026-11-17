# reference

<!-- tools/okf_index.py で生成。本文とmetadataの正本は各concept文書。 -->

## Playbook

- [データパック書式リファレンス](guide.md) - データ種別ごとの配置、field、値型、既定値と参照関係を調べる入口。

## Reference

- [26.3 確定仕様と26.2からの移行](26.3-migration.md) - 正式26.3のfield・配置・recipe・worldgen確定仕様、26.2からの移行
- [Block transformerとblock state provider](block-transformation.md) - block transformer、block state provider、rule、配置、migration
- [Command引数、座標、selector](command-arguments-and-selectors.md) - 座標、範囲、resource location、selector、block state、item stack、macro
- [コマンド木と引数parser](command-tree.md) - `commands.json`、argument parser、構文分岐、result検証
- [item stack、component、predicate](components-and-predicates.md) - item stack、data component、entity component、predicate、advancement条件
- [データ種別カバレッジ](coverage.md) - 26.3の全データ種別、26.2履歴、説明先・正本・検証方法の対応表
- [Damage system](damage-system.md) - damage type、分類tag、source、predicate、item・enchantmentとの接続
- [ダイアログ、入力、アクション](dialogs-and-actions.md) - 1.21.6以降のdialog、body、input、button、dynamic action、安全性
- [Dispenserのデータ駆動behavior](dispense-behaviors.md) - 26.4 Snapshot 9のdispense_behavior registry、item component、動作順序とtype別field。
- [NBT、SNBT、`/data`](nbt-snbt-and-data.md) - NBT型、SNBT、NBT path、`/data`、storage、item境界
- [Context依存number provider](number-providers.md) - 正式26.3のcontext依存number provider、四則演算、丸め、三角関数、分岐、失敗条件とpre-3の演算変更
- [pack metadata、namespace、配置](pack-and-paths.md) - `pack.mcmeta`、namespace、resource location、ディレクトリ、tag、overlay
- [recipe、loot、item modifier、GameTest](recipes-loot-and-tests.md) - recipe、loot table、item modifier、GameTest
- [Registry element、参照、holder set](registry-elements.md) - registry ID、tag、inline entry、list、holder set、参照の安定性
- [データ駆動registryの書式](registry-formats.md) - 26.2でデータパックから定義できるregistry entryの配置とパラメータ
- [Scoreboardとcommand result](scoreboards-and-results.md) - objective、score holder、整数演算、success、result、`execute store`
- [Slot source](slot-sources.md) - 1.21.11／26.3のslot source、command・lootとの接続、全type
- [サウンドとパーティクル](sounds-and-particles.md) - `playsound`、`stopsound`、`particle`、resource pack境界、負荷
- [Structure NBT、jigsaw、worldgen structure](structures-and-jigsaw.md) - structure NBT、template pool、processor、structure set、jigsaw、GameTest
- [Text component](text-components.md) - text componentの内容、style、event、JSON／SNBT境界
- [対象バージョンからJSONキーを選ぶ](versioned-json.md) - 対象versionとconsumerからJSONキー・値型・配置を選ぶ境界表と対比例
- [dimension、environment attributes、timeline](world-and-environment.md) - `dimension`、`dimension_type`、biome、environment attributes、timeline、world clock
- [world generation](worldgen.md) - biome、feature、placement、noise、structure、dimension generator
