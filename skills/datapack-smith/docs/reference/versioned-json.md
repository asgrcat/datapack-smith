# 対象バージョンからJSONキーを選ぶ

このページは、生成時に混ざりやすい**同じ用途の異なる表現**を並べます。完全なcodec schemaではありません。対象のexact profileとfamily履歴を先に解決し、ここで外形を選び、family文書で内側の値型・必須性・既定値・contextを確認します。正式リリースの範囲をsnapshotへそのまま適用しません。

## 決定手順

1. `resolve <exact-version>`でprofileと`json_parameter_history`を取得する。実行pathは[ハーネス](../harness.md)を参照。
2. 作るものをresource種別とconsumerまで特定する。例: `recipe / minecraft:smelting / $.result`。単なる「itemのJSON」では足りない。
3. 対象までのそのfamilyの追加・削除・renameを適用する。profileの「継承」は内側のschemaが全期間不変という保証ではない。
4. JSON pathごとに名前・値型・必須条件を選ぶ。旧新keyの併記、未知fieldの無視、format番号による自動変換を前提にしない。
5. IDの存在は対象report、fieldの意味は対象リリースノート、同型の例は対象vanilla dataで確認する。独自resourceのIDは自pack/依存packへ解決する。
6. `validate-project`の既知境界検査を実行する。検査外のcodec・値域・loot contextは必要な検証levelに応じて対象serverで確認する。読込成功でも無視された旧keyは発見できない場合があり、実際の結果も比較する。

各表のJSONは、特記した**fieldの値・断片**です。単独のresourceとして保存しません。全fileが揃ったpack例は[worked-example](../worked-example.md)です。

## 1. 配置・metadata

| 正式リリース | function / recipe / predicate | `pack`のformat field |
|---|---|---|
| 1.13〜1.14.4 | `functions` / `recipes` / 独立predicate未対応 | `pack_format`整数 |
| 1.15〜1.20.1 | `functions` / `recipes` / `predicates` | `pack_format`整数 |
| 1.20.2〜1.20.6 | 同上 | `pack_format`必須、範囲は任意`supported_formats` |
| 1.21〜1.21.8 | `function` / `recipe` / `predicate` | 同上 |
| 1.21.9〜26.3 | 単数形 | `min_format` / `max_format`。旧reader併用時は[metadata規則](../compatibility.md)も適用 |

`item_modifier`は1.17導入、1.20.6以前は`item_modifiers`です。function tagも1.21で`tags/functions`→`tags/function`となります。formatの数値は必ず対象profileから取得します。

## 2. Recipeのingredientとresult

### Ingredient: shapedの`key.S`、shapelessの`ingredients[]`、cookingの`ingredient`

| 正式リリース | 1 item | 1 tag | listの注意 |
|---|---|---|---|
| 1.13〜1.21.1 | `{"item":"minecraft:stone"}` | `{"tag":"minecraft:planks"}` | objectの配列。対象serializerの制約を確認 |
| 1.21.2〜26.3 | `"minecraft:stone"` | `"#minecraft:planks"` | item IDの配列。tagをlist内へ混ぜない |

`ingredient`はitem predicateでもitem stackでもありません。`count`や`components`を足してcomponent付きitemだけを材料にできるとは扱いません。smithingの空ingredient/省略規則やtransmuteは[recipe詳細](../json-parameters/loot-recipes.md)で確認します。

### Result: consumerを分ける

| 正式リリース | shaped / shapelessの`result` | smelting等の`result` | stonecuttingの`result` |
|---|---|---|---|
| 1.13〜1.20.4 | `{"item":"minecraft:stone","count":1}` | `"minecraft:stone"` | 1.14導入。`"minecraft:stone"`、個数はrecipe rootの`count` |
| 1.20.5〜1.21.11 | `{"id":"minecraft:stone","count":1}` | `{"id":"minecraft:stone"}`。個数指定不可 | `{"id":"minecraft:stone","count":1}` |
| 26.1〜26.3 | 共通item stack。`"minecraft:stone"`または`{"id":"minecraft:stone","count":1}` | 同左、countも利用可能 | 同左 |

