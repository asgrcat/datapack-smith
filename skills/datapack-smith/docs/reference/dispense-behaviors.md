---
type: "Reference"
title: "Dispenserのデータ駆動behavior"
description: "26.4 Snapshot 9のdispense_behavior registry、item component、動作順序とtype別field。"
tags: ["minecraft-java", "dispense-behavior", "item-components", "26.4-snapshot-9"]
sources: [{"id": "snapshot-9", "resource": "/snapshots/26.4-snapshot-9.md", "title": "Java Edition 26.4 Snapshot 9"}]
---

# Dispenserのデータ駆動behavior

対象は`26.4-snapshot-9`（format 128.0）です。Dispenserがitemを出すときの処理をregistry resourceまたはitem componentのinline listで選びます。Snapshot 8以前へこの書式を流用しません。[^snapshot-9]

## 配置とitemからの参照

配置は`data/<namespace>/dispense_behavior/<path>.json`、rootはbehavior objectの**list**です。各entryの`type`は`minecraft:dispense_behavior_type`のIDです。registryは`elements: true`／`stable: false`／`tags: true`ですが、componentの値にtag参照が使えるという意味ではありません。

item component `minecraft:dispense_behavior`は、registry entryのnamespaced IDまたはinline listを受け付けます。次は`data/example/dispense_behavior/place_or_drop.json`の全体です。

```json
[
  {"type": "minecraft:place_block"},
  {"type": "minecraft:drop_item"}
]
```

```mcfunction
give @s minecraft:white_wool[minecraft:dispense_behavior="example:place_or_drop"]
```

itemはWoolのままで、Dispenserで使うbehaviorを差し替えます。任意のitemをblock itemやprojectile itemへ変えるcomponentではありません。inline指定は次の形です。

```mcfunction
give @s minecraft:white_wool[minecraft:dispense_behavior=[{type:"minecraft:place_block"},{type:"minecraft:drop_item"}]]
```

## 順序と停止

entryは順番に試し、成功すると停止します。ただし停止する失敗もあり、満充電のRespawn Anchorに対する`charge_respawn_anchor`は後続へ進みません。全失敗時にitemを落としたい場合は、最後に`drop_item`を明示します。

vanilla `minecraft:default`は`equip_sulfur_cube` → `drop_item`、`minecraft:dropper`は`insert_into_container` → `drop_item`です。Dropperは専用のbehaviorを使い、Dispenser用componentの設定がそのままDropperに適用されるとは考えません。

vanilla itemのdefault componentは通常の処理を参照します。JAR実装ではcomponentを取り除くと空listとなり、itemを保持して失敗演出を行います。空listはcodecで許容されますが、`minecraft:default`を参照した状態とは異なります。これらのゲーム内動作は未検証です。

## typeと追加field

以下の24 typeを生成reportで確認しています。`shoot_projectile`と`transform_block`以外に追加fieldはありません。

