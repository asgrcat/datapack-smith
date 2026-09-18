# AI データパック生成契約

この文書は、利用者repositoryのproject設定と要件から、AIがどの資料をどの順で適用するかを定義します。

## 入力

永続化するproject設定の正本は、利用者repository rootの `datapack-project.json` です。schemaとtemplateは次にあります。

- `<harness-root>/schemas/datapack-project.schema.json`
- `<harness-root>/templates/datapack-project.json`

実装前に検査します。

```bash
python3 "$DATAPACK_SMITH_ROOT/tools/datapack_harness.py" \
  project-check --project datapack-project.json
```

- `target_version`、`namespace`、`pack_root`、対応範囲、experimental許可、server type、要求検証level、cache/report pathを会話だけに保持しない
- 省略された任意fieldにはハーネスの既定値を適用する。必須fieldは `schema_version`、`target_version`、`namespace`、`pack_root`、`validation_level`
- 実装要件はproject設定とは別に[設計契約](implementation-contract.md)へ記録する。調査のみならproject設定の新設は不要
- `edition` は `java` だけを受け付ける
- versionは [`versions/README.md`](versions/README.md) の正式リリース、または [`snapshots/README.md`](snapshots/README.md) の収録済み開発バージョンIDに完全一致させる
- 一覧にないsnapshot/pre-release/release candidate/Bedrock Editionを最寄りバージョンへ丸めない。`26.3`を最新の26.3開発バージョンとして解釈しない
- `26.1` を `1.26.1` に変換しない。文字列の辞書順や単純なsemver比較を使わず、version indexの順序を使う

## 解決アルゴリズム

```text
resolve(target_version):
  profile = versions/<target_version>.md or snapshots/<target_version>.md
  if profile does not exist:
    stop as unsupported

  validate profile against versions/profile.schema.json
  chain = resolve_inheritance(profile)
  active_rules = target profile's "AI 生成規則" bullets
  rule_history = ancestor rules for reference only
  json_parameter_history = chain's "JSONパラメータ差分" sections in order

  evidence = target profile + relevant versioned references
  reports = existing reports with matching version/provenance, if available
  if a required detail is unresolved and JAR/report generation is authorized:
    reports = generate_reports(official_manifest[target_version].server_jar)
  if reports exist:
    capabilities.commands = reports/commands.json
    capabilities.registries = reports/registries.json
    capabilities.datapack_registries = reports/datapack.json if present
    capabilities.vanilla_data = generated/data/minecraft
    capabilities.json_catalog = json-catalog(reports)

  state = common rules from commands.md and json-formats.md
  apply target profile's metadata and active_rules
  if requirements mention a family covered by json-parameters/README.md:
    read json_parameter_history and the family guide from json-parameters/README.md
  if requirements mention gameplay content:
    resolve observations and controls from content-hooks.md

  emit using target profile's data_pack_format and directory_schema
  check each JSON field in its consumer context using versioned-json.md
  resolve references by resource type: local pack / dependency pack / vanilla
  absence from vanilla examples alone does not prove a feature unsupported
  leave unresolved required details explicit; never invent their schema
```

`inherits` はmetadata、AI規則、JSONパラメータ差分の履歴追跡に使います。対象バージョンへ適用するAI規則は対象バージョン自体の `active_ai_rules` だけです。祖先規則は `rule_history` として出力しますが、後続バージョンで解除された禁止事項を累積適用しません。

`JSONパラメータ差分`は全プロファイルで存在と9 familyを検査し、`json_parameter_history`として1.13から対象バージョンまで順に出力します。これは追加・変更・削除・移行理由を解決する履歴です。その他の任意見出しから機能集合を合成せず、最終的に使用可能なcommand、registry、vanilla JSONは対象バージョンのJARから直接得ます。

機械処理では [`versions/profile.schema.json`](versions/profile.schema.json) の基本クラスと `compatibility_tags` を解釈します。本文の「コマンド」「JSON」「変更」などの見出し名は入力スキーマではありません。

## fail-closed

次の場合は推測で出力しません。

- 対象バージョンにcommand branchがあるか不明
- JSONの必須field、`type`固有field、loot contextが不明
- item component、entity predicate、text componentが境界バージョンのどちらか不明
- block/item/entity/registry IDが対象バージョンに存在するか不明
- experimental registryを通常worldで利用できるか不明

まず対象バージョンの公式資料と既存のreport/vanilla dataで確認します。必要なら [`validation.md`](validation.md) に従って生成します。JAR取得・Java実行を伴う手順と、資料だけで行う生成を区別します。環境がない場合も確認済みの独立部分は実装し、不明なfieldは推測せず未完了箇所と確認方法を示します。

## JSONキーを確定する単位

同じ`type`、`name`、`item`でも場所によって意味が異なります。各生成resourceで`対象ID / resource種別 / consumerのtype / JSON path / 値型 / 必須性・既定値 / 根拠`を揃えます。[バージョン別JSONの選択表](reference/versioned-json.md)から主要境界を選び、family文書と対象profileの差分で内側のfieldまで確認します。