component対応後は対応するresultに`components`を設定できます。1.20.5〜1.21.11でも、craftingの例から`count`をcookingへコピーしません。1.21.11と26.1は外見が似たJSONでも受理する型が異なります。

26.3ではcookingの`cookingtime`が必須です。26.2以前に省略していた場合は200、smoking/blastingで以前明示していた値は2倍にし、燃料の速度倍率と組み合わせます。`cookingtime`とworldgenの時間providerを同じcodecとして扱いません。

根拠: [1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)、[1.21.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2)、[26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)、[26.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3)のrecipe変更。serializer固有の追加条件は[loot/recipe](../json-parameters/loot-recipes.md)へ。

## 3. Item stack、component、text

| 場所 | 旧形式 | 新形式と境界 |
|---|---|---|
| 保存NBT item stack | `id`、byteの`Count`、`tag` | 1.20.5から`id`、integerの`count`、`components` |
| commandの任意item data | `minecraft:stick{demo:1b}` | 1.20.5から`minecraft:stick[minecraft:custom_data={demo:1b}]` |
| advancement `display.icon` | `{"item":"minecraft:stone"}`、任意`nbt` | 1.20.5からitem stackの`{"id":"minecraft:stone"}`、任意`components` |
| enchantments component | 1.20.5〜1.21.4は`levels` wrapper、`show_in_tooltip` | 1.21.5からID→level map直書き。tooltipは`tooltip_display` |
| attribute_modifiers component | 1.20.5〜1.21.4は`modifiers` wrapper | 1.21.5からlist直書き |
| dyed_color component | 1.20.5〜1.21.4は`rgb` wrapperを使用可能 | 1.21.5から色値直書き |
| custom_name command値 | 1.20.5〜1.21.4はJSON textをSNBT stringへ入れる | 1.21.5からSNBT text componentを直接渡す |
| text event | 1.21.4まで`clickEvent` / `hoverEvent` | 1.21.5から`click_event` / `hover_event`。内側のaction別fieldも変更 |

名前付きitemのcommand例:

```mcfunction
# 1.13〜1.20.4
give @s minecraft:stick{display:{Name:'{"text":"Token"}'}}
# 1.20.5〜1.21.4
give @s minecraft:stick[minecraft:custom_name='{"text":"Token"}']
# 1.21.5〜26.3
give @s minecraft:stick[minecraft:custom_name={text:"Token"}]
```

`tellraw`の1.21.4以前の引数はJSONを直接書きます。item NBT内のJSON文字列wrapperを`/tellraw`にも付けるわけではありません。JSON resource内では新しいtextでも厳密なJSONを使います。[items](../json-parameters/items.md)と[text](text-components.md)でcommand・保存NBT・JSONを分離します。

## 4. Predicate: resource rootと入れ子を分ける

player判定の独立predicateを同じ用途で比較します。

**1.15〜26.1.2**（1.20.6以前は`predicates/`、1.21以降は`predicate/`）:

```json
{"condition":"minecraft:entity_properties","entity":"this","predicate":{"type":"minecraft:player"}}
```

**26.2**:

```json
{"condition":"minecraft:entity_properties","entity":"this","predicate":{"minecraft:entity_type":"minecraft:player"}}
```

**26.3**:

```json
{"type":"minecraft:entity_properties","entity":"this","predicate":{"minecraft:entity_type":"minecraft:player"}}
```

外側のloot conditionと内側のentity predicateは、変更したリリースが違います。`type`を全文検索で一括置換すると壊れます。26.2のsub-predicate IDでは既定namespaceを省略できる場合もありますが、生成物ではnamespaced IDを明示します。旧`type`や`type_specific` wrapperは残しません。

