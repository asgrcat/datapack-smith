# `.mcfunction` とコマンド仕様

この文書は Java Edition のデータパックから実行するコマンドを扱います。コマンドの全分岐はバージョンごとに変化するため、最終的な正本は対象バージョン server JAR が生成する `generated/reports/commands.json` です。生成方法は [`validation.md`](validation.md) を参照してください。

executor、位置、分岐、function結果、load/tick/scheduleの実行意味は [`execution-model.md`](execution-model.md)、scoreboardとstorageの設計は [`state-management.md`](state-management.md) で詳しく扱います。

`commands.json`のnode、argument parser、propertiesを人間向けに読む方法は [`reference/command-tree.md`](reference/command-tree.md) を参照してください。

## `.mcfunction` の字句規則

```mcfunction
# data/example/functions/demo.mcfunction（1.13〜1.20.6）
# data/example/function/demo.mcfunction（1.21以降）
say hello
execute as @a at @s run particle minecraft:happy_villager ~ ~1 ~
```

- UTF-8 のテキストで、拡張子は `.mcfunction`
- 1行に1つの完全なコマンドを書く
- 行頭の `/` は付けない。`/say hello` は function 内では誤り
- 最初の非空白文字が `#` の行はコメント。コマンド末尾への inline comment は書かない
- 空行、コマンド前後の空白は許容される
- reload 時に通常行を構文解析し、1行でも構文エラーがあればその function は読み込まれない
- command block の 32,500 文字制限より長い行も function には書けるが、実用上は分割する
- 1.13〜1.20.6 では `data/<namespace>/functions/<path>.mcfunction`
- 1.21 以降は `data/<namespace>/function/<path>.mcfunction`。旧 `functions` は使わない

### 1.20.2 以降: 行継続

行の最後の非空白文字を単独の `\` にすると、次の行を連結します。次行の前後空白は除去されます。

```mcfunction
execute as @a at @s run summon minecraft:armor_stand ~ ~ ~ \
{Invisible:1b,Marker:1b}
```

1.20.1 以前へ対応する基底 function では使えません。

### 1.20.2 以降: function macro

最初の非空白文字が `$` の行は macro 行です。`$(key)` を呼出時の compound NBT で置換し、その結果を実行時に構文解析します。

```mcfunction
# example:teleport_up
$teleport @s ~ ~$(height) ~
```

```mcfunction
function example:teleport_up {height:10}
function example:teleport_up with storage example:args current
```

- key に使える文字は `A-Z a-z 0-9 _`
- 使用する全 key が必要。不足または置換後の構文エラーでは function 全体を実行しない
- string は引用符なし、数値は型 suffix なし、list/compound/array は canonical SNBT として挿入される
- 外部入力を macro の command/selector/resource location 位置へ無検証で挿入しない。文字列連結ではなく、許可リストを storage へ書く
- macro は文字列テンプレートであって型安全な引数ではない

## 引数の読み方

| 表記 | 意味 | 例 |
|---|---|---|
| `literal` | その文字をそのまま書く | `run`, `entity`, `add` |
| `<name>` | 必須引数 | `<targets>` |
| `[name]` | 末尾の省略可能引数 | `[scale]` |
| `a\|b` | いずれか一つ | `if\|unless` |
| `...` | もう一つの完全なコマンド | `execute ... run ...` |

座標、範囲、resource location、selector、block state、item stack、text componentの詳細とバージョン境界は [`reference/command-arguments-and-selectors.md`](reference/command-arguments-and-selectors.md) を正本とします。NBT／SNBTは [`reference/nbt-snbt-and-data.md`](reference/nbt-snbt-and-data.md)、text componentは [`reference/text-components.md`](reference/text-components.md)を併用してください。

引数が同じ文字列に見えてもparserが異なる場合があります。`entity`と`entities`、IDとtag対応holder set、integer rangeとfloat rangeを`reports/commands.json`で区別します。

| selector | 互換性上の境界 |
|---|---|
| `@n` | 最寄り entity。1.21 以降 |

## function の起動

```mcfunction
function example:init
function #example:all_handlers
schedule function example:later 20t replace
```

function は呼出元の entity、位置、回転、dimension、anchor を引き継ぎます。ある行の `/execute` による context 変更は、次の独立した行へ持ち越されません。

### `load` と `tick`

1.13〜1.20.6:

```text
data/minecraft/tags/functions/load.json
data/minecraft/tags/functions/tick.json
```

1.21 以降:

```text
data/minecraft/tags/function/load.json
data/minecraft/tags/function/tick.json
```

```json
{
  "values": [
    "example:load"
  ]
}
```

- `#minecraft:load`: world load または `/reload` 後に1回
- `#minecraft:tick`: 毎 tick の先頭
- 1.19.3 以降は load tag が tick tag より先に実行されることが明確化された
- 毎 tick 全 entity を走査する設計を避け、scoreboard、schedule、predicate で対象と頻度を絞る

