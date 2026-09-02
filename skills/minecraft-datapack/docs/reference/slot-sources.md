# Slot source

slot sourceは、entity、block entity、item内container等から0個以上のslotを順序付きで選ぶ値です。この文書はJava Edition 1.21.11のinline slot sourceと、26.3 Snapshot 1以降の独立`minecraft:slot_source` registryを扱います。

## バージョン境界

| バージョン | 書式と利用場所 |
|---|---|
| 1.21.11 | inline slot source、loot entry `minecraft:slots`を追加。独立resource folderはない |
| 26.3-snapshot-1 | `data/<namespace>/slot_source/<path>.json`を追加。コマンドのslot引数をslot source化 |
| 26.3-snapshot-4 | `reference` typeを削除し、slot sourceを受けるfieldが直接IDを受付 |
| 26.3-snapshot-5 | element listでinline値とID参照を混在可能 |
| 26.3-snapshot-9 | inline `group`をtop-level fileに限定。top-level ID aliasの不具合を修正 |

26.3の書式を1.21.11へ先取りしません。1.21.11ではinline codecだけを使い、独立`slot_source/` resourceを生成しません。

## 結果のモデル

slot sourceの結果はitemのcopyではなくslotの位置列です。

- 0件、1件、複数件になり得る
- `group`は入力順を保って連結する
- 同じslotが複数回含まれても重複排除しない
- 複数entityを対象にしたcommandではentityごとの結果を連結する
- `filtered`や`limit_slots`は元の順序を保つ

同じslotへ複数回書く場合、command側の置換規則と評価順が結果へ影響します。

## 26.3 Pre-Release 1のtype

公式JARの`minecraft:slot_source_type` registryには6 typeがあります。

| type | field | 結果 |
|---|---|---|
| `minecraft:empty` | なし | 空のslot列 |
| `minecraft:group` | `terms` | 複数sourceの結果を順番に連結 |
| `minecraft:slot_range` | `slots`、任意`source` | loot context内のinventoryからslot rangeを選択 |
| `minecraft:contents` | `component`、`slot_source` | 選択itemのinventory component内slotを展開 |
| `minecraft:filtered` | `item_filter`、`slot_source` | item predicateに一致するslotだけ残す |
| `minecraft:limit_slots` | `limit`、`slot_source` | 先頭から最大`limit`件に制限 |

### empty

```json
{
  "type": "minecraft:empty"
}
```

条件付き構成で「対象なし」を明示するときに使います。空であることは評価失敗ではありません。

### group

```json
{
  "type": "minecraft:group",
  "terms": [
    {
      "type": "minecraft:slot_range",
      "slots": "hotbar.*"
    },
    {
      "type": "minecraft:slot_range",
      "slots": "armor.*"
    }
  ]
}
```

list自体が`group`の省略形として認められる場所があります。26.3-snapshot-9以降、inline `group`はtop-level slot source resourceで使い、nested位置では独立resourceのIDを参照します。

### slot_range

```json
{
  "type": "minecraft:slot_range",
  "source": "this",
  "slots": "container.*"
}
```

`slots`は`armor.chest`のような単一slotまたは`container.*`のようなrangeです。1.21.11の`source`候補には`block_entity`、`this`、`attacking_entity`、`last_damage_player`、`direct_attacker`、`target_entity`、`interacting_entity`があります。利用場所のloot contextが対象entityを供給しなければ使えません。

26.3-snapshot-1では`container` sourceを追加し、`source`を省略した場合もcontainerを既定にします。commandが評価する対象inventoryは`minecraft:command_slot_source` contextの`container`です。

command引数の`hotbar.4`や`container.*`は、対応する`slot_range`の省略形です。

### contents

```json
{
  "type": "minecraft:contents",
  "component": "minecraft:container",
  "slot_source": {
    "type": "minecraft:slot_range",
    "slots": "weapon.mainhand"
  }
}
```