| consumer | 境界 |
|---|---|
| item predicate | 1.17で`item`→`items`。1.20.5で旧NBT・durability等をcomponent predicateへ移動 |
| gameplay block predicate | 1.17で`block`→`blocks`。1.20.5で旧`tag`を`blocks`のID/list/tagへ統合 |
| location predicate | 1.20.5で`biome`→`biomes`、`structure`→`structures` |
| condition合成 | 1.20で`alternative`→`any_of`、`all_of`追加 |
| standalone predicate | 1.15導入。1.16からroot arrayはAND。26.3では明示的`all_of`を使う |
| predicate参照 | 26.2までは`reference` wrapper、26.3ではpredicate ID直接参照 |

rootの完全例はplayer executorから`execute if predicate <id>`で評価します。server contextでは`this`がないため、同じJSONでも期待する真偽になりません。条件の値型とcontextは[predicates](../json-parameters/predicates.md)へ。

## 5. Loot tableとitem modifier

| JSON path / consumer | 26.2まで | 26.3 |
|---|---|---|
| condition objectのdiscriminator | `condition` | `type` |
| item modifier / loot functionのdiscriminator | `function` | `type` |
| loot function / pool entryの条件 | `conditions` array | 単一`condition`（predicate / ID） |
| pool entryの加工 | `functions` | `modifier` |
| `minecraft:tag` entry | `name` | `items`（ID / list / tag） |

この表の「pool entry」を「pool」や「table root」へ拡張しません。root、pool、entry、functionは別codecです。例えば旧`set_loot_table.type`はdiscriminatorではなくtable typeだったため、新discriminatorの`type`と区別して移行します。[26.3移行表](26.3-migration.md)と対象のvanilla JSONを使います。

`set_count` item modifierの完全なroot例は、1.17〜26.2では`{"function":"minecraft:set_count","count":2}`、26.3では`{"type":"minecraft:set_count","count":2}`です。provider objectを使う場合は26.3のinteger/float分割とconsumerのcontextを[number provider](number-providers.md)で確認します。

## 6. Advancement・worldgen・その他のregistry

| family | 主な境界 | 確定する資料 |
|---|---|---|
| advancement | 1.20のtrigger内location条件、1.20.5のicon/item predicate、1.21.5の背景参照、26.3のroot背景必須・条件参照 | [advancement parameters](../json-parameters/advancements.md)、[26.3](26.3-migration.md) |
| dimension/worldgen | 1.16と1.16.2のexperimental配置、1.18/1.18.2のnoise、1.19のstructure、1.21.11の属性、26.1のclock、26.3の再編 | [dimension/worldgen](../json-parameters/dimensions-worldgen.md)、[worldgen](worldgen.md) |
| enchantment | 1.21でdefinitionをデータ駆動化。それ以前はitemの強化値と固定registryのみ | [enchantment/variant](../json-parameters/enchantments-variants.md) |
| variant | registryごとに導入時期、asset/spawn/soundの型が異なる | [enchantment/variant](../json-parameters/enchantments-variants.md)、[registry formats](registry-formats.md) |
| dialog | 1.21.6導入。command actionとdynamic actionの入力形式・権限を分離 | [dialogs](dialogs-and-actions.md) |
| damage type | 1.19.4導入。IDを定義するfileとdamage分類tagは別 | [damage](damage-system.md) |

26.3のworldgenでは`configured_feature`→`feature`、`configured_carver`→`carver`、`config`内fieldのrootへの移動があります。block stateの`Name`/`Properties`も`id`/`properties`へ変わります。単純なfolder renameだけでは完了しません。

## 開発バージョンと未確認field

26.3の開発枝では、Snapshot 1でfeature配置、Snapshot 4でcondition/参照、Pre-Release 1でinteger/float providerとcookingtimeが変わります。正式26.3の形をSnapshot 1へ使わず、完全一致profileの継承枝を使います。ハーネスの既知境界検査もこの枝で判定します。

このページにないfieldを「どのversionでも同じ」と扱いません。調査メモに`version / family / type / JSON path / 値型 / 必須性・既定 / 出典 / 実施検証`を残し、対象JARの同型vanilla例を基底にします。vanillaに例がない任意fieldは、公式field定義や対象codecで確認し、未確認のまま「対応済み」としません。未収録のゲームバージョンはこのskillの対応保証外です。
