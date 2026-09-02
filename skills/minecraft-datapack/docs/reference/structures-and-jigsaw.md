# Structure NBT、jigsaw、worldgen structure

この文書はデータパックのstructure NBTと、template pool、processor list、worldgen structure／structure set、`/place`、GameTestの接続を扱います。同じ「structure」という語でもbinary templateとworldgen配置定義は別resourceです。

## 5つの層

```text
structure NBT
└── template pool element
    ├── processor list
    └── projection
        └── worldgen structure
            └── structure set／placement
```

| 層 | 役割 |
|---|---|
| structure NBT | block、block entity、entity、paletteを保存するtemplate |
| template pool | jigsawが選ぶtemplate候補とweight |
| processor list | template配置時にblockを置換・省略・処理 |
| worldgen structure | 開始条件、biome、step、terrain adaptation等 |
| structure set | spacing／concentric rings等の配置規則 |

`/place template`はstructure NBTを直接置きますが、worldgen structureのbiome判定やstructure set配置を実行するものではありません。

## Structure NBTの配置

| バージョン | path |
|---|---|
| 1.13〜1.20.6 | `data/<namespace>/structures/<path>.nbt` |
| 1.21以降 | `data/<namespace>/structure/<path>.nbt` |

fileはgzip圧縮NBTです。JSONやSNBT textを`.nbt` extensionで保存しません。

## NBTの概念構造

structure templateは概念的に次を持ちます。

| field | 内容 |
|---|---|
| `DataVersion` | 保存したgame data version |
| `size` | X／Y／Z size |
| `palette`または`palettes` | block state表 |
| `blocks` | position、palette index、任意block entity NBT |
| `entities` | position、block position、entity NBT |

binary NBTを手作業でindex編集するより、対象バージョンのstructure block、`/test`関連機能、公式toolで保存します。palette index、size、block positionの不整合はload失敗や欠落配置につながります。

## DataVersionと移行

- 1.12以前のtemplateは旧バージョンで読み、1.13で再保存してから配布する
- 新しいDataVersionのNBTを古いserverへdowngradeしない
- entity、block entity、item stack、text componentのDataFixがstructure内部にも適用され得る
- 更新後は同じtemplateを新規worldで配置し、block state、container、entityを比較する
- structure NBTを単にbyte一致させるのでなく、対象versionでの配置結果を検証する

## `/place template`

```mcfunction
place template example:room ~ ~ ~
```

rotation、mirror、integrity、seed等のbranchは対象`commands.json`で確認します。

- placement originとtemplate内pivotを区別する
- integrityが1未満なら一部blockをrandomに省略する
- entityを含むか、block updateを行うかを対象branchで確認する
- loaded chunk、world border、高さ範囲を確認する
- command成功と全blockが置かれたことを同一視しない

## Template pool

1.21以降の配置:

```text
data/<namespace>/worldgen/template_pool/<path>.json
```

```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "element_type": "minecraft:single_pool_element",
        "location": "example:room",
        "processors": "minecraft:empty",
        "projection": "rigid"
      }
    }
  ]
}
```

field名は対象バージョンのvanilla poolを正本にします。pool element typeにはsingle、legacy single、list、feature、empty等があります。

### Weightとfallback

- weightは正integerを使う
- weight 0を「無効entry」として生成しない
- fallbackはjigsaw展開が継続できない場合のpool
- fallback循環や無制限再帰へ依存しない
- pool内templateのjigsaw `target_pool`と参照先IDを検査する

## Processor list

```json
{
  "processors": [
    {
      "processor_type": "minecraft:block_ignore",
      "blocks": [
        "minecraft:structure_block"
      ]
    }
  ]
}
```

processor typeとfield名はバージョンで変わります。代表的な役割:

- blockを無視する
- rule predicateで置換する
- block／block entity dataを変更する
- protected blockを避ける
- gravityやcap処理を加える

processor順序は意味を持ちます。前のprocessorが変更したstateを後のprocessorが見るかを実際の配置で確認します。

## Worldgen structure

worldgen structureはtemplateそのものではなく、どのbiome／generation step／terrain条件で開始するかを定義します。

主な共通field:

| field | 意味 |
|---|---|
| `type` | structure type |
| `biomes` | biome ID／tag集合 |
| `step` | generation step |
| `spawn_overrides` | mob categoryごとのspawn override |
| `terrain_adaptation` | 地形との接続方法 |

jigsaw structureではstart pool、size、start height、max distance、dimension padding等のtype固有fieldがあります。各バージョンの同type vanilla JSONを基底にします。

## Structure set

structure setは候補structureと配置typeを結びます。

```json
{
  "structures": [
    {
      "structure": "example:camp",
      "weight": 1
    }
  ],
  "placement": {
    "type": "minecraft:random_spread",
    "spacing": 32,
    "separation": 8,
    "salt": 123456789
  }
}
```

`spacing`は`separation`より大きくします。salt、frequency reduction、locate offset等のfieldは対象typeで確認します。既生成chunkは定義変更だけで再生成されません。

## `/place jigsaw`と`/place structure`

- `place template`: NBT templateを直接配置
- `place jigsaw`: poolとtargetを使ってjigsaw展開
- `place structure`: worldgen structureの開始処理を実行

各commandはvalidation範囲と副作用が異なります。template単体の成功だけで自然生成やstructure setの成功を証明しません。

## GameTestとの接続

1.21.5以降のdata-driven GameTestはstructure templateをtest空間として使います。

- test structureをworldgen structure folderへ置かない
- test instanceのstructure IDとNBT pathを一致させる
- template内のmarker、block entity、entityを対象versionで再保存する
- rotationごとの差をtest definitionで明示する

## バージョン境界

| バージョン | 主な境界 |
|---|---|
| 1.13 | namespaced structure NBT、`/place`以前の基準。旧templateは再保存が必要 |
| 1.16.2 | configured structure feature、template pool、processor等をデータ駆動化 |
| 1.18.2 | experimental structure／structure setとuniversal tag |
| 1.19 | `worldgen/structure`へ再編、`/place`追加 |
| 1.20 | jigsaw／processor拡張 |
| 1.21 | folderを単数形へ変更 |
| 1.21.5 | data-driven GameTestと`/place template ... strict` |
| 26.3-snapshot-1 | configured feature／material rule再編がstructure周辺worldgenへ波及 |

## 生成規則

- binary template、pool、processor、worldgen structure、structure setを別resourceとして扱う
- template NBTは対象versionで保存する
- pool、processor、structure参照の循環とmissing IDを検査する
- weight、size、spacing、separation、generation heightの値域を確認する
- 既生成chunkで自然生成の成否を判定しない
- template配置、jigsaw展開、自然生成、`/locate`を別々にtestする

## 検証

最初に`/place template`でNBTを確認し、次にpool／processorを使う`/place jigsaw`、最後に新規worldまたは未生成chunkでworldgen structure／structure setを確認します。`/locate`結果、bounding box、mob spawn、terrain adaptationも記録します。

## 出典

- 対象server JARのvanilla structure、template pool、processor、structure、structure set
- 各 [`../versions/<version>.md`](../versions/README.md) のworldgen差分
