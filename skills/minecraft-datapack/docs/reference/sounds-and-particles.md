# サウンドとパーティクル

データパックから音と粒子を再生する際のID、コマンド引数、到達範囲、対象player、バージョン境界をまとめます。音源ファイルやtexture自体はresource pack側の資産です。データパックは再生タイミング、位置、対象、登録済みIDを制御します。

## 役割の分離

| 要素 | 主な所有側 | データパックから行うこと |
|---|---|---|
| sound event | ゲームのregistry／resource packの`sounds.json` | IDを指定して再生・停止する |
| `.ogg`音源 | resource pack | 直接配布しない。event経由で参照する |
| particle type | ゲームのregistry | IDと型固有parameterを指定する |
| particle texture | resource pack | built-inまたはresource pack資産を使う |

custom soundを使うpackは、対応resource packの導入、配布方法、hash、導入失敗時のfallbackも設計します。

## `/playsound`

```text
playsound <sound> <source> <targets> [pos] [volume] [pitch] [minVolume]
```

```mcfunction
playsound minecraft:block.note_block.pling master @a ~ ~ ~ 1 1 0
```

| 引数 | 意味 | 設計上の注意 |
|---|---|---|
| `sound` | sound eventのresource location | 対象バージョンのregistryで存在を確認する |
| `source` | 音量設定のcategory | `master`、`music`、`record`、`weather`、`block`、`hostile`、`neutral`、`player`、`ambient`、`voice`等。1.21.6以降は`ui`も確認する |
| `targets` | 聞かせるplayer | selectorの絞り込みと実行dimensionに注意 |
| `pos` | 音源位置 | 省略時は実行位置。`at`と`positioned`の影響を受ける |
| `volume` | 基準音量と可聴距離 | 1より大きい値は主に到達範囲を広げる。全員へ同じ大きさで鳴らす指定ではない |
| `pitch` | 再生pitch | 許容範囲は対象コマンド木で確認する |
| `minVolume` | 通常範囲外にいる対象への最低音量 | 非0では遠距離playerにも各自の位置から聞こえる挙動を考慮する |

UI通知のように位置減衰させたくない用途と、world内の音源表現を同じ設計にしません。対象playerごとに`execute as ... at @s`して鳴らす場合と、固定地点から一度だけ鳴らす場合では結果が異なります。

26.3-pre-1のcommand treeでは`volume`は0以上、`pitch`は0〜2、`minVolume`は0〜1です。別バージョンへ値域を一般化せず、対象JARのargument propertiesを確認します。

## `/stopsound`

```text
stopsound <targets> [source] [sound]
```

```mcfunction
stopsound @a master minecraft:block.note_block.pling
```

`source`だけを指定するとcategory全体、`sound`まで指定すると該当eventを停止します。ループ音や長いcustom soundには、開始経路と対になる停止経路を用意します。

categoryを問わず特定eventだけを止める分岐では`*`を使います。

```mcfunction
stopsound @a * example:ui.confirm
```

## custom sound event

resource packの`assets/<namespace>/sounds.json`は次のようにeventから音源へ対応付けます。

```json
{
  "ui.confirm": {
    "sounds": [
      {
        "name": "example:ui/confirm",
        "stream": false
      }
    ],
    "subtitle": "subtitles.example.ui.confirm"
  }
}
```

このファイルはデータパックの`data/`配下には置きません。データパック側からは`example:ui.confirm`を再生します。音源名、event ID、翻訳keyを混同しないでください。

## `/particle`

```text
particle <particle> [pos] [delta] [speed] [count] [force|normal] [viewers]
```

```mcfunction
particle minecraft:happy_villager ~ ~1 ~ 0.4 0.6 0.4 0.02 20 normal @a[distance=..32]
```

