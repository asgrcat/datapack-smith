# ダイアログ、入力、アクション

Java Edition 1.21.6以降のデータ駆動ダイアログと、ボタンから実行するアクションを扱います。ダイアログはサーバー側の処理を置き換えるものではなく、入力値をコマンドまたはcustom payloadへ渡すUIです。信頼境界は常にサーバー側へ置きます。

## 配置と参照

```text
data/<namespace>/dialog/<path>.json
```

ダイアログIDは`<namespace>:<path>`です。表示には次を使います。

```mcfunction
dialog show @s example:settings
```

他のダイアログからは`show_dialog` actionや`dialog_list`のentryとして参照できます。利用可能なdialog type、body type、input type、action typeは対象バージョンの`reports/registries.json`で確認します。

## 共通フィールド

| field | 必須性 | 意味 |
|---|---:|---|
| `type` | 必須 | `notice`、`confirmation`、`multi_action`、`server_links`、`dialog_list` |
| `title` | 必須 | 画面上部のtext component |
| `external_title` | 任意 | 一覧や外部導線に表示する短いtext component |
| `body` | 任意 | `plain_message`または`item`の配列 |
| `inputs` | 任意 | `text`、`boolean`、`single_option`、`number_range`の配列 |
| `can_close_with_escape` | 任意 | Escで閉じられるか。既定値`true` |
| `pause` | 任意 | singleplayerで開いたとき停止するか。既定値`true` |
| `after_action` | 任意 | action実行後の扱い。`close`、`none`、`wait_for_response` |

`after_action`の既定値は`close`です。`none`はsingleplayerを操作不能にしないため`pause: false`のときだけ使えます。`wait_for_response`は多重送信を抑える待機画面へ置き換え、サーバーが後続ダイアログを返す用途です。

### type固有フィールド

| type | 主なfield | 終了時のaction |
|---|---|---|
| `notice` | `action`。省略時はactionなしのOKボタン | `action`と同じ |
| `confirmation` | `yes`、`no` | `no`と同じ |
| `multi_action` | 空でない`actions`、`columns`、任意の`exit_action` | `exit_action`があれば実行 |
| `server_links` | `columns`、`button_width`、任意の`exit_action` | `exit_action`があれば実行 |
| `dialog_list` | `dialogs`、`columns`、`button_width`、任意の`exit_action` | `exit_action`があれば実行 |

`columns`の既定値は2、`button_width`の既定値は150です。`dialogs`は単一ID、list、dialog tagを取れます。type固有fieldを別typeへ流用しません。

## body

### `plain_message`

説明文を表示します。`contents`はtext component、`width`は表示幅です。

```json
{
  "type": "minecraft:plain_message",
  "contents": {"text": "設定を選択してください"},
  "width": 300
}
```

### `item`

item stackをinventory slotと同様に表示します。`item`が必須で、任意の`description`、`show_decorations`（既定値`true`）、`show_tooltip`（既定値`true`）、1〜256の`width`／`height`（既定値16）を持ちます。item componentを含むstack表現は対象バージョンの書式に従います。item stackの境界は[`components-and-predicates.md`](components-and-predicates.md)を参照してください。

## input

全inputは一意な`key`を持ちます。このkeyがdynamic actionへ渡す値の名前になります。

| type | 主なfield | 出力 |
|---|---|---|
| `text` | `label`、`initial`、`max_length`、`multiline`、`width` | string |
| `boolean` | `label`、`initial`、`on_true`、`on_false` | 選択に対応する値。tag出力ではbyte |
| `single_option` | `label`、`options`、`width` | 選択したoptionの`id` |
| `number_range` | `label`、`start`、`end`、`initial`、`step`、`width` | number |

`text.width`は1〜1024で既定値200、`max_length`の既定値は32です。`multiline`を使う場合は最大行数または高さを対象codecに合わせます。`number_range.step`は指定するなら正の値にします。

