---
type: "Reference"
title: "OKF knowledgeの構造と参照方法"
description: "Datapack SmithのOKF v0.2バンドル、metadata、索引と更新手順。"
tags: ["minecraft-java", "okf", "documentation"]
sources: [{"id": "okf-spec", "resource": "https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md", "title": "Open Knowledge Format v0.2 Specification"}]
---

# OKF knowledgeの構造と参照方法

この`docs`ディレクトリ全体をOpen Knowledge Format（OKF）v0.2のknowledge bundleとします。`SKILL.md`、tools、schemas、templatesはbundleの外側にあり、Agent Skillsの配布形式を保ちます。OKFは文書形式を定め、スキルや実行環境の置き換えを要求しません。[^okf-spec]

## 構造

- [index.md](index.md): bundleの入口。`okf_version: "0.2"`と各ディレクトリ・conceptへの説明付きリンク
- `versions/index.md`: 正式リリースの一覧。1リリースにつき`versions/<version>.md`を1つ維持
- `snapshots/index.md`: 完全一致で指定する開発バージョンの一覧
- `reference/index.md`と`json-parameters/index.md`: 必要なresource種別・JSON familyの発見
- `guide.md`、`reference/guide.md`、`json-parameters/guide.md`: 参照順序や書式・JSON familyの読み方を説明するconcept
- `versions/catalog.md`、`snapshots/catalog.md`: 公開日とdata pack formatの対応表を持つconcept

`index.md`は索引専用です。root以外ではfrontmatterを持ちません。[log.md](log.md)にはこのbundleの変更をISO日付ごとに新しい順で記録します。配布物全体のリリース履歴は配布元のCHANGELOGで管理します。OKFでは`log.md`の配置は任意ですが、このbundleでは単独で配布しても履歴を確認できるように用意します。

## metadata

OKFで常に必須なのは空でない`type`です。このbundleでは発見しやすさのため、`title`、1行の`description`、文字列listの`tags`も全conceptへ付けます。[^okf-spec]

| field | このbundleでの用途 |
|---|---|
| `type` | `Minecraft Version`、`Reference`、`Playbook`、`Example`による分類 |
| `title` | 日本語の表示名。バージョン文書では対象ゲームIDも確認する |
| `description` | 文書の役割。索引生成時にリンクの説明へ反映する |
| `tags` | `minecraft-java`、機能・分野、`release`／`development`、完全一致バージョンID |
| `sources` | 外部URL、内部concept、対象JARの生成物などの参照範囲。本文の脚注は`id`をキーに結合する |
| `edition`、`version`、`inherits`など | Minecraft固有の拡張。対象profileの解決と検証に使用 |

metadataはトップレベルの`key: value`とし、文字列はJSONの引用形式、list・objectはJSONのflow形式で記述します。これは有効なYAMLの部分集合で、標準ライブラリだけの既存profile readerと共有できます。新しいfieldは既存のMinecraft fieldと重複させません。

`sources`は出典の所在を記録するもので、検証済みの保証ではありません。実施していない`verified`や人間によるレビューを追加しません。共通資料方針への参照しかない文書では、具体的な仕様の確認に対象profileと公式資料・JARを使います。

外部資料の本文リンクは`sources`にも記録します。本文の出典は安定した`sources[].id`をラベルにした脚注で結びます。`resource`には参照先のURI／pathだけでなく「対象server JARのreports/commands.json」のような参照範囲も書けます。範囲の説明を実在するbundle内ファイルと誤認しません。資料名、本文の参照、脚注のURLを変更するときは対応する`sources`も更新します。

## スキルからの取得

1. [index.md](index.md)から[参照手順](guide.md)と[AI生成契約](ai-authoring.md)を読む
2. 正式／開発の索引から完全一致する`Minecraft Version`を選び、Minecraft固有metadataと本文を読む
3. `title`・`description`・`tags`で必要なconceptを選び、本文のバージョン境界と参照リンクを辿る
4. 相対リンクは文書の場所、`/`始まりのbundle内pathはこの`docs`を基準に解決する
5. `sources`を辿り、対象バージョンの公式資料やJARで未確定の詳細を確認する

未知の`type`や追加fieldを理由に文書を捨てません。`verified`等の任意fieldがなくても参照できます。未知のゲームバージョンや不正なMinecraft profileは引き続き受け付けません。tagの一致や文書の新しさだけで、別バージョンの構文を対象へ適用しません。

`verified`の単一mappingは1件のlistと同じ意味です。未指定なら未検証、非`human:`actorだけなら機械確認、`human:`actorがあれば人間によるレビューと解釈します。`status`未指定は`stable`です。`draft`／`deprecated`と、現在時刻が`stale_after`以上の文書はその状態を明示し、実装へ採用する仕様を対象バージョンの一次資料で再確認します。欠けた任意metadataを補ってレビュー済み・最新と推定しません。

切れたリンクは未記載の知識への参照である場合もあり、bundle全体の形式不適合とはしません。必要な参照先が欠けている場合はその箇所を未解決として扱います。未知の`okf_version`でも可能な範囲で読み取ります。現在このbundleに`Attested Computation`はなく、harnessの通常の検査を実行証明付きの計算として扱いません。

## 更新と検証

保守用ツールだけがPyYAMLを使います。スキルによるMarkdown参照とデータパック検証ハーネスに追加依存はありません。利用者projectではなく配布元repositoryで実行します。

```bash
python3 -m pip install -r skills/datapack-smith/tools/requirements-dev.txt
python3 skills/datapack-smith/tools/okf_index.py --write
python3 skills/datapack-smith/tools/okf_index.py --conformance-only
python3 skills/datapack-smith/tools/okf_index.py
python3 skills/datapack-smith/tools/datapack_harness.py profiles
python3 -m unittest discover -s tests -v
```

索引はconceptのmetadataから生成します。本文を更新したら`description`・`tags`・`sources`も見直し、knowledgeの変更を`log.md`へ記録します。

`--conformance-only`はOKF §11の必須条件を確認します。通常実行は、このbundleで採用する`title`・`description`・`tags`、出典・脚注の整合、索引の最新性と任意metadataの書式も検査します。索引の存在、リンク切れの解消、出典や任意fieldの追加は、OKFの必須条件とは区別します。保守検査はこのbundleの運用規約のためのもので、外部OKF bundleを独自の追加条件で拒否するconsumerではありません。

[^okf-spec]: Open Knowledge Format Specification §3–6、§8、§11–12。