正式リリースは1.13から対象までのfamily履歴を適用し、開発targetはその`inherits`枝だけを使います。後続リリースのreferenceは自動的には有効になりません。「同じformat」「継承」「vanillaに出現しない」はschema一致・非対応の証拠ではありません。旧keyを新keyと併記して互換を狙わず、対象ごとに1つの形を生成します。

## 出力順

1. 対象バージョン、data pack format、namespace
2. 完全なdirectory tree
3. `pack.mcmeta`
4. 全 `.mcfunction`
5. 全 JSON と必要な `.nbt` structure
6. entry pointごとのexecutor、位置、dimension、状態owner
7. 導入/reload手順
8. 対象バージョンでの検証項目
9. 複数バージョン対応なら共通部分とoverlayの対応表

「変更する部分だけ」を依頼された場合を除き、互いに参照するfileは省略しません。

workspaceへ作成した場合は、出力順に沿った説明とfileへの案内でよく、全内容の再掲は不要です。表示用例・schema断片・完全に配置できるresourceを区別します。

## resource命名

- 利用者指定がなければnamespaceは `generated` のような衝突しにくいlowercase IDを提案し、確定値を全fileで統一
- 自作function/tag/storage/predicate/loot tableは常にnamespaceを明示
- scoreboard objectiveはresource locationではないため、対象バージョンの長さ制約内で短い固有prefixを使う
- fake player/entity tagも他packと衝突しないprefixを持つ
- `minecraft` namespaceは `load`/`tick` tagへのentry追加や、明示されたvanilla overrideだけに使う

## 典型的な境界テスト

### 1.20.4 と1.20.5

要件: 名前付きdiamond swordを配る。

1.20.4:

```mcfunction
give @s minecraft:diamond_sword{display:{Name:'{"text":"Blade"}'}}
```

1.20.5:

```mcfunction
give @s minecraft:diamond_sword[minecraft:custom_name='{"text":"Blade"}']
```

pack formatだけを変更して同じfunctionを共有しません。

### 1.20.6 と1.21

要件: `example:init` function。

```text
# 1.20.6
data/example/functions/init.mcfunction

# 1.21
data/example/function/init.mcfunction
```

resource locationはどちらも `example:init` ですが、物理pathが異なります。

### 1.21.4 と1.21.5

要件: text表示。

1.21.4以前のJSON text文字列例を、1.21.5のSNBT component引数へそのまま二重quoteしません。click/hover field renameも同時に適用します。

### 26.1.2 と26.2

要件: player判定predicate。

26.1.2:

```json
{
  "type": "minecraft:player"
}
```

26.2:

```json
{
  "minecraft:entity_type": "minecraft:player"
}
```

26.2ではunknown fieldを拒否するため、旧 `type` を互換用に併記しません。

### 26.3開発バージョン

正式`26.3`は`versions/26.3.md`を選び、`26.2`からの確定差分を適用します。開発プロファイルは正式の継承に含めません。26.3の開発バージョンは `26.3-snapshot-1`〜`26.3-snapshot-10`と`26.3-pre-1`〜`26.3-pre-3`、`26.3-rc-1`、`26.3-rc-2`、`26.3-rc-3`を完全一致で選びます。各開発バージョンでdata pack formatと破壊的変更が進むため、「26.3向け」は正式リリースへ解決し、「最新snapshot向け」は具体的な収録IDが確定するまで生成しません。

開発バージョン向け生成では、隔離した実験world、対象JARのreport、対象formatへ固定したmetadataを必須にし、正式リリース互換とは報告しません。

## 複数バージョン

1. 最古バージョンの機能集合を基底にする
2. [`compatibility.md`](compatibility.md) の全境界を列挙
3. 同一pathで両立しないfileをoverlayへ
4. 1.20.2未満を含む場合、overlayを利用できないため別pack配布も検討
5. 1.21.9のmetadata境界をまたぐ場合、旧reader用fieldを残す条件を適用
6. 対象範囲の全正式リリース／開発バージョンでtestできない場合、「対応済み」と断定しない

## 検証levelと報告

project設定の `validation_level` を要求levelとします。

| level | 必要な証拠 | AIが報告できること |
|---|---|---|
| `generated` | profile解決と全file生成 | 対象バージョン向けに生成した |
| `static` | `validate-project` 成功 | 静的検査に成功した |
| `server` | exact serverでenabled/reload成功 | 対象バージョンのserverで読み込めた |
| `functional` | 機能test成功 | 記録した機能testに成功した |

AIは実行済みlevel、使用した対象バージョン、残っているwarning、未実施の上位levelを明記します。`static` が要求levelなら、server検査を省略してもハーネス利用失敗ではありません。

consumer CIは `static` を最小levelとします。`generated` levelの自動化は整備中のため、生成だけをCI成功として報告しません。

報告形式:

```text
target_version:
requested_level:
completed_level:
evidence:
warnings:
not_run:
```

levelにかかわらず、永続状態のowner・初期化・migration・cleanup、experimental利用、world upgradeの不可逆性、追加block/entityの観測・制御上の限界は、該当する場合に実装説明へ含めます。

`server` は利用者がEULA同意と実行環境を判断した場合だけ実行します。`functional` は実行した機能test結果だけを証拠にします。