```json
[
  {
    "type": "minecraft:text",
    "key": "name",
    "label": {"text": "名前"},
    "initial": "Steve",
    "max_length": 32
  },
  {
    "type": "minecraft:boolean",
    "key": "enabled",
    "label": {"text": "有効"},
    "initial": true,
    "on_true": "1",
    "on_false": "0"
  },
  {
    "type": "minecraft:single_option",
    "key": "mode",
    "label": {"text": "モード"},
    "options": [
      {"id": "safe", "display": {"text": "安全"}, "initial": true},
      {"id": "fast", "display": {"text": "高速"}}
    ]
  },
  {
    "type": "minecraft:number_range",
    "key": "amount",
    "label": {"text": "量"},
    "start": 1,
    "end": 10,
    "initial": 5,
    "step": 1
  }
]
```

## action

ボタンは通常`label`、任意の`tooltip`、1〜1024の`width`（既定値150）、実行する`action`を持ちます。26.3-pre-1でreportに現れるaction typeは次のとおりです。

| action type | 役割 | 注意 |
|---|---|---|
| `run_command` | 固定コマンドを実行 | 先頭の`/`を含めない |
| `suggest_command` | chat入力欄へ候補を設定 | 実行は利用者操作 |
| `show_dialog` | 別のダイアログを表示 | 循環導線を避ける |
| `open_url` | 外部URLを開く | 利用者確認を前提にする |
| `copy_to_clipboard` | 文字列をclipboardへコピー | 秘密情報を含めない |
| `change_page` | book等のpageを変更 | actionを受ける文脈に限定 |
| `custom` | 固定payloadをcustom actionとして送る | 受信側実装が必要 |
| `dynamic/run_command` | inputをfunction macroへ渡してコマンドを組み立てる | 入力値を命令として信頼しない |
| `dynamic/custom` | inputと追加値をcompound tagとして送る | 受信側で型・範囲を再検証する |

`dynamic/run_command`はinput keyをmacro parameterとして展開します。一致しないparameterは空になります。文字列入力をコマンド構文へ直接埋め込む設計は、引用符やselector、改行を含む入力で意味が変わり得ます。可能なら選択肢を固定し、呼び先function内でもallowlist、範囲、権限、現在状態を検査してください。

## 最小構成

```json
{
  "type": "minecraft:notice",
  "title": {"text": "確認"},
  "body": [
    {
      "type": "minecraft:plain_message",
      "contents": {"text": "処理を開始します"}
    }
  ],
  "action": {
    "label": {"text": "閉じる"},
    "action": {
      "type": "run_command",
      "command": "function example:dialog/closed"
    }
  }
}
```

field名とactionのnamespace省略可否は対象バージョンで再検証してください。開発バージョンではcodecが変わり得るため、上の例を近いsnapshotへ横流ししません。

## セキュリティとmultiplayer

- ダイアログを開いたplayerと、コマンドの実行主体・権限を明示する。
- inputは信頼済みデータではない。文字数、数値範囲、候補ID、実行可能状態をサーバー側で再検査する。
- `open_url`は遷移先を固定し、入力からURL全体を生成しない。
- 二重送信、再接続、画面を閉じた場合を含め、actionを冪等にする。
- `pause`はmultiplayer全体を停止する機能ではない。

## バージョン境界

| バージョン | 境界 |
|---|---|
| 1.21.5以前 | データ駆動dialog resourceは使用しない |
| 1.21.6 | dialog、body、input、actionと`/dialog`を導入 |
| 1.21.11 | 1.21.6の基礎を継承。対象JARのreportで型一覧を確定 |
| 26.3開発バージョン | actionやcodecの追加・変更をsnapshot単位で確認 |

## 検証

1. `reports/datapack.json`で`minecraft:dialog`が定義可能か確認する。
2. `reports/registries.json`でdialog、body、input、action typeを照合する。
3. `/reload`後に`/dialog show @s <id>`で各分岐を開く。
4. 空入力、最大長、範囲端、Esc、二重押下、権限不足を試す。
5. dynamic actionは展開後のコマンドまたはpayloadを受信側で記録して確認する。

## 関連資料

- [text component](text-components.md)
- [コマンド引数とselector](command-arguments-and-selectors.md)
- [NBT、SNBT、`/data`](nbt-snbt-and-data.md)
- [registry elementとtag](registry-elements.md)
- [1.21.6](../versions/1.21.6.md)

## 出典

- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6)
- `build/minecraft/26.3-pre-1/generated/reports/registries.json`（26.3-pre-1公式server JARから生成、commit対象外）
- `build/minecraft/26.3-pre-1/generated/data/minecraft/dialog/`（同上）