## 実行制御

### `execute`

1.13 で現在の連結型へ全面改訂されました。

```mcfunction
execute as @a at @s if block ~ ~-1 ~ minecraft:gold_block run function example:on_gold
execute store result score #value example.tmp run data get storage example:data value 100
```

代表的な subcommand:

- context: `as`, `at`, `positioned`, `positioned as`, `rotated`, `rotated as`, `facing`, `align`, `anchored`, `in`
- 条件: `if|unless block`, `blocks`, `entity`, `score`, `predicate`, `data`
- 保存: `store result|success score|bossbar|storage|entity|block ...`
- 関係: `on <relation>`。追加時期と利用可能な relation はバージョンごとに確認
- 終端: `run <command>`

`as` は実行 entity だけを変え、位置は変えません。entity の位置も必要なら通常 `as <selector> at @s` とします。

### `return`

```mcfunction
# 1.20以降
execute unless score #ready example.state matches 1 run return 0
return 1

# 1.20.3以降
return run data get storage example:data result
return fail
execute if function example:check run say passed
```

- `return <value>` は 1.20 で追加
- `return run` と `execute if|unless function` は 1.20.2 正式リリースでは利用不可。開発途中で除かれ、1.20.3 で再導入
- 1.20.3 以降、通常の function は `return` しない限り result を持たない。`execute store ... run function` の旧挙動を前提にしない

## 状態管理

永続性、NBT path、migration、複数実行時の競合を含む実装は [`state-management.md`](state-management.md) を参照してください。

### scoreboard

objective、score holder、演算、未設定値、`execute store`、success/resultの詳細は [`reference/scoreboards-and-results.md`](reference/scoreboards-and-results.md) を正本とします。objective名とfake player名にはpack固有の接頭辞を付けます。

### command storage と `/data`

storage、NBT path、`/data`の変更操作、scoreboardとの変換は [`reference/nbt-snbt-and-data.md`](reference/nbt-snbt-and-data.md) を正本とします。storageは1.15以降で、内容はJSONではなくSNBTです。

### entity tag

```mcfunction
tag @s add example.active
tag @s remove example.active
execute if entity @s[tag=example.active] run function example:active
```

entity tag は resource location ではなく文字列で、保存 NBT の `Tags` に入ります。長期状態、scoreboard、advancement、predicate のどれを使うべきかを用途で分けます。

## 主要コマンドのバージョン境界

この表はデータパック実装へ直接影響する追加・削除です。同じコマンド内の細かな branch 追加は各バージョンファイルを参照してください。

| 正式リリース | 追加・変更 |
|---|---|
| 1.13 | `/advancement`, `/bossbar`, `/data`, `/datapack`, `/execute` 再設計、`/function`, `/reload`, function tag、`/tag`, `/team`。`/blockdata`, `/entitydata`, `/execute` 旧構文等を削除 |
| 1.13.1 | `/forceload` |
| 1.14 | `/data modify`, `/loot`, `/schedule`, `/teammsg` |
| 1.15 | `/data ... storage`、`/execute store ... storage`、`/schedule clear` |
| 1.16 | `/attribute`, `/locatebiome` |
| 1.17 | `/item` を追加し `/replaceitem` を削除 |
| 1.18.2 | `/locate` が configured structure/tag を取るよう変更 |
| 1.19 | `/place`、`/locate biome`。`/locatebiome` を `/locate` へ統合 |
| 1.19.3 | `/fillbiome`、`execute positioned over <heightmap>` 等 |
| 1.19.4 | `/damage`, `/ride`、`data modify ... string`、execute 条件の追加 |
| 1.20 | `/return <value>` |
| 1.20.2 | `/random`、function macro。正式リリースでは `return run` と `execute if function` は利用不可 |
| 1.20.3 | `/tick`、`return run`, `return fail`, `execute if|unless function` |
| 1.20.5 | `/transfer` |
| 1.21.2 | `/rotate` |
| 1.21.5 | `/test` と GameTest data |
| 1.21.6 | `/dialog`, `/version`, `/waypoint`, `/datapack create` |
| 1.21.9 | `/fetchprofile`、world border の dimension 別管理 |
| 1.21.11 | `/stopwatch`, `execute if|unless stopwatch`。gamerule を registry 化し全名称を namespaced snake_case へ変更 |
| 26.1 | `/time` が world clock/timeline 対応へ変更 |
| 26.2 | `/unpublish`、team/waypoint の色名を lowercase snake_case のみに制限 |

