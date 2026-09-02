# Command引数、座標、selector

この文書は`.mcfunction`で頻出するBrigadier引数の意味を扱います。完全なbranchとparser propertyは対象server JARの`reports/commands.json`を正本とし、ここでは生成判断と実行時の落とし穴をまとめます。

## Argument graphを先に確認する

commandは空白区切りの文字列だけでなく、literal nodeとargument nodeから成るgraphです。

```text
literal execute
└── literal as
    └── argument targets: minecraft:entity
        └── literal run
            └── argument command: brigadier:command
```

同じ見た目の`<target>`でもparserとpropertyが異なります。特に次を区別します。

- entity 1件／複数件
- player 1件／複数件
- element ID／elementまたはtag
- block position／3次元vector／rotation
- integer range／float range
- item stack／item predicate
- NBT compound／NBT path

## 座標

### 絶対座標

```mcfunction
setblock 10 64 -5 minecraft:stone
```

world座標です。整数block positionと浮動小数positionでは同じtokenでもparserが異なります。

### 相対座標

```mcfunction
particle minecraft:flame ~ ~1 ~
```

`~`は現在の実行位置を基準にします。`~1`は現在値へ1を加えます。command block、function、entity、server consoleで基準位置が異なるため、entry pointでcontextを定義します。

### Local座標

```mcfunction
particle minecraft:end_rod ^ ^1 ^2
```

`^left ^up ^forward`で実行rotationを基準にします。同じ3次元座標内で`^`と絶対／`~`を混在させません。`anchored eyes`は位置のanchorを変えますが、entityの向きやexecutorそのものを自動変更しません。

### Contextを変える`execute`

| subcommand | 主に変えるもの |
|---|---|
| `as` | executor |
| `at` | position、rotation、dimension |
| `positioned` | position |
| `rotated` | rotation |
| `facing` | rotation |
| `anchored` | feet／eyes anchor |
| `in` | dimensionと座標scale |
| `on` | owner、attacker、passenger等のrelationからexecutor |

`execute as @e run ...`だけでは各entity位置へ移動しません。entity自身の位置で実行するなら通常`as @e at @s`を使います。

## Rotationと角度

rotationはyaw／pitchの2値です。方向vectorやEuler rotation、display entityのquaternionとは別型です。角度のwrap境界に依存するselectorや`facing`処理は、-180／180付近と真上／真下をtestします。

## Range

```text
5
..5
5..
5..10
```

| 表現 | 意味 |
|---|---|
| `5` | ちょうど5 |
| `..5` | 5以下 |
| `5..` | 5以上 |
| `5..10` | 5以上10以下 |

integer rangeとfloat rangeは別parserです。minがmaxより大きいrangeや非有限値を生成しません。

## Target selector

| selector | 基本集合 |
|---|---|
| `@s` | 現在のexecutor。entityでなければ空 |
| `@a` | 全player |
| `@e` | 全entity |
| `@p` | 最寄りplayer |
| `@r` | random player |
| `@n` | 最寄りentity。1.21以降 |

literal player名、UUID、selectorはscore holderやentity argumentで受理範囲が異なります。

### よく使うfilter

```mcfunction
@e[type=minecraft:zombie,tag=example.active,distance=..16,sort=nearest,limit=1]
@a[scores={example.cooldown=1..},gamemode=!spectator]
@e[predicate=example:is_target,nbt={Silent:1b}]
```

| filter | 注意 |
|---|---|
| `type` | entity type ID／許可されたtag。否定と複数指定の規則を確認 |
| `tag` | entityのstring tag。未指定と空tag条件を区別 |
| `distance` | selector originからのEuclidean distance |
| `dx`,`dy`,`dz` | box範囲。distance sphereとは別 |
| `scores` | scoreが未設定のholderはrangeに一致しない |
| `predicate` | 呼出側selector contextで独立predicateを評価 |
| `nbt` | 保存NBTの部分match。頻繁な広域scanは高コスト |
| `sort` | `nearest`、`furthest`、`random`、`arbitrary`等 |
| `limit` | 結果上限。parserの単一対象制約を変更しない |
| `name`,`team`,`gamemode` | player／entity種別と未設定状態を考慮 |
| `advancements` | player advancement状態。player以外には使わない |

`limit=1`を付けても、複数entity selectorが単一entity parserで常に受理されるとは限りません。`commands.json`の`amount`／`type` propertyを確認します。

### 順序と対象0件

- `sort=nearest`の基準は現在のexecute position
- `@p`はplayerだけ、`@n`はentity全般
- `arbitrary`やfilterなしのentity順序を永続ID順として使わない
- selector結果0件では後続commandが実行されず、branch全体のsuccess／resultへ影響する
- 複数executorでは後続commandが対象数だけ分岐し、副作用も複数回起きる

## Resource locationとtag

```text
example:combat/on_hit
#example:entity/hostile
```

- 自作IDはnamespaceを省略しない
- `#`はtagを受けるparserだけで使う
- element IDとtag IDの両方を受けるparserか、単一element限定かをcommand reportで区別する
- 1.21のfolder単数形変更はresource location文字列そのものを通常変更しない

## Block state

```mcfunction
setblock ~ ~-1 ~ minecraft:oak_log[axis=y]
execute if block ~ ~-1 ~ minecraft:oak_log[axis=y] run function example:match
```

propertiesは対象blockが持つ値だけを指定します。predicate的に一部propertyを照合する場所と、完全stateを生成する場所を区別します。block entity NBTを併記できるbranchでも、block stateとblock entity typeを一致させます。

## Item stackとitem predicate

```mcfunction
# 1.20.4以前
give @s minecraft:diamond_sword{Damage:1}

# 1.20.5以降
give @s minecraft:diamond_sword[minecraft:damage=1]
```

item stackは1.20.5で旧NBTからcomponent patchへ破壊的に移行しました。`clear`や`execute if items`等のitem predicateはstack生成構文と別codecです。

## Time、color、UUID等

同じprimitiveに見えても専用parserです。

- timeはtick／second／day suffixと許容範囲を持つ
- colorはnamed color、RGB integer、text color等で形式が異なる
- UUIDはUUID string、int array NBT、entity selectorで用途が異なる
- objective、team、entity tagはresource locationとは限らず、それぞれ文字数と文字種制約を持つ

## Macro引数

1.20.2以降のfunction macroはSNBT値をcommand textへ展開します。型付き関数引数ではありません。

```mcfunction
$teleport @s $(x) $(y) $(z)
```

selector、resource ID、command断片、NBT pathへ外部文字列を挿入すると構文や対象範囲を変えられます。数値範囲、ID allowlist、固定branchで検証してからstorageへ書きます。

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.13 | Brigadier、local座標、range、`nbt=` selector |
| 1.14 | NBT path拡張、selector／function tag順序の修正 |
| 1.15 | selector `predicate=`、storage target |
| 1.20.2 | function macro、`/random`、overlay |
| 1.20.5 | item component patch、`execute if items` |
| 1.21 | `@n`、folder単数形 |
| 1.21.5 | text／SNBT parser大変更 |
| 1.21.11 | inline slot source |
| 26.3-snapshot-1 | command slot引数をslot source化 |

## 検証

`reference/command-tree.md`の手順で対象versionのcommand graphを確認し、単一／複数target、0件、dimension違い、console／function／entity executor、座標境界をtestします。syntax parse成功と、意図した対象へ一度だけ作用したことを分けて記録します。

## 出典

- 対象server JARの`reports/commands.json`
- 各 [`../versions/<version>.md`](../versions/README.md) のcommand差分
