# Context依存number provider

この文書は Java Edition `26.3-pre-1`〜`26.3-pre-3`（data pack format 119.0〜121.0）の`minecraft:context_int_provider`と`minecraft:context_float_provider`を扱います。四則演算、剰余、累乗、集約、丸め、型変換、三角関数、乱数、値の取得、条件分岐を、入力fieldと失敗条件まで含めて引くためのリファレンスです。

resource ID、tag、inline定義、listを受け付ける箇所の共通規則は [`registry-elements.md`](registry-elements.md) を参照してください。このページはnumber provider固有の型、演算、評価失敗に集中します。

これらは開発中の仕様です。26.2以前の正式リリース、26.3 Snapshot 10以前、将来の26.3正式リリースへそのまま適用せず、対象launcher IDの公式server JARで再検証してください。

## バージョン境界

| launcher ID | data pack format | このページへの適用 |
|---|---:|---|
| `26.3-pre-1` | 119.0 | integer／float registry分割と下記type／fieldを導入 |
| `26.3-pre-2` | 120.0 | 一部providerの`/compute` error、loot contextの不具合を修正 |
| `26.3-pre-3` | 121.0 | float `mod`を通常の剰余へ変更、float `pow`の`0^0`を評価中止へ変更 |

type／field一覧はPre-Release 1を基底とし、演算規則には対象バージョンの差分を適用します。

## 2種類のregistry

119.0では、Snapshot 10までの`minecraft:number_provider`と`minecraft:number_provider_type`を次へ分割します。

| 値の種類 | element registry | type registry | resource path | tag path |
|---|---|---|---|---|
| 32-bit integer | `minecraft:context_int_provider` | `minecraft:context_int_provider_type` | `data/<namespace>/context_int_provider/<path>.json` | `data/<namespace>/tags/context_int_provider/<path>.json` |
| single-precision float | `minecraft:context_float_provider` | `minecraft:context_float_provider_type` | `data/<namespace>/context_float_provider/<path>.json` | `data/<namespace>/tags/context_float_provider/<path>.json` |

名前に`context`がない`minecraft:int_provider_type`と`minecraft:float_provider_type`は、主にworldgenで使うcontext非依存providerです。119.0のcontext依存providerとregistry、resource path、受理するfieldを共有するとは限りません。

providerを評価できるparameterは利用場所のcontextで決まります。例えば`/compute default`、`/compute block`、`/compute entity`が供給するblock state、block entity、target entityは異なります。provider内のpredicateやenvironment attributeが必要とするparameterを、利用場所が供給するか確認してください。

## Snapshot 10からの移行

### registryとtype名

| 118.0まで | 119.0 | 移行先 |
|---|---|---|
| `minecraft:number_provider` | 削除 | 利用fieldに応じて`minecraft:context_int_provider`または`minecraft:context_float_provider` |
| `minecraft:number_provider_type` | 削除 | 対応するinteger／float type registry |
| `minecraft:sum` | `minecraft:add` | integer／floatの両方 |
| `minecraft:product` | `minecraft:mul` | integer／floatの両方 |
| `minecraft:minimum` | `minecraft:min` | integer／floatの両方 |
| `minecraft:maximum` | `minecraft:max` | integer／floatの両方 |
| `minecraft:average` | `minecraft:avg` | integer／floatの両方 |
| `operands` | `inputs` | `add`、`mul`、`min`、`max`、`avg` |
| `minecraft:binomial` | 同名 | integerだけ |
| `minecraft:score` | 同名 | integerだけ |
| `minecraft:enchantment_level` | 同名 | floatだけ |

`constant`、`uniform`、`storage`、`weighted_list`、`conditional`、`number_dispatcher`、`environment_attribute`は同名のinteger／float variantへ分かれます。旧registryのIDやtagを互換用に残さず、参照するconsumerとprovider resourceを一括で移行します。

### 新しく使える演算

119.0では新registryの導入に加え、次の演算が利用できます。