| type（すべて`minecraft:`） | 処理・前提 |
|---|---|
| `brush_armadillo` | 前方のArmadilloをbrushする |
| `charge_respawn_anchor` | 前方のRespawn Anchorを充電。満充電時も後続へ進まない |
| `convert_to_mud` | Water potionを含むitemで`#minecraft:convertible_to_mud`のblockをMudへ |
| `drop_item` | item entityとして落とす |
| `empty_bucket` | bucketの内容を空ける。bucket以外は失敗 |
| `equip` | 前方のliving entityへ装備。itemが対象slotへ装備可能であること |
| `equip_chest` | chestを運べる飼い慣らされたmobへ装備 |
| `equip_sulfur_cube` | `#minecraft:sulfur_cube_swallowable`のitemを前方のcubeへ渡す |
| `fill_bottle` | 前方のblockからbottleを満たす |
| `fill_bucket` | 前方のfluidをbucketへ回収 |
| `grow_plant` | 前方の植物を成長 |
| `ignite` | 前方のblockへ着火 |
| `insert_into_container` | 前方のcontainerへitemを挿入 |
| `place_armor_stand` | 前方へArmor Standを配置 |
| `place_block` | block itemをblockとして配置。それ以外のitemは失敗 |
| `place_boat` | `entity_data`で指定したBoat／Chest Boat／Raft／Chest Raftを水上へ。他のentity typeは失敗 |
| `place_minecart` | `entity_data`で指定したMinecartをrailへ。他のentity typeは失敗 |
| `shear` | mobの剪毛またはbeehiveの収穫 |
| `shoot_projectile` | projectile itemを射出。追加fieldは後述 |
| `spawn_golem_from_carved_pumpkin` | 前方のGolem構造を完成 |
| `spawn_mob` | `minecraft:entity_data`のentityを前方へ生成 |
| `spawn_tnt` | Primed TNTを生成 |
| `transform_block` | 必須`transformer`で指定したblock transformerを前方へ適用 |
| `spawn_wither_from_wither_skeleton_skull` | 前方のWither構造を完成 |

## shoot_projectile

| field | 型・必須性 | 意味 |
|---|---|---|
| `offset` | 必須、double 3個のvector | Dispenser中心からの射出原点offset |
| `scale` | 必須、double | offset位置からDispenserの向きへさらにずらす距離 |
| `uncertainty` | 必須、0以上のfloat | 射出の不正確さ |
| `power` | 必須、0以上のfloat | 射出速度 |
| `sound` | 任意、object | 省略時は`minecraft:block.dispenser.launch`、volume 1.0、pitch 1.2 |
| `sound.sound` | sound objectを置く場合は必須、sound event | 射出音 |
| `sound.volume`／`sound.pitch` | sound objectを置く場合は両方必須、float provider | 音量とpitch |

音のproviderは`FloatProviders.CODEC`で、context依存の`context_float_provider`とは別codecです。vanilla Fire Chargeのpitchは`minecraft:trapezoid`を使用します。音object内のfieldまで省略できるとは判断しません。

`minecraft:default_projectile`の定義は次の形です。

```json
[
  {
    "type": "minecraft:shoot_projectile",
    "offset": [0.0, 0.1, 0.0],
    "scale": 0.699999988079071,
    "uncertainty": 6.0,
    "power": 1.1
  }
]
```

## entity_dataとvanilla entry

Boat／Minecart itemは`minecraft:entity_data`をdefault componentとして持ちます。たとえばOak Boatは`{"id":"minecraft:oak_boat"}`です。通常使用時とDispenser使用時の両方にentity typeの制約があり、異なる種類のentityへ無条件に置換できるとは考えません。

生成dataには次の27 entryがあります。これらはbehavior type IDとは別の、**list resourceのID**です。

`armor_stand`、`boat`、`bone_meal`、`brush`、`carved_pumpkin`、`chest`、`default`、`default_projectile`、`dropper`、`empty_bucket`、`equipment`、`filled_bucket`、`fire_charge`、`firework_rocket`、`flint_and_steel`、`glass_bottle`、`glowstone`、`honeycomb`、`minecart`、`potion`、`shears`、`shulker_box`、`spawn_egg`、`thrown_potion`、`tnt`、`wind_charge`、`wither_skeleton_skull`。

各entryの正確な動作順とfieldは対象JARの`data/minecraft/dispense_behavior/`を正本として確認します。

## 検証範囲

registry・vanilla JSON・default component、順序と停止の処理、projectileの必須fieldと音のcodecを対象JARで照合しました。list codecの実行で配置→drop例とprojectile例、空listの受理、projectileの必須field不足の拒否も確認しました。ここにあるpack／command例のserver reloadと機能検証は未実施です。

[^snapshot-9]: [Java Edition 26.4 Snapshot 9の公式資料・JAR照合](../snapshots/26.4-snapshot-9.md)
