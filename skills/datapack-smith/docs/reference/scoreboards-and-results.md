# Scoreboardとcommand result

この文書はscoreboard objective／score holder／演算と、commandのsuccess／result、`execute store`を扱います。状態の所有権、migration、uninstallは[`../state-management.md`](../state-management.md)で設計します。

## 値モデル

scoreはobjectiveとscore holderの組に属する32-bit signed integerです。

```text
(holder, objective) -> 未設定 または -2147483648〜2147483647
```

未設定と0は異なります。selectorの`scores={...}`、`execute if score`、`scoreboard players get`は未設定scoreを0として自動作成しません。

## Objective

```mcfunction
scoreboard objectives add example.state dummy
scoreboard objectives add example.used minecraft.used:minecraft.carrot_on_a_stick
scoreboard objectives setdisplay sidebar example.state
```

| 種類 | 用途 |
|---|---|
| `dummy` | commandだけで変更する任意状態 |
| built-in criterion | gameplay eventを自動集計 |
| trigger | playerが`/trigger`で変更できる一時入力 |
| health等 | 表示／読取中心で変更制約を持つcriterion |

criterion名と利用可能性は対象JARで確認します。objective名はresource locationではないため、pack prefixと文字数制約を守ります。

## Score holder

```mcfunction
scoreboard players set @s example.state 1
scoreboard players set #phase example.state 2
scoreboard players add @a example.cooldown 0
```

holderにはplayer、entity、UUID、fake player名等を使えます。

- `#phase`のようなfake playerは通常selectorに一致しない内部定数に向く
- 実在player名と衝突しにくいprefixを使う
- offline playerのscoreもworldに残る
- entity消滅後のscore cleanupを必要に応じて設計する
- `add ... 0`は未設定scoreの初期化に使える
- `reset`は未設定へ戻し、0代入とは異なる

## 基本操作

```mcfunction
scoreboard players set #value example.tmp 10
scoreboard players add #value example.tmp 2
scoreboard players remove #value example.tmp 1
scoreboard players reset #value example.tmp
```

`set`／`add`／`remove`が複数holderを対象にした場合、各holderへ個別に作用します。途中の別command失敗で先行変更がrollbackされることはありません。

## `operation`

```mcfunction
scoreboard players operation #out example.tmp = #in example.tmp
scoreboard players operation #out example.tmp += #delta example.tmp
scoreboard players operation #min example.tmp < #value example.tmp
scoreboard players operation #a example.tmp >< #b example.tmp
```

| operation | 意味 |
|---|---|
| `=` | 代入 |
| `+=` | 加算 |
| `-=` | 減算 |
| `*=` | 乗算 |
| `/=` | 整数除算 |
| `%=` | 整数剰余 |
| `<` | 小さい値をtargetへ代入 |
| `>` | 大きい値をtargetへ代入 |
| `><` | targetとsourceをswap |

source scoreが未設定、0除算、範囲外演算のsuccess／resultを対象バージョンでtestします。特に1.13.1で`%=`がtruncating remainderから`floorMod`へ変更され、`-1 %= 7`は`6`になりました。古い正式リリースと新しい演算を同一視しません。

## 比較

```mcfunction
execute if score @s example.level matches 1..5 run function example:level/low
execute if score #a example.tmp = #b example.tmp run function example:equal
execute unless score @s example.ready matches 1 run function example:not_ready
```

`matches`はinteger range、score同士の比較は`<`、`<=`、`=`、`>=`、`>`を使います。未設定scoreを条件falseとして扱うのか、初期化漏れとして失敗させるのかを設計します。

## Successとresult

commandには表示messageとは別にsuccessとinteger resultがあります。

| 値 | 概念 |
|---|---|
| success | commandが条件を満たし有効に実行されたか |
| result | 変更数、取得値、対象数等のcommand固有integer |

同じcommandでもbranchやバージョンでresultの意味が変わります。例えばteam join／leave、give、data get等の結果を一律に「成功件数」としません。

```mcfunction
execute store success score #ok example.tmp run function example:try
execute store result score #count example.tmp run clear @a minecraft:stone 0
```

`success`は通常0／1、`result`はcommand固有です。複数executorへ分岐した`execute`ではstore先が同じfake playerだと後のbranchが前の値を上書きし得ます。

## NBTとの変換

```mcfunction
execute store result storage example:state value int 1 run scoreboard players get @s example.value
execute store result score @s example.value run data get storage example:state value 1
```

- storageへは数値NBT型とscaleを指定する
- float／doubleからscoreへ保存するときの丸めをtestする
- compound、list、string全体はscoreへ保存できない
- missing pathや複数matchのresultを正常値と混同しない

## Player別状態

```mcfunction
scoreboard players add @a example.cooldown 0
execute as @a[scores={example.cooldown=1..}] run scoreboard players remove @s example.cooldown 1
execute as @a[scores={example.cooldown=0}] at @s run function example:ready
```

初参加、死亡、dimension移動、logout中、名前変更、再参加を考慮します。player UUIDとscore holderの永続性をstorage内の独自indexと重複管理する場合は正本を決めます。

## `/trigger`

trigger objectiveはplayer入力用です。

```mcfunction
scoreboard objectives add example.menu trigger
scoreboard players enable @a example.menu
execute as @a[scores={example.menu=1..}] run function example:menu/select
scoreboard players reset @a example.menu
```

値を処理した後にresetし、必要なタイミングで再度enableします。chat入力をAPIとして公開する場合は許容rangeを検証します。

## 表示

sidebar、list、below-name等のdisplay slotはgameplay状態の正本とは別です。1.20.3以降はscoreboard entryのdisplay nameとnumber formatを設定できます。

- UI用objectiveと内部演算用objectiveを分ける
- playerへ見せるtranslation／colorと内部holder名を混同しない
- display slot名のrename境界を対象profileで確認する
- 表示を消してもscore自体は削除されない

## 定数と一時値

```mcfunction
scoreboard players set #two example.const 2
scoreboard players operation @s example.value *= #two example.const
```

load functionで毎回設定してよい定数と、既存worldから保持すべき状態を分けます。一時objectiveの値が複数player／recursive functionで競合しないよう、executor別scoreまたは明示したworkspace holderを使います。

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.13 | command体系を再設計し、team／tagを専用commandへ分離 |
| 1.13.1 | `%=`をfloor modulusへ変更 |
| 1.15 | `execute store`からstorageへ保存可能 |
| 1.20.2 | display slot名のsnake_case化等 |
| 1.20.3 | entry display nameとnumber format |
| 1.21.11 | gamerule等のregistry化とは別に、objectiveは従来のscoreboard体系を維持 |
| 26.3-pre-1 | integer number providerからscoreを読み、`/compute`結果へ利用可能 |

## 生成規則

- objectiveの作成、初期化、migration、cleanupを定義する
- 未設定と0を区別する
- 0除算、負数、32-bit境界へ依存する演算をtestする
- successとresultのどちらが必要かcommandごとに選ぶ
- 複数executorが同じstore先を上書きしないようにする
- UI表示用と内部状態用を分ける
- uninstallでobjectiveを削除するか利用者へ確認できる手順を用意する

## 検証

演算前後のscore、command success、resultを別holderへ記録します。未設定source、0除算、最小／最大integer、複数target、offline player、reload、再起動、pack更新をtestします。

## 出典

- 各 [`../versions/<version>.md`](../versions/README.md) のscoreboard／command差分
- 対象server JARの`commands.json`
