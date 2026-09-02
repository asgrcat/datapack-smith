# NBT、SNBT、`/data`

この文書はJava EditionのNBT値、SNBT表記、NBT path、`/data`、command storage、`execute store`を扱います。JSON resource、item data component、text componentは外側codecが異なるため分離して説明します。

## NBTとSNBT

NBTは型付きbinary tree、SNBTはそのtext表現です。

| NBT型 | SNBT例 |
|---|---|
| byte | `1b` |
| short | `2s` |
| int | `3` |
| long | `4L` |
| float | `1.5f` |
| double | `1.5d` |
| string | `"text"` |
| list | `[1,2,3]` |
| compound | `{enabled:1b,count:3}` |
| byte array | `[B;1b,0b]` |
| int array | `[I;1,2,3]` |
| long array | `[L;1L,2L]` |

JSONには数値型suffix、typed array、unquoted key、single quoteを持ち込みません。SNBTで許可される表現も対象バージョンと外側command parserで制限されます。

## 1.21.5のSNBT拡張

1.21.5ではheterogeneous list、trailing comma、boolean／UUID等の表現が拡張されました。古いバージョン向けpackへ逆輸入しません。

```snbt
{values:[1,"two",{three:3}],enabled:true,id:uuid("00000000-0000-0000-0000-000000000000"),}
```

この例は説明用SNBTです。JSON code fenceとして扱いません。値を保存した後のcanonical表現は入力文字列と完全一致しない場合があります。

## `/data`のtarget

| target | 例 | 特性 |
|---|---|---|
| entity | `entity @s` | selectorは単一対象が必要なbranchが多い。player NBTは直接変更不可 |
| block | `block ~ ~ ~` | loaded block entityが必要 |
| storage | `storage example:state` | world共有で永続するnamespaced storage |

```mcfunction
data get storage example:state
data get entity @s Pos
data get block ~ ~ ~ Items
```

`data get`の表示文字列とcommand resultは別です。数値pathではscaleした数値がresultになり得ますが、compoundやlist全体をscoreへ保存できるとは仮定しません。

## NBT path

| 構文 | 例 | 意味 |
|---|---|---|
| child | `config.schema` | compound child |
| quoted key | `"key.with.dot"` | 特殊文字を含むkey |
| index | `queue[0]` | listの先頭 |
| negative index | `queue[-1]` | listの末尾側 |
| all elements | `queue[]` | 全要素 |
| element match | `players[{active:1b}]` | patternに一致する要素 |
| compound match | `{id:"minecraft:pig"}` | 現在compoundのpattern match |

1.14で複数match、negative index、list／compound pattern等が拡張されました。pathは0件、1件、複数件を返し、commandごとに許容件数が異なります。

```mcfunction
data get storage example:state queue[-1]
data remove storage example:state queue[{done:1b}]
```

外部入力からpath文字列を組み立てるより、固定pathとpatternを使います。macroへpathを挿入する場合はkey／indexの許可範囲を検証します。

## `data modify`

| operation | 用途 |
|---|---|
| `set` | 対象値を置換 |
| `merge` | compoundを再帰merge |
| `append` | list末尾へ追加 |
| `prepend` | list先頭へ追加 |
| `insert` | 指定indexへ追加 |

source:

| source | 用途 |
|---|---|
| `value <snbt>` | commandに直接書いた値 |
| `from <target> <path>` | 別NBT値をcopy |
| `string <target> <path> [start] [end]` | source stringのsubstring |
| `compute ...` | 26.3-snapshot-10以降、number provider結果 |

```mcfunction
data modify storage example:state config set value {schema:2,enabled:1b}
data modify storage example:state queue append value {type:"example:job",ticks:20}
data modify storage example:state copy set from entity @s Inventory
data remove storage example:state queue[0]
```

`merge`はlistを連結する操作ではありません。型不一致、source path欠落、複数match、index範囲外はruntime failureになり得ます。複数commandをtransactionとしてrollbackする仕組みはありません。

## Command storage

storageは1.15以降です。storage ID自体はnamespacedですが、内部schemaはpackが管理します。

```text
example:state
├── schema
├── config
├── runtime
└── queue
```

- load時に毎回rootを上書きしない
- schema versionを持ち、既存値をmigrationする
- 一時値と永続設定を同じpathへ混在させない
- multiplayerのplayer別値にはUUID等の安定keyを使うか、scoreboardとの役割を分ける
- uninstall時に削除するstorageと利用者dataを残すstorageを区別する

## `execute store`

```mcfunction
execute store result score #value example.tmp run data get storage example:state count
execute store success storage example:state ok byte 1 run function example:try
execute store result storage example:state value int 1 run scoreboard players get @s example.value
```

| branch | 保存値 |
|---|---|
| `success` | 通常0または1の成否 |
| `result` | command固有のinteger result |

NBTへ保存するときは`byte`、`short`、`int`、`long`、`float`、`double`とscaleを指定します。丸め、overflow、NaN相当、command failureを対象バージョンで確認します。先行する副作用が後続の`store`失敗で取り消されるとは仮定しません。

## Item dataの境界

### 1.20.4以前

item固有dataはstackの`tag` compoundに置きます。

```mcfunction
give @s minecraft:stone{example:{level:1}}
```

### 1.20.5以降

標準機能はtyped data component、任意dataは`minecraft:custom_data`へ移します。

```mcfunction
give @s minecraft:stone[minecraft:custom_data={example:{level:1}}]
```

旧item `tag`をcomponent patchへそのまま移しません。名前、lore、enchantment、damage、attribute等は対応するtyped componentを使います。

## Block／entity data

- player NBTは`/data modify entity`で直接変更しない
- entity typeやblock entity typeの`id`と保存dataを一致させる
- 1.21.4以降の`entity_data`／`block_entity_data` componentは対象type不一致を利用しない
- 1.21.5のequipment、attribute、variant等のrenameを対象profileから適用する
- block置換時にNBT未指定なら既存block entity dataを保持するバージョンがある。明示消去と保持を分ける

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.13 | `/data`、Brigadier NBT parser、entity／block target |
| 1.14 | `/data modify`、複数match NBT path |
| 1.15 | command storageと`execute store ... storage` |
| 1.20.2 | mob effect NBTをsnake_case／namespaced IDへ変更 |
| 1.20.5 | item `tag`からdata componentへ全面移行 |
| 1.21.4 | furnace等のblock entity field rename、data componentのtype一致を厳格化 |
| 1.21.5 | heterogeneous list、text／equipment等のNBT大変更 |
| 1.21.6 | JSONをstrict化。SNBT拡張と混同しない |
| 26.3-snapshot-10 | `data modify ... compute`を追加 |

## 生成規則

- target versionと対象の保存codecを固定する
- JSON、SNBT、text component、data componentを別型として扱う
- pathの0件／1件／複数件とsource型不一致を設計する
- compound mergeとlist操作を混同しない
- player NBTを直接変更するcommandを生成しない
- itemの旧`tag`と新component patchをversionで分離する
- state更新を複数commandで行う場合は途中失敗から復旧できる順序にする

## 検証

`data get`で実際の保存型を確認し、`execute store success/result`を別scoreへ記録します。通常値だけでなく、欠落path、複数match、空list、型不一致、数値境界、offline entity、unloaded blockをtestします。

## 出典

- 各 [`../versions/<version>.md`](../versions/README.md) のNBT／command差分
- 対象server JARの`commands.json`と実際の`data get`出力
