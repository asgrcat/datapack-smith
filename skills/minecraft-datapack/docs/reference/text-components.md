# Text component

text componentは、chat、title、item名、dialog、death message等の構造化textです。この文書はJava Edition 1.13以降の内容type、style、event、JSON／SNBT境界を扱います。resource packのfont画像や翻訳ファイル自体は対象外です。

## 保存形式と意味を分ける

同じcomponentでも外側の場所により表現が異なります。

| 場所 | 代表表現 |
|---|---|
| JSON resourceのfield | JSON object／array／許可された省略形 |
| 1.20.4以前のcommand／NBT | JSON textをSNBT stringへ入れる場所が多い |
| 1.21.5以降のcommand／NBT | SNBT objectとしてcomponentを直接書く場所が増加 |
| network／client表示 | serverが解決・検証したcomponent |

「componentがJSONに似ている」ことと、外側のファイルがJSONであることは別です。command引数へJSON用の二重quoteを残したり、JSON resourceへSNBTのsuffixやtrailing commaを入れたりしません。

## 内容type

代表的なcomponentは次です。利用可能なtypeと省略形は対象バージョンで確認します。

| 内容 | 主なfield | 用途 |
|---|---|---|
| literal | `text` | 固定文字列 |
| translatable | `translate`, 任意`with`, `fallback` | language keyをclient側で翻訳 |
| score | `score.name`, `score.objective` | scoreboard値を表示 |
| selector | `selector`, 任意`separator` | selector結果のentity名 |
| keybind | `keybind` | clientの割当key名 |
| NBT | `nbt`, source、任意`interpret`, `separator` | block／entity／storage NBTを表示 |
| object | type固有field | 1.21.9以降のatlas sprite／player object等 |

### Literalとsiblings

```json
{
  "text": "HP: ",
  "color": "red",
  "extra": [
    {
      "score": {
        "name": "@s",
        "objective": "example.hp"
      },
      "color": "white"
    }
  ]
}
```

`extra`は親componentの後ろへsiblingsを連結します。styleは明示的に上書きしない限り子へ継承される場合があるため、再利用するcomponentでは必要styleを明記します。

### Translation

```json
{
  "translate": "chat.type.text",
  "with": [
    {
      "selector": "@s"
    },
    {
      "text": "Hello"
    }
  ],
  "fallback": "%s: %s"
}
```

`fallback`は1.19.4以降です。placeholder数と`with`の値数を合わせ、clientごとに翻訳後の語順が変わることを前提にします。

### NBT component

```json
{
  "nbt": "config.message",
  "storage": "example:state",
  "interpret": false
}
```

sourceは対象バージョンに応じて`block`、`entity`、`storage`等です。`interpret: true`はNBT文字列をさらにtext componentとしてparseするため、外部入力をそのまま解釈しません。大量matchや循環的な解決へ依存せず、1.21.5以降も解決上限を考慮します。

## Style

| field | 型 | 意味 |
|---|---|---|
| `color` | named color／`#RRGGBB` | 文字色。hexは1.16以降 |
| `font` | resource location | 使用font |
| `bold` | boolean | 太字 |
| `italic` | boolean | 斜体 |
| `underlined` | boolean | 下線 |
| `strikethrough` | boolean | 取消線 |
| `obfuscated` | boolean | 難読化表示 |
| `insertion` | string | shift-click挿入文字列 |
| `click_event`／旧`clickEvent` | object | click時action |
| `hover_event`／旧`hoverEvent` | object | hover時表示 |

field名やevent objectの形はバージョンで変わります。対象バージョンのvanilla JSONとprofileを優先し、camelCaseとsnake_caseを混在させません。

## Click eventと安全性

代表action:

| action | 影響 |
|---|---|
| `run_command` | player権限でcommand実行を試みる |
| `suggest_command` | chat入力欄へ文字列を設定 |
| `open_url` | clientへURL確認を表示 |
| `copy_to_clipboard` | client clipboardへcopy。1.15以降 |
| `show_dialog` | dialogを開く。1.21.6以降 |
| `custom` | client／server間のcustom action。対応バージョン限定 |

- `run_command`へ利用者入力やNBTを無検証で連結しない
- `/op`等の権限をcomponentが昇格させるとは仮定しない
- signのclick eventは26.3-snapshot-4以降、`allow_op_features`が既定false
- URL、clipboard、custom payloadはclient境界をまたぐため内容と長さを制限する
- 1.19.1で`run_command`値に先頭`/`が必要になった境界を対象profileで確認する

## Hover event

代表actionはtext表示、item表示、entity表示です。1.16で旧`value`中心の形から`contents`を使う形へ移行しました。item stackとentity内容はcomponent本文とは別codecなので、対象バージョンのitem component／entity形式を適用します。

```json
{
  "text": "Diamond",
  "hoverEvent": {
    "action": "show_item",
    "contents": {
      "id": "minecraft:diamond",
      "count": 1
    }
  }
}
```

この例のfield名は1.20.4以前の形です。新しいsnake_case形を古いバージョンへ、古いitem `tag`をcomponent時代へ持ち込みません。

## Commandでの表現

### 1.20.4以前

```mcfunction
tellraw @s {"text":"Hello","color":"gold"}
give @s minecraft:paper{display:{Name:'{"text":"Note"}'}}
```

item NBTではJSON textをSNBT stringへ入れる二重構造です。

### 1.20.5〜1.21.4

itemはdata component patchへ移行しますが、text componentのcommand表現は利用場所ごとに確認します。

```mcfunction
give @s minecraft:paper[minecraft:custom_name='{"text":"Note"}']
```

### 1.21.5以降

多くのcommand引数とNBT fieldでSNBT componentを直接使います。

```mcfunction
tellraw @s {text:'Hello',color:'gold'}
give @s minecraft:paper[minecraft:custom_name={text:'Note'}]
```

1.21.4以前のJSON string wrapperを残しません。逆に1.21.5のunquoted key、single quote、SNBT拡張をJSON resourceへ入れません。

## 厳格化の境界

| バージョン | 主な変更 |
|---|---|
| 1.13 | raw JSON textをcommand／NBTの基準にする |
| 1.15 | NBT sourceにstorage、click actionにclipboardを追加 |
| 1.16 | hex color、font、hover `contents` |
| 1.19.1 | `run_command`値のslash要件 |
| 1.19.4 | translatable `fallback` |
| 1.20.3 | `null`／空array、不正color／event等を厳格に拒否。任意`type`とNBT `source`を追加 |
| 1.20.5 | item名等を旧item NBTからdata componentへ移行 |
| 1.21.5 | command／NBTのcomponentをSNBT objectとして直接表現する大変更 |
| 1.21.6 | data pack JSONをstrict JSONでparse |
| 1.21.9 | object componentを追加 |
| 26.3-snapshot-1 | NBT componentの解決回数を64Kへ制限 |

## 生成規則

- 外側がJSON、SNBT、command argumentのどれかを先に決める
- component内容と外側serializationを別々に検証する
- 対象バージョンのevent field名、action、item stack形を使う
- player入力、score、selector、NBTが0件／複数件の場合のseparatorを設計する
- `interpret`、`run_command`、URL、custom actionへ未検証入力を渡さない
- 翻訳keyがclient resource packにない場合のfallbackを考慮する

## 検証

JSON resourceはJSON parser、commandは対象JARの`commands.json`、item／entity保存値は実際の`data get`で確認します。表示だけでなくclick／hover、権限不足、欠落translation、複数selector結果、NBT解決上限もtestします。

## 出典

- 各 [`../versions/<version>.md`](../versions/README.md) のtext／NBT差分
- [Mojang Java Edition release notes](https://www.minecraft.net/en-us/articles)