- integer: `abs`、`sub`、`negate`、`pow`、`div`、`floor_div`、`mod`、`floor_mod`、`from_float`
- float: `abs`、`sub`、`negate`、`pow`、`div`、`mod`、`ceil`、`floor`、`round`、`truncate`、`sin`、`cos`、`sqrt`、`length`、`from_int`

`tan`、逆三角関数、対数、指数関数、専用のclamp typeは、Pre-Release 1の公式JARが出力したtype registryにはありません。

## 共通の値表現

providerを受けるfieldには、利用場所が許す範囲で次を指定します。

- inline object: `type`とtype固有fieldを持つobject
- namespaced ID: 同じ値種類のprovider resourceへの参照
- 定数の省略形: integerは`1`、floatは`1.0`のようなplain number

例えばintegerの`1`は次のobjectの省略形です。

```json
{
  "type": "minecraft:constant",
  "value": 1
}
```

集約演算の`inputs`は、単一inline値、単一ID、inline値のlist、IDのlist、または同じprovider registryの`#`付きtag IDを受けます。1要素以上が必須です。`left`／`right`、`input`、`min`／`max`のような単一provider fieldへprovider tagを使えるとは仮定しません。

## Integer provider

integer providerは32-bit signed integer、すなわち`-2147483648`〜`2147483647`で計算します。typeごとに明記されたoverflow、0除算、不正変換は評価を中止します。仕様が未定義とする不正値へ依存せず、入力範囲をpredicateやデータ設計で制限してください。

### Integer type一覧

| type | field | 結果と制約 |
|---|---|---|
| `minecraft:constant` | `value` integer | 定数。plain integerで省略可能 |
| `minecraft:add` | `inputs` | 1個以上の入力の和。最終結果が範囲外なら中止 |
| `minecraft:sub` | `left`, `right` | `left - right`。最終結果が範囲外なら中止 |
| `minecraft:mul` | `inputs` | 1個以上の入力の積。最終結果が範囲外なら中止 |
| `minecraft:div` | `left`, `right` | 0方向へ丸める整数除算。0除算は中止 |
| `minecraft:floor_div` | `left`, `right` | 負の無限大方向へ丸める整数除算。0除算または範囲外は中止 |
| `minecraft:mod` | `left`, `right` | 0方向へ丸める除算に対応した剰余。0除算は中止 |
| `minecraft:floor_mod` | `left`, `right` | 負の無限大方向へ丸める除算に対応した剰余。0除算は中止 |
| `minecraft:pow` | `base`, `exponent` | 整数の累乗。負の指数、`0`の`0`乗、範囲外は中止 |
| `minecraft:abs` | `input` | 絶対値。結果が範囲外なら中止 |
| `minecraft:negate` | `input` | 符号反転。結果が範囲外なら中止 |
| `minecraft:min` | `inputs` | 1個以上の入力の最小値 |
| `minecraft:max` | `inputs` | 1個以上の入力の最大値 |
| `minecraft:avg` | `inputs` | 1個以上の入力の算術平均。除算は0方向へ丸める |
| `minecraft:from_float` | `input` float provider | floatを0方向へ切り捨てる。32-bit整数に収まらない値とNaNは中止 |
| `minecraft:uniform` | `min`, `max` | 両端を含む閉区間からintegerを選ぶ |
| `minecraft:binomial` | `n` integer provider, `p` float provider | 成功確率`p`で`n`回試行した成功回数。`p`は0.0〜1.0 |
| `minecraft:weighted_list` | `distribution` | `data`と正integerの`weight`を持つ候補から選ぶ |
| `minecraft:conditional` | `condition`, `on_true`, 任意`on_false` | predicateが真なら`on_true`、偽なら`on_false`。省略時は`0` |
| `minecraft:number_dispatcher` | `cases`, 任意`default` | 順番に最初の真の`condition`に対応する`value`。該当なしの既定値は`0` |
| `minecraft:score` | `score`, `target`, 任意`fallback` | score holderのscore。値がなければ`fallback`、既定は`0` |
| `minecraft:storage` | `storage`, `path`, 任意`fallback` | command storageのinteger。欠落、非数値、複数match時はfallback、既定は`0` |
| `minecraft:environment_attribute` | `attribute` | integerで表せるenvironment attribute値 |

