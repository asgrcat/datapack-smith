# Block transformerとblock state provider

この文書はJava Edition 26.3の`minecraft:block_transformer` item component／registryと、変換後のblock stateを決める`minecraft:worldgen/block_state_provider`を扱います。開発中の仕様なので、対象launcher IDを固定して使います。

## バージョン境界

| バージョン | 境界 |
|---|---|
| 26.3-snapshot-2 | `minecraft:block_transformer` item componentをinline objectとして追加 |
| 26.3-snapshot-3 | ruleへ`update_from_neighbors`を追加 |
| 26.3-snapshot-10 | 内容を独立`minecraft:block_transformer` registryへ移し、componentはID参照専用化 |
| 26.3-pre-1 | block state providerを独立registry化し、type名を短縮、inline block state省略形を追加 |

Snapshot 2〜9のinline componentと、Snapshot 10以降のregistry ID componentを混在させません。

## Resourceの関係

```text
item stack
└── minecraft:block_transformer component
    └── block_transformer ID
        └── 順序付きrule list
            ├── block_state_provider
            │   ├── inline provider
            │   └── worldgen/block_state_provider ID
            ├── loot table
            ├── sound／particle
            └── drop、更新、消費設定
```

Pre-Release 1の配置:

```text
data/<namespace>/block_transformer/<path>.json
data/<namespace>/worldgen/block_state_provider/<path>.json
```

`reports/datapack.json`では両registryともelementとtagに対応します。

## Block transformer rule

transformer resourceのrootはrule objectのlistです。上から評価し、最初に変換結果を返したruleを使います。

| field | 必須性 | 型 | 既定値／意味 |
|---|---|---|---|
| `block_state_provider` | 必須 | block state provider | 変換後state。結果なしなら次ruleへ |
| `sound` | 任意 | sound event | 無音 |
| `particle` | 任意 | enum | `none` |
| `disallowed_faces` | 任意 | direction list | 空list |
| `loot` | 任意 | loot table ID | dropなし |
| `drop_strategy` | 任意 | `from_middle`／`clicked_face` | `from_middle` |
| `update_from_neighbors` | 任意 | boolean | `true` |
| `transform_type` | 任意 | `single_block`／`copper_chest` | `single_block` |
| `consume_on_use` | 任意 | boolean | `true` |
| `item_damage_per_use` | 任意 | 非負integer | `0` |

`particle`は`none`、`scrape`、`wax_on`、`wax_off`です。`disallowed_faces`にclicked faceが含まれる場合、そのruleを失敗として次ruleを試します。

### 最小例

`data/example/block_transformer/path_maker.json`:

```json
[
  {
    "block_state_provider": {
      "type": "minecraft:rule_based",
      "rules": [
        {
          "if_true": {
            "type": "minecraft:matching_block_tag",
            "tag": "minecraft:turns_into_dirt_path"
          },
          "then": "minecraft:dirt_path"
        }
      ]
    },
    "disallowed_faces": [
      "down"
    ],
    "item_damage_per_use": 1,
    "sound": "minecraft:item.shovel.flatten"
  }
]
```

item stack側ではcomponent値をIDにします。

```mcfunction
give @s minecraft:stick[minecraft:block_transformer="example:path_maker"]
```

独立resourceをinlineでcomponentへ埋め戻しません。

## Ruleの評価と副作用

1. clicked faceが`disallowed_faces`なら次ruleへ進む
2. `block_state_provider`を現在位置と現在stateに対して評価する
3. providerが結果なしなら次ruleへ進む
4. stateを`transform_type`に従って適用する
5. neighbor update、loot、sound、particle、item消費／damageを処理する

providerのpredicate、loot table、block entity、neighbor updateが失敗した場合の部分適用へ依存しません。block変更とitem消費をtransactionとして扱わず、失敗ケースを対象serverで確認します。

## Block stateの省略形

Pre-Release 1ではinline block state objectが`minecraft:simple` providerの省略形です。

```json
{
  "id": "minecraft:oak_log",
  "properties": {
    "axis": "y"
  }
}
```

block ID文字列だけのroot省略形は認められません。propertiesなしでもobjectにします。

```json
{
  "id": "minecraft:stone"
}
```

ただしprovider内部の`then`等ではblock ID文字列が観測される場所があります。外側codecのblock stateと、provider type全体の省略形を混同せず、同じfieldのvanilla例を基準にします。

## Pre-Release 1のprovider type

公式JARの`minecraft:worldgen/block_state_provider_type`には10 typeがあります。

