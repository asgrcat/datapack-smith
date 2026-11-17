---
type: "Reference"
title: "コマンド木と引数parser"
description: "`commands.json`、argument parser、構文分岐、result検証"
tags: ["minecraft-java", "reference", "command-tree"]
sources: [{"resource": "/sources.md", "title": "資料と検証方針", "id": "source-d11281c5d9"}, {"id": "snapshot-9", "resource": "/snapshots/26.4-snapshot-9.md", "title": "Java Edition 26.4 Snapshot 9"}]
---

# コマンド木と引数parser

正式26.3向けでは、以下の旧バージョンの例に先立ち[26.3確定仕様と移行表](26.3-migration.md)を適用します。旧field・配置をそのまま26.3へ生成せず、各例の対象バージョンを維持してください。

`.mcfunction`の字句と代表構文は [`../commands.md`](../commands.md)、座標・selector・resource等の引数は [`command-arguments-and-selectors.md`](command-arguments-and-selectors.md)、success／resultの保存は [`scoreboards-and-results.md`](scoreboards-and-results.md)、executor、position、forkは [`../execution-model.md`](../execution-model.md) を参照します。この文書は、対象バージョンの`commands.json`を完全な構文リファレンスとして読む方法を説明します。

## node

以下の例はSnapshot 7までの形式です。Snapshot 8の配置は[新しいcommand report](#264-snapshot-8のcommand-report)を参照してください。

```json
{
  "type": "argument",
  "parser": "brigadier:integer",
  "properties": {
    "min": 0,
    "max": 15
  },
  "executable": true,
  "children": {}
}
```

| field | 説明 |
|---|---|
| `type` | `root`、固定語の`literal`、引数の`argument` |
| `parser` | argument nodeが使うparser ID |
| `properties` | min/max、単数／複数、resource registry等の追加制約 |
| `executable` | そのnodeでcommandを終了できるか |
| `children` | 続けられるliteral／argument |
| `redirect` | 別nodeへ処理を移すpath |

rootからchildrenを辿り、`executable: true`へ到達するpathだけが完結した構文です。Wikiの角括弧表記を先に解釈してnodeを省略しません。

## Brigadier parser

| parser | properties | 説明 |
|---|---|---|
| `brigadier:bool` | なし | `true`または`false` |
| `brigadier:integer` | 任意の`min`、`max` | 32-bit integer |
| `brigadier:long` | 任意の`min`、`max` | 64-bit integer |
| `brigadier:float` | 任意の`min`、`max` | floating point |
| `brigadier:double` | 任意の`min`、`max` | double |
| `brigadier:string` | `type` | `word`、`phrase`、`greedy`。greedyは残りの行全体 |

## 主なMinecraft parser

実際のparser IDとpropertiesは対象バージョンのreportを優先します。

| 分類 | parserの例 | 説明・確認点 |
|---|---|---|
| entity | `minecraft:entity` | `amount`がsingle／multiple、`type`がplayers／entities |
| game profile | `minecraft:game_profile` | player名またはselector等 |
| position | `minecraft:block_pos`, `vec3`, `vec2`, `column_pos` | absolute、relative、local座標の許可 |
| rotation | `minecraft:rotation` | yaw／pitch |
| range | `minecraft:int_range`, `float_range` | `min..max`の片端省略 |
| block | `minecraft:block_state`, `block_predicate` | block ID、state、NBT、tag許可 |
| item | `minecraft:item_stack`, `item_predicate` | item componentの対象バージョン境界 |
| NBT | `minecraft:nbt_compound_tag`, `nbt_tag`, `nbt_path` | SNBTとNBT pathを区別 |
| text | `minecraft:component`, `message`, `style` | text componentの1.21.5境界 |
| resource | `minecraft:resource`, `resource_key` | propertiesのregistryに属する単一ID |
| resource/tag | `minecraft:resource_or_tag`, `resource_or_tag_key` | `#`tagを許可 |
| objective | `minecraft:objective`, `objective_criteria` | scoreboard objective／criterion |
| score holder | `minecraft:score_holder` | 単数／複数property |
| operation | `minecraft:operation` | scoreboard operation |
| slot | `minecraft:item_slot`, `item_slots`, `slot_source` | slot ID、複数slot、26.2のslot source |
| time | `minecraft:time` | tickとunit suffix、min制約 |
| function | `minecraft:function` | function ID／tag／inline functionのバージョン差 |
| UUID | `minecraft:uuid` | UUID |
| angle | `minecraft:angle` | degree |
| color | `minecraft:color` | 対象バージョンのcolor名制約 |

`resource`と`resource_or_tag`、`entity`のsingleとmultipleを最も注意します。文字列として同じに見えてもargument parserの制約は異なります。

## commandの意味

構文木は次を保証しません。

- command実行に必要なpermission level
- chunkがload済みか
- 対象0件時の成否
- success値とresult値
- forkした各branchの集約
- stateを実際に変更しなかった場合の結果
- consumer固有codecを持つinline JSON／SNBTの妥当性

これらは同じ正式リリースの公式リリースノート、実server、機能テストで確認します。

## バージョン差分を取る

```text
previous commands.json root children
  vs
target commands.json root children
```

root commandの追加だけでなく、同じroot以下のnodeを再帰的に比較します。

```text
[ ] literalの追加・削除
[ ] argument parser IDの変更
[ ] parser propertiesの変更
[ ] executable nodeの移動
[ ] redirect先の変更
[ ] result semanticsのrelease note
```

同じdata pack formatでもcommand treeが変わる正式リリースがあります。format番号だけでcommand構文を共有しません。

## 26.2で特に確認する境界

- team／waypoint colorはlowercase snake_case
- advancement grant／revokeのresult報告
- `execute on owner`のowner関係
- `/unpublish`
- 26.1からのworld clock対応`/time`
- 1.21.11からのnamespaced gamerule、`/stopwatch`
- 1.21.6からの`/dialog`、`/waypoint`
- 1.21.5以降のSNBT text component
- 1.20.5以降のitem component patch

## 検証

```text
[ ] rootからexecutable nodeまでの全pathを辿った
[ ] argument parserのpropertiesを保持した
[ ] resourceとresource-or-tagを区別した
[ ] single targetとmultiple targetを区別した
[ ] inline JSON／SNBTを対象codecで検証した
[ ] success、result、permission、chunk条件を機能テストした
```

## 26.4 Snapshot 8のcommand report

`26.4-snapshot-8`では引数の情報がnode直下の`parser`／`properties`から`argument`へ移ります。引数型は`argument.type`に、`min`／`max`／`registry`／`context`などは`argument`直下に置かれます。nodeの`type: "argument"`と引数の`argument.type`を区別します。

```json
{
  "type": "argument",
  "argument": {
    "type": "minecraft:integer",
    "max": 1000,
    "min": 1
  },
  "executable": true,
  "permissions": {
    "type": "minecraft:always_pass"
  }
}
```

- 数値・bool・文字列のparser IDは`brigadier:`から`minecraft:`へ変わります。たとえば`brigadier:integer`は`minecraft:integer`です。`resource_key`／`resource_or_tag_key`は対応する`resource`／`resource_or_tag`へ変わります。
- `permissions`はそのnodeに記録された権限条件です。1つのnodeが`always_pass`でも、経路上の他nodeや実行環境の制約を確認します。
- `custom_suggestion`は補完情報です。たとえば`advancement grant ... only ... <criterion>`のcriterionは`{"type": "minecraft:ask_server"}`です。候補の表示と構文の受理を混同しません。
- `argument.context`はcontext依存のfloat／int provider、loot modifier／predicate／table、slot sourceで使います。判定は[context検証](../validation.md#264-snapshot-8のcontext検証)を参照してください。
- 正規表現用の`minecraft:pattern`はserver-side mod／plugin向けに追加されたparserです。vanillaの生成command treeでは使われていません。

Snapshot 7からnode path・node type・実行可能位置・redirectに差分はありません。report形式の差分をコマンドの追加・削除と判断しません。

## 26.4 Snapshot 9の文字列report修正

`argument.type`の`minecraft:string`は`minecraft:word`／`minecraft:quoted_string`／`minecraft:greedy_string`へ分離されます。Snapshot 8では文字列のmodeと引数typeを同じfieldへ記録していた不具合（MC-313181）があり、reportの`type`だけで受理する文字列を決めません。

Snapshot 9のtag名はword、datapack名はquoted string、helpのcommandはgreedy stringです。以前のreportと単純なfield比較をして、すべてを新しいコマンド構文と判断しません。`schedule`や`title ... times`のtime引数には`min: 0`も記録されます。runtimeのerrorや後続引数の修正は対象profileを参照してください。[^snapshot-9]

[^snapshot-9]: [Java Edition 26.4 Snapshot 9の公式資料・JAR照合](../snapshots/26.4-snapshot-9.md)