Mojangの記事は`minecraft:conditional`のfieldを`conditions`と記載していますが、Pre-Release 1の公式JARが生成したvanilla providerは`condition`を使用しています。このリポジトリでは公式JARの`condition`を正本とします。

### 四則演算と剰余

`add`と`mul`は`inputs`を使う可変長演算、`sub`と`div`は`left`／`right`を使う二項演算です。Snapshot 9〜10の`operands`や、`sub.inputs`のようなfieldを生成しません。

integerの負数除算では`div`と`floor_div`が異なります。

| 式 | 結果 | 対応する剰余 |
|---|---:|---:|
| `-7 div 3` | -2 | `-7 mod 3` = -1 |
| `-7 floor_div 3` | -3 | `-7 floor_mod 3` = 2 |

どちらも`left = quotient * right + remainder`を満たします。負数を含む座標、周期、index計算では、欲しい剰余の符号を先に決めて`div`／`mod`または`floor_div`／`floor_mod`を組にして使います。

```json
{
  "type": "minecraft:div",
  "left": {
    "type": "minecraft:add",
    "inputs": [20, 4]
  },
  "right": {
    "type": "minecraft:sub",
    "left": 7,
    "right": 1
  }
}
```

この例は`(20 + 4) / (7 - 1)`をintegerとして評価し、`4`を返します。

### Integer固有の境界

- `abs(-2147483648)`と`negate(-2147483648)`は正の結果を32-bit integerで表せないため中止する
- `pow`は負の指数を受け付けず、`0^0`も中止する
- `from_float`は小数を0方向へ切り捨てるため、`1.9`は`1`、`-1.9`は`-1`
- `avg`も0方向へ丸めるため、負の平均で`floor`と同じ結果になるとは限らない
- provider評価の失敗は`/compute`の失敗へ伝播する

## Float provider

float providerはsingle-precision floating-pointで計算します。結果がNaNまたはInfinityになる計算の挙動は未定義です。特に0除算、負数の平方根、定義域外の累乗、極端に大きい中間値をportableな結果として扱いません。

### Float type一覧

| type | field | 結果と制約 |
|---|---|---|
| `minecraft:constant` | `value` float | 定数。plain floatで省略可能 |
| `minecraft:add` | `inputs` | 1個以上の入力の和 |
| `minecraft:sub` | `left`, `right` | `left - right` |
| `minecraft:mul` | `inputs` | 1個以上の入力の積 |
| `minecraft:div` | `left`, `right` | `left / right`。NaN／Infinityになる入力へ依存しない |
| `minecraft:mod` | `left`, `right` | pre-1〜2はfloor modulus、pre-3は0方向へ丸める除算に対応した剰余。NaN／Infinityになる入力へ依存しない |
| `minecraft:pow` | `base`, `exponent` | floatの累乗。pre-3では`0^0`で中止。定義域外や非有限結果へ依存しない |
| `minecraft:abs` | `input` | 絶対値 |
| `minecraft:negate` | `input` | 符号反転 |
| `minecraft:min` | `inputs` | 1個以上の入力の最小値 |
| `minecraft:max` | `inputs` | 1個以上の入力の最大値 |
| `minecraft:avg` | `inputs` | 1個以上の入力の算術平均 |
| `minecraft:ceil` | `input` | 正の無限大方向へ丸めたfloat |
| `minecraft:floor` | `input` | 負の無限大方向へ丸めたfloat |
| `minecraft:round` | `input` | 最近傍へ丸め、ちょうど中間なら正の無限大方向へ丸めたfloat |
| `minecraft:truncate` | `input` | 0方向へ丸めたfloat |
| `minecraft:sin` | `input` | radian入力の正弦 |
| `minecraft:cos` | `input` | radian入力の余弦 |
| `minecraft:sqrt` | `input` | 平方根。負数入力の結果へ依存しない |
| `minecraft:length` | `inputs` | 1個以上の入力について平方和の平方根 |
| `minecraft:from_int` | `input` integer provider | integerをfloatへ変換 |
| `minecraft:uniform` | `min`, `max` | 指定範囲からfloatを選ぶ |
| `minecraft:weighted_list` | `distribution` | `data`と正integerの`weight`を持つ候補から選ぶ |
| `minecraft:conditional` | `condition`, `on_true`, 任意`on_false` | predicateが真なら`on_true`、偽なら`on_false`。省略時は`0.0` |
| `minecraft:number_dispatcher` | `cases`, 任意`default` | 順番に最初の真の`condition`に対応する`value`。該当なしの既定値は`0.0` |
| `minecraft:storage` | `storage`, `path`, 任意`fallback` | command storageのfloat。欠落、非数値、複数match時はfallback、既定は`0.0` |
| `minecraft:environment_attribute` | `attribute` | floatで表せるenvironment attribute値 |
| `minecraft:enchantment_level` | `amount` | enchantment level-based valueを現在のenchantment levelで評価 |