| type | 主なfield | 役割 |
|---|---|---|
| `minecraft:simple` | `state`またはinline block state | 固定state |
| `minecraft:weighted` | `entries[].data`, `weight` | 重み付きstate選択 |
| `minecraft:randomized_int` | `source`, `property`, `values` | 元stateのinteger propertyを乱数化 |
| `minecraft:noise` | `seed`, `noise`, `scale`, `states` | noise値でstateを選ぶ |
| `minecraft:dual_noise` | 通常noise、slow noise、`variety` | 2段階noiseで候補集合とstateを選ぶ |
| `minecraft:noise_threshold` | noise、`threshold`、low／high state | thresholdの上下で候補を分ける |
| `minecraft:rule_based` | `rules[].if_true`, `then` | block predicateを順番に評価 |
| `minecraft:copy_properties` | `source` | 現在stateと同名のpropertyを変換先へcopy |
| `minecraft:rotated` | type固有field | 対応blockの向きをrandom化 |
| `minecraft:random_block` | type固有field | block候補をrandom選択 |

Pre-Release 1では旧type名のsuffixを削除します。

| 118.0まで | 119.0 |
|---|---|
| `dual_noise_provider` | `dual_noise` |
| `noise_provider` | `noise` |
| `noise_threshold_provider` | `noise_threshold` |
| `randomized_int_state_provider` | `randomized_int` |
| `rule_based_state_provider` | `rule_based` |
| `simple_state_provider` | `simple` |
| `weighted_state_provider` | `weighted` |
| `random_block_provider` | `random_block` |
| `rotated_block_provider` | `rotated` |

### weighted

```json
{
  "type": "minecraft:weighted",
  "entries": [
    {
      "data": "minecraft:stone",
      "weight": 3
    },
    {
      "data": "minecraft:andesite",
      "weight": 1
    }
  ]
}
```

`weight`は正integerを使います。乱数のsample回数や別ruleとの乱数共有へ依存しません。

### randomized_int

```json
{
  "type": "minecraft:randomized_int",
  "property": "age",
  "source": {
    "id": "minecraft:cave_vines",
    "properties": {
      "age": "0"
    }
  },
  "values": {
    "type": "minecraft:uniform",
    "min_inclusive": 0,
    "max_inclusive": 25
  }
}
```

`property`がsource blockに存在し、provider値がそのpropertyの許容範囲へ収まることを確認します。

### rule_based

```json
{
  "type": "minecraft:rule_based",
  "rules": [
    {
      "if_true": {
        "type": "minecraft:matching_blocks",
        "blocks": "minecraft:coarse_dirt"
      },
      "then": "minecraft:dirt"
    }
  ]
}
```

Pre-Release 1ではruleが結果を返さない場合に後続ruleを評価します。全ruleとfallbackが結果を返さなければprovider全体も結果なしとなり、block transformerでは次のtransformer ruleを試せます。

### copy_properties

```json
{
  "type": "minecraft:copy_properties",
  "source": {
    "id": "minecraft:stripped_oak_log",
    "properties": {
      "axis": "y"
    }
  }
}
```

現在stateと変換先stateの両方に存在する同名propertyをcopyします。存在しないpropertyの新規作成や、別名propertyの変換は行いません。door、chest、stairs等では`transform_type`とneighbor updateも合わせて検証します。

## Lootとdrop位置

`loot`を設定したruleでは、変換時に指定loot tableを評価します。`drop_strategy`はdrop位置をblock中央またはclicked face側から選びます。

- loot table IDをblock loot pathへ固定とは仮定しない
- loot contextが提供するblock state／block entity／tool等を対象JARで確認する
- dropを出すことと、元blockの通常dropを自動実行することを同一視しない
- containerやcopper chestの内容保持／dropは`transform_type`ごとにtestする

## 生成規則

- launcher IDとdata pack formatを完全一致させる
- Snapshot 10以降はcomponentへtransformer IDだけを設定する
- Pre-Release 1では旧`*_provider` type名を出力しない
- block ID文字列だけをroot providerの省略形として出力しない
- ruleの順序、結果なし、disallowed faceを設計する
- property copy後のblock stateが有効か検証する
- door／chest等は単一block変換として扱わず、`transform_type`とneighbor updateを確認する
- itemのconsumeとdamage、loot、sound、particleを独立してtestする

## 検証

Pre-Release 1の公式JARでは、transformer resource `axe`、`hoe`、`shovel`と、block state provider resource 8件が生成されます。これらを同じtypeの最小例として使い、公式registryの10 provider typeと照合します。隔離した実験worldで、各clicked face、両手、creative／survival、耐久0直前、block entity、neighbor updateを確認してください。

## 出典

- [Mojang: Minecraft 26.3 Snapshot 2](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-2)
- [Mojang: Minecraft 26.3 Snapshot 10](https://feedback.minecraft.net/hc/en-us/articles/48394701938573-Minecraft-Java-Edition-26-3-Snapshot-10)
- [Mojang: Minecraft 26.3 Pre-Release 1](https://www.minecraft.net/en-us/article/minecraft-26-3-pre-release-1)
