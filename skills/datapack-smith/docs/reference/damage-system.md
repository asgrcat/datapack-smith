# Damage system

この文書はJava Edition 1.19.4以降のdamage type registry、damage type tag、`/damage`、damage source predicate、item／enchantmentとの接続を扱います。damage量、damage分類、攻撃者、death messageは別の要素です。

## Damageの構成

```text
damage event
├── amount
├── damage type
│   ├── JSON metadata
│   └── damage type tags
├── direct entity
├── causing entity
└── position
```

- damage type JSONはmessage、difficulty scaling、exhaustion等を定義する
- armor bypass、fire、projectile、fall等の性質は主にdamage type tagで分類する
- direct entityとcausing entityは矢と射手のように異なり得る
- amountを指定してもarmor、effect、enchantment、difficulty等で最終health減少が変わり得る

## Damage type resource

1.21以降の配置:

```text
data/<namespace>/damage_type/<path>.json
```

1.20.6以前は対象profileの複数形／単数形規則を確認します。

```json
{
  "message_id": "example.arcane",
  "scaling": "never",
  "exhaustion": 0.1,
  "effects": "hurt"
}
```

| field | 必須性 | 意味 |
|---|---|---|
| `message_id` | 必須 | death message translation keyのsuffix |
| `scaling` | 必須 | difficultyによるdamage scaling |
| `exhaustion` | 必須 | playerへ加えるfood exhaustion |
| `effects` | 任意 | hurt sound／visual分類 |
| `death_message_type` | 任意 | death messageの組み立て方 |

`scaling`の有効enumは対象JARのvanilla damage typeを確認します。新しい値を推測しません。

## Death message

`message_id: "example.arcane"`はresource pack language keyと接続します。代表的にはdamage sourceだけのmessage、attackerを含むmessage、itemを含むmessage等があります。

- data packだけで翻訳文を追加したことにはならない
- missing translation key時のclient表示を確認する
- attackerやitemが存在しないsourceでもmessageが組み立てられるようにする
- `death_message_type`を選ぶだけでcausing entityが自動設定されるとは仮定しない

## Damage type tag

```text
data/<namespace>/tags/damage_type/<path>.json
```

例としてcustom damageをarmor bypass集合へ追加するtag override:

```json
{
  "replace": false,
  "values": [
    "example:arcane"
  ]
}
```

実際のtag IDは対象JARの`data/minecraft/tags/damage_type/`を正本にします。代表的な分類にはarmor、shield、invulnerability、fire、projectile、fall、explosion、magic、cooldown、wolf retaliation等があります。

tagをoverrideするとき`replace: true`でvanilla entryを消さないようにします。custom typeを複数tagへ入れた結果、armor、enchantment、AI、advancement、death messageへ同時に影響することをtestします。

## `/damage`

基本形:

```mcfunction
damage @s 4 example:arcane
damage @s 4 minecraft:arrow by @e[type=minecraft:arrow,limit=1] from @p
```

利用可能なbranchは対象`commands.json`で確認します。

| 要素 | 意味 |
|---|---|
| target | damageを受けるentity |
| amount | 基本damage量 |
| damage type | source分類 |
| `at` | source位置 |
| `by` | direct entity |
| `from` | causing entity |

direct／causing entityを逆にすると、predicate、advancement、death message、AI retaliationの意味が変わります。対象0件や無敵状態でcommandがparse成功しても、healthが減るとは限りません。

## Damage source predicate

1.19.4で旧boolean群を廃止し、damage type tagの期待値を使う形へ移行しました。

```json
{
  "type": {
    "tags": [
      {
        "id": "minecraft:is_projectile",
        "expected": true
      }
    ]
  }
}
```

外側predicate fieldの形は対象バージョンに合わせます。type tag判定に加え、direct entity、source entity、位置等を絞れる場所があります。damage event外のloot contextではdamage source parameter自体がありません。

## Itemとの接続

### `minecraft:damage_resistant`

1.21.2で旧`minecraft:fire_resistant`を`minecraft:damage_resistant`へ置換しました。damage type集合を指定し、ground item entityの耐性や装備品のdamage挙動へ影響します。

- player本体の全damageを無効にするcomponentではない
- tooltipだけの表示componentではない
- tag集合の変更が既存item挙動へ波及する

### Weapon／projectile

item component、attribute、enchantment、projectile entityのdamage値とdamage typeは別です。攻撃速度、base attack damage、projectile powerを変更してもcustom damage typeへ自動変更されません。

## Enchantmentとの接続

data-driven enchantmentではdamage protection、post attack effect、damage entity effect等がdamage typeやtagを参照します。

- protection対象tagと実際のsource typeを一致させる
- effect内で追加damageを発生させる場合、再帰発火や多重適用をtestする
- direct attacker／attacking entity等のloot context parameterを確認する
- item durability damageとentity health damageを混同しない

## Armor、shield、effect

最終damageはdamage type tagだけでなく、armor、toughness、resistance effect、enchantment、shield、invulnerability time、difficulty等の影響を受けます。「amount 10が常にheart 5個」とは限りません。

テストでは次を分けます。

- command success／result
- health差分
- absorption差分
- armor／item durability差分
- knockback、sound、hurt animation
- retaliation、advancement、death message

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.19.4 | `damage_type` registry、`/damage`、tag中心のdamage source predicate |
| 1.20.5 | item data component化がdamage／attribute item表現へ波及 |
| 1.21 | enchantmentをデータ駆動化 |
| 1.21.2 | `fire_resistant`を`damage_resistant`へ置換 |
| 1.21.5 | entity／equipment NBT再編 |
| 1.21.11 | spear damage type等を追加 |
| 26.3-snapshot-9 | `#minecraft:bypasses_cooldown`等のtag追加 |

## 生成規則

- damage type JSONとdamage type tagを一緒に設計する
- direct entity、causing entity、source positionを明示する
- translation keyが必要ならresource pack側の責務を記載する
- tag overrideは原則`replace: false`でvanilla entryを保持する
- amountと最終health差分を同値と仮定しない
- damage event外のpredicate contextへdamage source条件を持ち込まない
- item、enchantment、AI、advancementへの波及を機能testする

## 検証

survival／creative、armor有無、shield、effect、projectile／melee、direct／indirect、player／mob、致死／非致死を分けてtestします。公式JARのdamage type registryとvanilla damage type tagを対象バージョンごとに取得します。

## 出典

- [Java Edition 1.19.4 profile](../versions/1.19.4.md)
- 対象server JARのdamage type registry、vanilla `tags/damage_type/`