`component`は対象バージョンで`minecraft:bundle_contents`、`minecraft:charged_projectiles`、`minecraft:container`を受けます。外側sourceが複数itemを選べば、各itemの内部slotを`group`と同じ規則で連結します。26.3-snapshot-1以降は空slotも選択対象になり得るため、非空だけが必要なら`filtered`を重ねます。

### filtered

```json
{
  "type": "minecraft:filtered",
  "item_filter": {
    "count": {
      "min": 16
    }
  },
  "slot_source": {
    "type": "minecraft:slot_range",
    "slots": "hotbar.*"
  }
}
```

`item_filter`はitem predicateです。空slotの扱い、component predicate、countの書式は対象バージョンのitem predicateに従います。

### limit_slots

```json
{
  "type": "minecraft:limit_slots",
  "limit": 3,
  "slot_source": {
    "type": "minecraft:slot_range",
    "slots": "container.*"
  }
}
```

順序を変えず先頭`limit`件を残します。ランダム選択ではありません。負数やcodec範囲外の値を生成しません。

## 独立resource

`data/example/slot_source/hotbar_and_armor.json`:

```json
{
  "type": "minecraft:group",
  "terms": [
    {
      "type": "minecraft:slot_range",
      "slots": "hotbar.*"
    },
    {
      "type": "minecraft:slot_range",
      "slots": "armor.*"
    }
  ]
}
```

Snapshot 1の一時的な`minecraft:reference`形はSnapshot 4で削除されています。Pre-Release 1では、slot sourceを受けるfieldへ`"example:hotbar_and_armor"`を直接渡します。

## Commandでの評価

26.3-snapshot-1以降、`/item`と`execute if|unless items`はslot sourceを取ります。また`execute if|unless slots`は選択されたslot数を条件にします。

```mcfunction
execute if slots entity @s example:hotbar_and_armor run function example:has_slots
execute if items entity @s example:hotbar_and_armor minecraft:diamond
item replace entity @s hotbar.* from entity @s armor.*
```

`/item`のdestination数とsource item数が異なる場合:

| subcommand | destinationが多い場合 |
|---|---|
| `replace` | 余ったdestinationを変更しない |
| `fill` | source item列を繰り返して全destinationを埋める |
| `override` | 余ったdestinationを空にする |

source itemの方が多い場合、余ったsource itemは無視します。複数entityをsourceにすると、entityごとのslot列が連結されます。

## Loot tableでの利用

1.21.11以降の`minecraft:slots` entryはslot内のitemをloot候補へ渡します。

```json
{
  "type": "minecraft:slots",
  "slot_source": {
    "type": "minecraft:slot_range",
    "source": "this",
    "slots": "armor.*"
  }
}
```

itemをcopyするのか、外側loot functionで変更するのか、実際のcontainerへ書き戻すのかを区別します。loot entryの評価だけで元slotを消費・変更するとは仮定しません。

## 生成規則

- target versionが1.21.11か26.3系かを先に固定する
- 1.21.11へ独立`slot_source/`を出力しない
- Pre-Release 1へ削除済み`minecraft:reference`を出力しない
- nested位置へinline `group`を出力しない
- sourceが必要とするloot context parameterを呼出側が供給するか確認する
- 0件、重複slot、複数entity、destination／source数の不一致をtestする
- slot列の順序へ依存する処理ではtag展開順を使わない

## 検証

Pre-Release 1では公式JARの`minecraft:slot_source_type` 6 entryと`reports/datapack.json`のelement／tag対応を正本にします。独立resourceをreloadした後、空inventory、満杯inventory、bundle／container item、同じslotの重複、複数entityを機能テストします。

## 出典

- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- [Mojang: Minecraft 26.3 Snapshot 1](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-1)
- [Mojang: Minecraft 26.3 Snapshot 4](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-4)
- [Mojang: Minecraft 26.3 Snapshot 9](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-9)
