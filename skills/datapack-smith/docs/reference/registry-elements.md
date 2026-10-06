# Registry element、参照、holder set

この文書は、データパック内のregistry elementをinline値、namespaced ID、tag、listとして受け渡す書式を扱います。正式Java Edition 26.3の直接参照と混在listを扱い、旧バージョンとの境界を区別します。

## 最初に区別するもの

| 表現 | 例 | 意味 |
|---|---|---|
| element ID | `example:fast` | registryに登録された1要素を参照 |
| tag ID | `#example:fast` | registry要素の集合を参照 |
| inline element | `{"type":"minecraft:..."}` | 参照元の中で無名要素を定義 |
| element list | `["example:a","example:b"]` | 順序を持つ複数要素 |
| holder set | 単一ID、list、tagのいずれか | 要素集合を受けるcodec。inline対応はfieldごとに異なる |

resource locationの文字列であることだけでは、ID、tag、任意文字列のどれとして解釈されるかは決まりません。外側のcodecが期待するregistryと値形を決めます。

## Resourceの定義と参照

正式26.3の次のpredicate resourceは`example:is_ready`として登録されます。1.15〜26.2ではdiscriminatorを`condition`にし、1.20.6以前の配置は`predicates/`へ変えます。

`data/example/predicate/is_ready.json`:

```json
{
  "type": "minecraft:entity_scores",
  "entity": "this",
  "scores": {
    "example.ready": 1
  }
}
```

26.2以前のpredicate fieldでID文字列を直接受けるとは限りません。対象バージョンによって`minecraft:reference` wrapper、inline object、直接IDのどれを使うかが変わります。

## Tag

registry tagは、対応するregistry pathの下へ置きます。1.21以降の基本形は次です。

`data/example/tags/<registry-path>/fast.json`:

```json
{
  "replace": false,
  "values": [
    "example:a",
    "example:b",
    {
      "id": "example:optional",
      "required": false
    }
  ]
}
```

- `replace: false`は下位packのtag内容へ追加する
- `replace: true`は下位packのtag内容を捨てる
- `required: false`は参照先がない場合だけそのentryを無視する
- tag自体を参照するfieldでは`#example:fast`の`#`を省略しない
- tagを受けない単一element fieldへtag IDを渡さない

1.18.2以降は任意registryのtagをデータパックから定義できますが、resource folderの複数形／単数形は対象バージョンに合わせます。

## 26.3のelement value

### 正式26.3の単一参照

正式26.3では、advancement、item modifier、loot table、context integer／float provider、predicate、recipe、slot source等で、registry ID、tag、inline値を共通のelement value／element set codecへ移行しました。

主な変更:

- predicateやloot functionの`reference` typeを直接ID参照へ置換
- predicate discriminatorを`condition`から`type`へ変更
- loot function discriminatorを`function`から`type`へ変更
- 暗黙ANDの`conditions`配列を単一`condition`へ変更し、複数条件は`all_of`で明示
- holder setを受けるfieldで単一ID、ID list、tagを選択可能

すべてのfieldがtagやinline値を受けるわけではありません。「element value」「element list」「holder set」「単一ID」は別codecです。

### 正式26.3の混在list

正式26.3では、同じelement list内でinline値とID参照を混在できるようになりました。

```json
[
  "example:shared",
  {
    "type": "minecraft:constant",
    "value": 2
  }
]
```

この形は112.0より前へ出力しません。111.0で「inline list」と「ID list」が別分岐だったfieldでは、混在listがloadに失敗します。

### 明示typeと集合の省略形

正式26.3ではitem modifier／slot sourceを受けるfieldでlist／tagによるsequence／groupの省略形を使えます。stand-alone fileには省略形を使わず明示objectを置きます。明示typeのsequence／group objectをnested位置で使う代わりに、独立resourceのIDも参照できます。開発中の制約は下のバージョン表とsnapshot履歴を参照します。

「IDを受けられる」と「参照先resourceのrootをID文字列だけにできる」は同じではありません。top-level alias、nested inline、element listの各位置を個別に確認します。

## 値形の選択

| 要件 | 選択 |
|---|---|
| その場所だけで使う短い値 | inline element |
| 複数箇所で再利用する | 独立resource＋ID |
| 利用者や別packが集合へ追加する | tag |
| 順序に意味がある処理 | list。tag展開順へ依存しない |
| typeがtop-level限定 | 独立resourceへ分離しnested位置からID参照 |

tagは公開拡張点に向きますが、処理順を固定するAPIではありません。最初に一致した要素を使うdispatcherやmodifier列では、明示listを使い、順序を機能テストします。

## 参照の安全性

- 自己参照と循環参照を作らない
- optional tag entryを必須resourceの代替にしない
- ID参照で新しいloot contextや実行文脈が作られると仮定しない
- 同名resourceの上書きとtagのmergeを区別する
- inline値を独立resourceへ移したとき、外側から供給されるcontextが変わらないことを確認する
- `minecraft` namespaceへ独自elementを置かず、明示したvanilla override以外は自分のnamespaceを使う

## バージョン境界

| バージョン | 境界 |
|---|---|
| 1.13 | データパックresourceとnamespaced IDを基準化 |
| 1.18.2 | universal registry tagを追加 |
| 1.21 | resource／tag folderを原則単数形へ変更 |
| 26.3-snapshot-4 | 多数のfieldを直接element／holder set参照へ統一 |
| 26.3-snapshot-5 | element listでinline値とID参照を混在可能 |
| 26.3-snapshot-9 | top-level aliasを修正し、一部inline typeをtop-level限定化 |
| 26.3-pre-1 | integer／float providerを別registryと別tagへ分割 |

## 検証

1. `reports/datapack.json`で対象registryが`elements`／`tags`に対応するか確認する
2. `reports/registries.json`でtype IDが存在するか確認する
3. 同じ外側fieldを使うvanilla JSONで、単一／list／tag／inlineの分岐を確認する
4. missing ID、optional entry、空tag、循環参照、混在listを別々にreloadする
5. 順序が意味を持つ場合は展開後の評価順を機能テストする

## 出典

- [Mojang: Minecraft 26.3 Snapshot 4](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-4)
- [Mojang: Minecraft 26.3 Snapshot 5](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-5)
- [Mojang: Minecraft 26.3 Snapshot 9](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-9)

- [Mojang: Java Edition 26.3](https://feedback.minecraft.net/hc/en-us/articles/48913133328013-Minecraft-Java-Edition-26-3)

## 26.4 Snapshot 3の追加registry

`minecraft:block_sound_set`はelementとtagを持つデータ駆動registryです。配置、field、既定値と値域は[音と粒子reference](sounds-and-particles.md#264-snapshot-3のblock-sound-setとparticle)を参照します。対象は`26.4-snapshot-3`以降の収録済み開発バージョンで、正式26.3やSnapshot 1〜2には出力しません。