`from_int`の出力もsingle precisionです。大きなintegerは隣接値を区別できない場合があるため、変換後に元の32-bit値を完全保持できるとは仮定しません。

### Pre-Release 3の演算変更

`26.3-pre-3`のcontext依存float `minecraft:mod`は、integer `mod`と同様に0方向へ丸める除算に対応した剰余を使います。pre-1〜2のfloor modulusとは負数入力で結果が異なります。

| float式 | pre-1〜2（floor modulus） | pre-3（通常の剰余） |
|---|---:|---:|
| `4.0 mod -3.0` | -2.0 | 1.0 |
| `-4.0 mod 3.0` | 2.0 | -1.0 |
| `4.0 mod 3.0` | 1.0 | 1.0 |

表は公式記事に記載された剰余規則から計算した期待値です。入力fieldは引き続き`left`／`right`です。

```json
{
  "type": "minecraft:mod",
  "left": 4.0,
  "right": -3.0
}
```

pre-3でこの式をfloat providerとして評価する期待値は`1.0`です。周期や座標の正規化で負数を含む場合は、旧結果へ依存していないか確認します。integerの`floor_mod`とfloatの`mod`を同じ演算として扱いません。

float `minecraft:pow`はpre-3で底`base`と指数`exponent`がともに0の場合にerrorで計算を中止します。pre-1〜2で得られた値に依存する式は、入力制約または`conditional`などの分岐でこの組合せを避けます。integer `pow`はpre-1から同じ失敗条件です。

検証では、上表の正負の組合せ、`pow(0.0, 0.0)`の失敗、通常の`pow(2.0, 3.0)`の期待値`8.0`を確認します。`/compute`や`data modify ... compute`の評価失敗を成功・書き込み完了として扱わないでください。

### 三角関数とvector length

`sin`と`cos`の入力単位はdegreeではなくradianです。90度を渡したい場合は約`1.5707964` radianへ変換します。

```json
{
  "type": "minecraft:sin",
  "input": 1.5707964
}
```

結果はsingle precisionで約`1.0`です。組み込みの`pi` providerは公式type registryにないため、定数を使う場合は必要精度を明示してください。

`length`は複数入力`x1, x2, ...`に対し、`sqrt(x1*x1 + x2*x2 + ...)`を返します。

```json
{
  "type": "minecraft:length",
  "inputs": [3.0, 4.0]
}
```

この例は`5.0`を返します。2次元・3次元vectorの長さだけでなく、任意個数の入力を受けますが、空の`inputs`は使えません。

