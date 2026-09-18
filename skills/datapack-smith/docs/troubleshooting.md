# 読み込み・実行失敗の診断

まず対象のexact version、project設定、実行したcommand、最初のerrorを確認します。後続の`unknown function`が、先行するfunction parse errorの結果である場合があります。形式番号だけを書き換えて警告を消す修正はしません。

## 症状から切り分ける

| 症状 | 確認する証拠 | 修正・次の検査 |
|---|---|---|
| `python: can't open file` | `SKILL.md`の設置先、実行cwd | `<harness-root>/tools/datapack_harness.py`を絶対pathで呼ぶ。projectは利用者repository側 |
| profile未対応 | `target_version`とversion索引 | 完全一致のIDへ確認。未収録IDを近い値へ変換しない |
| project-check失敗 | ERRORに示されたfield | schemaの必須5 field、相対path、対応範囲、開発targetのexperimental設定を直す |
| packがavailable一覧にも出ない | worldの`datapacks/`、zip直下 | `pack.mcmeta`の階層・JSON・extensionを確認。zip内の余分な親folderを外す |
| availableだがenabledではない | `/datapack list available`と`enabled` | 実際のpack IDと有効化状態を確認。自動的に本番packを切り替えない |
| reload成功でも処理が始まらない | load/tick tag、valuesのID | 1.21境界の`tags/functions`と`tags/function`、function path、tag参照切れを確認 |
| `Unknown function` | 最初のparse error、ID、folder | 先頭`/`、BOM、導入前の構文、参照先の定義、外部依存packを確認 |
| `@s`が無反応／位置が違う | 呼出元のexecutor・dimension | load/tick/console/scheduleではplayerを明示。`as`は位置を変えず、`at`はexecutorを変えない |
| cooldown・状態判定が発火しない | `scoreboard players get` | 未設定と0を分ける。objective作成と`add ... 0`の順を確認 |
| rewardが一度しか動かない | criterion完了状態、revoke経路 | 反復eventだけをrevoke。報酬副作用はrevokeで巻き戻らない |
| rewardが重複する | 複数selector、状態遷移、再入 | generationと処理済み状態、状態更新順、同tickの重複入口を確認 |
| JSONはparseできるがresourceが無効 | serverのcodec error | 対象versionのfield、discriminator、型、loot context、参照種別を確認 |
| item/text/recipeが移行後に壊れる | 入出力versionのprofile | 1.20.5のcomponent、1.21.2のingredient、1.21.5のtext、26.3の参照/conditionを文脈別に変換 |
| worldgen変更が見えない | 新規world・未生成chunkか | registry loadに再起動が必要か確認。生成済みchunkがreloadで作り直されるとは扱わない |
| `UnsupportedClassVersionError` | `java -version`と必要Java major | [Java対応表](harness.md)に従い`--java`で対象JDKを指定 |
| report version mismatch | `.datapack-harness-report.json` | 正しいversion専用reportを指定。markerを書き換えて別versionを装わない |
| static成功なのにゲーム内で失敗 | static warningとserver log | 全Brigadier引数、codec、macro展開、runtimeをstaticが保証しない点を確認 |

## 最小の観測手順

次はゲーム内chatからの例です。consoleでは先頭`/`を外します。`example:*`は実際のIDへ置換します。

```text
/datapack list enabled
/reload
/function example:load
/execute as @s at @s run function example:player/tick
/scoreboard players get @s example.state
/data get storage example:state
```

この順序を無条件に実行するのではなく、調べるpackの入口契約を先に読みます。手動loadがmigrationや初期化を実行する場合があるため、再現用worldで確認します。consoleの`@s`はplayerではありません。player処理をconsoleから試すなら対象player名を指定します。storageは1.15以降です。

`execute store success score ...`と`execute store result score ...`を別の診断用scoreへ保存すれば、対象なし・変更なし・結果0を切り分けられます。診断objectiveもpack固有名にし、確認後に撤去します。

## report・server検査の証拠

- `reports`はdata generatorを実行し、worldは起動しません。JARを取得する場合があるため、既存生成物があれば先に使います。
- `server-test --log ... --expect-log ...`は隔離worldのreload区間でmarkerを確認します。markerはtest対象のload入口から出します。
- server検査失敗時も`--log`のファイルを読みます。timeout時はprocess状態、Java、最初のerrorを確認し、同じ起動を繰り返すだけにしません。
- player操作・client表示・offline復帰・world更新は`server-test`の自動操作対象ではありません。[完全例の受入表](worked-example.md)のように別の機能testを記録します。

残す記録は、対象ID、harness version、必要ならJAR SHA-1、実行command、終了code、log path、再現入力、期待値と実測値です。未実行の手順書を成功の証拠として扱いません。