### 26.3開発バージョン

| launcher ID | 追加・変更 |
|---|---|
| 26.3-snapshot-1 | `/item` と `execute if|unless items` をslot source化。`give`／`tick`の失敗通知と`team join|leave`のresultを修正 |
| 26.3-snapshot-2 | command tree固有差分なし |
| 26.3-snapshot-3 | `/posteffect add|clear|list|remove`、`/place feature`のinline feature |
| 26.3-snapshot-4 | sign click eventを既定無効化。`spreadplayers`の安全判定をblock tag化 |
| 26.3-snapshot-5 | command tree固有差分なし |
| 26.3-snapshot-6 | `/publish`から`gamemode`引数を削除 |
| 26.3-snapshot-7 | `/swing`へ`whack`／`stab` animationとdurationを追加。playerのattack strengthをresetしないよう変更 |
| 26.3-snapshot-8 | command tree固有差分なし（Snapshot 7と生成済み`commands.json`が同一） |
| 26.3-snapshot-9 | command tree固有差分なし（Snapshot 8と生成済み`commands.json`が同一） |
| 26.3-snapshot-10 | `/compute`と`data modify ... compute`を追加。`/swing`へ`none` animationを再追加 |
| 26.3-pre-1 | `/compute <target> integer|float ...`と`data modify ... compute <target> integer|float ...`へ変更。provider評価失敗時はコマンドも失敗 |

開発バージョンのcommandは変更中です。正式リリース表の「現行コマンド」へ合成せず、対象IDの`commands.json`を正本にします。

26.3-pre-1の`/compute`と`data modify ... compute`で使うinteger／float providerの全type、演算規則、resource例は [`reference/number-providers.md`](reference/number-providers.md) を参照してください。

## 現行コマンドの分類

26.2 の通常 command set を、AI が用途を選ぶために分類します。対象バージョンに存在するかは上表と `commands.json` で制限してください。

| 分類 | コマンド |
|---|---|
| flow/function | `execute`, `function`, `return`, `schedule`, `reload`, `datapack`, `random`, `tick` |
| state/NBT | `data`, `scoreboard`, `tag`, `bossbar`, `gamerule`, `stopwatch`, `time` |
| item/loot/recipe | `clear`, `give`, `item`, `loot`, `recipe`, `enchant` |
| block/world | `setblock`, `fill`, `clone`, `fillbiome`, `place`, `forceload`, `worldborder`, `locate` |
| entity | `summon`, `kill`, `damage`, `effect`, `attribute`, `ride`, `rotate`, `teleport`, `spreadplayers` |
| player/UI | `advancement`, `title`, `tellraw`, `playsound`, `stopsound`, `particle`, `dialog`, `waypoint`, `spectate` |
| testing/admin | `test`, `version`, `jfr`, `debug`, `perf`, `transfer`, `publish`, `unpublish` |

`ban`, `op`, `save-*`, `stop`, `whitelist` など専用サーバー管理コマンドも command graph にはありますが、通常のゲームプレイ用データパックが依存すべきではありません。function の許可レベルは singleplayer/LAN では通常 2、専用サーバーでは `function-permission-level` の設定に制限されます。

## 失敗、success、result

parse不能、runtime failure、success、result、voidは別の状態です。保存・分岐・functionの戻り値を含む詳細は [`reference/scoreboards-and-results.md`](reference/scoreboards-and-results.md) を参照し、command固有resultは実ゲームで確認します。

## 参照

- [Minecraft Wiki: Commands](https://minecraft.wiki/w/Commands)
- [Minecraft Wiki: Function](https://minecraft.wiki/w/Function_(Java_Edition))
- [Minecraft Wiki: Target selectors](https://minecraft.wiki/w/Target_selectors)
- [Minecraft Wiki: `/execute`](https://minecraft.wiki/w/Commands/execute)
- [Minecraft Wiki: `/data`](https://minecraft.wiki/w/Commands/data)
- [Minecraft Wiki: `/function`](https://minecraft.wiki/w/Commands/function)
- [Mojang: Java Edition 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2)
- [Mojang: Java Edition 1.20.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-3)