`tan(x)`に相当する専用typeはありません。`sin(x) / cos(x)`として合成できますが、`cos(x)`が0または0に近い場合のInfinity、NaN、精度悪化を呼び出し側で避ける必要があります。

### 丸めの違い

4つの丸めproviderはいずれもfloat providerであり、結果の数値型もfloatです。

| 入力 | `ceil` | `floor` | `round` | `truncate` |
|---:|---:|---:|---:|---:|
| 1.4 | 2.0 | 1.0 | 1.0 | 1.0 |
| 1.5 | 2.0 | 1.0 | 2.0 | 1.0 |
| -1.4 | -1.0 | -2.0 | -1.0 | -1.0 |
| -1.5 | -1.0 | -2.0 | -1.0 | -1.0 |
| -1.6 | -1.0 | -2.0 | -2.0 | -1.0 |

整数型が必要なら、丸め後に`minecraft:from_float`を使います。`from_float`自体は常に0方向へ切り捨てるため、先に選んだ丸め結果が整数値になっていることを確認します。

## 分岐、取得、乱数

### conditional

`conditional`は単一predicateで2分岐します。

```json
{
  "type": "minecraft:conditional",
  "condition": "example:is_enabled",
  "on_true": 10,
  "on_false": 0
}
```

`on_false`を省略した場合、integerでは`0`、floatでは`0.0`です。predicateが参照するloot context parameterを利用場所が供給しない場合を、単なる偽として扱えるとは仮定しません。

### number_dispatcher

`number_dispatcher`は`cases`を先頭から評価し、最初に真になったcaseの`value`だけを返します。

```json
{
  "type": "minecraft:number_dispatcher",
  "cases": [
    {
      "condition": "example:is_high",
      "value": 100
    },
    {
      "condition": "example:is_medium",
      "value": 50
    }
  ],
  "default": 0
}
```

caseの順序は意味を持ちます。複数条件が真でも最初のcaseだけが採用されます。

### storageとscore

`storage`は1件の数値NBTだけを読みます。pathが0件、複数件、または非数値ならfallbackを返します。数値NBT間の型変換結果は未定義とされているため、integer providerではinteger tag、float providerではfloat tagへ保存型を揃えます。

`score`はinteger専用です。scoreが存在しない場合はfallbackを返します。selector、固定名、context対象など`target`が受ける具体形は対象JARのcodecと利用contextで確定し、存在しないscoreを自動作成する用途には使いません。

### uniform、binomial、weighted_list

- integer `uniform`は`min`と`max`を含む閉区間から選ぶ
- float `uniform`は指定範囲から選ぶ。端点の厳密な出現可否へ依存する処理を作らない
- `binomial`はinteger専用で、`n`回の独立試行の成功数を返す。`p`だけはfloat provider
- `weighted_list.distribution[].weight`は正integer。0または負数を出力しない
- 乱数providerを同じ式の複数箇所へ複製した場合、同じsampleが再利用されるとは仮定しない

## resourceとコマンド例

次の2ファイルを定義します。

`data/example/context_int_provider/four_arithmetic.json`:

```json
{
  "type": "minecraft:div",
  "left": {
    "type": "minecraft:add",
    "inputs": [20, 4]
  },
  "right": {
    "type": "minecraft:sub",
    "left": 7,
    "right": 1
  }
}
```

`data/example/context_float_provider/vector_length.json`:

```json
{
  "type": "minecraft:length",
  "inputs": [3.0, 4.0]
}
```

consoleでは次の形で評価できます。

```mcfunction
/compute default integer example:four_arithmetic
/compute default float example:vector_length
/compute default float example:vector_length 100
```

float branchの任意`scale`はコマンド結果へ乗算するための値です。provider resource自体の返り値を書き換えません。`data modify ... compute`には`scale` branchがありません。

```mcfunction
/data modify storage example:result integer_value set compute default integer example:four_arithmetic
/data modify storage example:result float_value set compute default float example:vector_length
```