| 引数 | 意味 | 設計上の注意 |
|---|---|---|
| `particle` | particle typeと、必要なら型固有parameter | exact syntaxは対象バージョンのparserに従う |
| `pos` | 発生中心 | 実行位置・dimensionを明示する |
| `delta` | 3軸の広がりまたは型に応じた計算入力 | 見た目を座標offsetだけで推測せず実機確認する |
| `speed` | 拡散速度等 | particle typeと`count`により意味が変わる場合がある |
| `count` | 個数 | `0`が特殊な方向指定になる歴史的構文があるため対象バージョンで確認する |
| `normal`／`force` | client側の表示距離・設定による抑制の扱い | `force`でも過剰生成を正当化しない |
| `viewers` | 送信先player | 近距離selectorでnetwork負荷を制限する |

## parameterを持つparticle

particle typeによって追加データが異なります。代表的なfamilyは次のとおりです。

| family | 代表的な追加情報 |
|---|---|
| block系 | block state |
| item系 | item stackとdata component |
| `dust` | 色、scale |
| `dust_color_transition` | 開始色、終了色、scale |
| vibration系 | destination、到達tick |
| `sculk_charge` | roll |
| `shriek` | delay |
| `trail` | target位置、色、duration |

parameterの記法は歴史的にコマンド後続引数からSNBT風のinline optionへ移行しています。古い例を貼り付けず、`reports/commands.json`の`minecraft:particle` parserと対象JARの実行結果を正本にします。item系particleでは1.20.5のdata component移行も適用します。

## 実行文脈と負荷

- `execute at <entity>`は位置とdimensionを変えるが、`as`だけでは変えない。
- entityごとに毎tick実行すると、粒子数だけでなくcommand実行数とpacket数も増える。
- animationは常時tickより、schedule、score、predicateで更新間隔を制御する。
- multiplayerでは`viewers`を距離で絞り、観測者ごとに同じeffectを重複送信しない。
- custom resource packがないclientでも処理が破綻しないfallbackを用意する。

## データ駆動JSON内のsound／particle

biome、worldgen、item component、enchantment effect、entity effectなどもsound eventやparticle optionを参照します。ただしfield名と表現は利用側codecごとに異なります。

- 単なるID、inline sound event、tag参照を相互に置換しない。
- particle typeだけでよい場所と、parameter付きparticle optionを要求する場所を区別する。
- `range`を持つinline sound eventは、resource packの音量設定や`/playsound`の`volume`と同じfieldではない。
- 利用側JSONの詳細は対象バージョンのvanilla resourceとregistry reportを照合する。

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.13 | Brigadier移行後のコマンド構文を基準にする |
| 1.20.5 | item stackを取るparticleでdata component移行を反映する |
| 1.21.4 | `trail`等の型固有fieldを対象バージョンで確認する |
| 1.21.6 | sound sourceに`ui`を追加。area effect cloud等のparticle field変更も個別に確認する |
| 1.21.11 | environment attributesによる環境表現と、明示的なコマンド演出を分ける |
| 26.3開発バージョン | 新規IDと型固有codecをsnapshot／pre-releaseごとに再生成する |

## 検証

1. `reports/registries.json`でsound eventとparticle typeのIDを確認する。
2. `reports/commands.json`で`playsound`、`stopsound`、`particle`の分岐と範囲を確認する。
3. 最小・最大距離、別dimension、対象0人、複数playerで試す。
4. clientの各音量category、字幕、particle表示設定、resource pack未導入を試す。
5. profilerとpacket量を見ながら、同時発生数と更新頻度を調整する。

## 関連資料

- [コマンド引数とselector](command-arguments-and-selectors.md)
- [registry elementとtag](registry-elements.md)
- [item componentとpredicate](components-and-predicates.md)
- [worldとenvironment attributes](world-and-environment.md)
- [実行モデル](../execution-model.md)

## 出典

- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6)
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- `build/minecraft/26.3-pre-1/generated/reports/commands.json`（26.3-pre-1公式server JARから生成、commit対象外）
- `build/minecraft/26.3-pre-1/generated/reports/registries.json`（同上）