integer branchはinteger tag、float branchはfloat tagを書き込みます。providerの評価が失敗した場合はコマンドも失敗し、書き込み成功として扱えません。

## providerを受ける主なfield

119.0で明示された主なconsumerは次のとおりです。完全な一覧は対象JARのcodecとvanilla dataで閉じます。

| 値種類 | 主なfield |
|---|---|
| integer | `cooking_fuel.burn_time`、`brewing_fuel.uses`、`compostable.layers`、loot pool `rolls`、`enchant_with_levels.levels`、`set_count.count`、`limit_count.limit.min`／`max`、enchantment count、color、amplifier、dye count、stew duration、villager tradeの`max_uses`／`xp`／item count |
| float | `cooking_fuel.speed_multiplier`、`brewing_fuel.speed_multiplier`、loot pool `bonus_rolls`、attribute amount、`enchanted_count_increase.count`、custom model data float、`set_damage.damage`、villager tradeの`reputation_discount` |

`minecraft:int_value_check`と`minecraft:float_value_check`、`random_chance`、`time_check`、`entity_scores`も対応するproviderを受けます。consumerがintegerを要求する場所へfloat provider IDを、floatを要求する場所へinteger provider IDを直接渡しません。変換が必要なら`from_float`または`from_int`を式に含めます。

## 生成規則

- targetを収録済みlauncher IDへ完全一致させ、pre-1は119.0、pre-2は120.0、pre-3は121.0へ固定する
- float `mod`／`pow`には対象バージョンの演算規則を適用し、pre-3の変更をpre-1〜2へ書き戻さない
- provider resource、provider tag、consumer fieldの値種類を一致させる
- 旧`minecraft:number_provider`、旧type名、`operands`を119.0へ残さない
- 四則演算でinteger／floatのどちらが必要か、負数の除算規則、overflow、0除算を先に決める
- 三角関数の入力をradianにし、degreeを直接渡さない
- floatのNaN／Infinity、single precision、integer変換時の丸めへ依存しない
- 乱数providerの再評価回数を固定と仮定しない
- predicate、score、storage、environment attributeが必要とするcontextをconsumerが供給するか確認する
- `conditional`には公式JARで確認した単数field `condition`を使う

## 検証

基底となるPre-Release 1のtype／fieldは次で照合しました。

- Mojang公式Pre-Release 1記事のtype／field／丸め／失敗条件
- version manifestのlauncher ID `26.3-pre-1`
- SHA-1 `1e6e3a06cc13cf6975a0921b272ab544798d4b06`の公式server JAR
- 公式JARが生成した`reports/registries.json`のinteger 23 type、float 28 type
- 公式JARが生成したvanilla `context_int_provider`／`context_float_provider` resource

Pre-Release 3の演算差分はMojang公式記事とversion manifestで照合しました。SHA-1 `74b30963f532fa08c5f32311cc7caa0de41bf29e`の公式server JARでreport／vanilla dataを生成し、Pre-Release 2と比較して`commands.json`、`registries.json`、`datapack.json`、vanilla provider JSONに差分がないことを確認しました。上記の境界値は仕様からの期待値であり、ゲーム内の実行結果ではありません。

独自式は隔離した実験worldでreloadし、通常値だけでなく0除算、負数、32-bit境界、NaNになり得る入力、欠落score／storage、predicateが必要とするcontextも機能テストしてください。

## 出典

- [Mojang: Minecraft 26.3 Pre-Release 1](https://www.minecraft.net/en-us/article/minecraft-26-3-pre-release-1)
- [Mojang 公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Java Edition 26.3 Pre-Release 1](https://minecraft.wiki/w/Java_Edition_26.3-pre1)

- [Mojang: Minecraft 26.3 Pre-Release 3](https://feedback.minecraft.net/hc/en-us/articles/48740521840909-Minecraft-Java-Edition-26-3-Pre-release-3)
