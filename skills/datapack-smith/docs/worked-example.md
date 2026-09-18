# 完全例: player別の入力とcooldown

Java Edition **1.21.5専用**の小さなpackです。非OPのplayerが`/trigger sd.request set 1`で自分だけにparticleとメッセージを出し、100オンラインtickのcooldownを持ちます。生成物の正本は[同梱プロジェクト](../templates/examples/cooldown-1.21.5/datapack-project.json)です。文書内の断片を組み立てなくても全fileが揃っています。

この例の保証は静的検査までです。Minecraft serverでのreloadとplayer操作の機能testは別に実施し、下の受入表へ実測結果を残します。別のバージョンへ使う場合はprofile、folder、metadata、構文を変換します。

## 別の作業ディレクトリへコピーして検査する

以下は利用者repositoryのrootで実行します。`DATAPACK_SMITH_ROOT`には、このskillの`SKILL.md`がある実際の絶対pathを設定します。`demo-cooldown`は未作成の出力先です。

```bash
DATAPACK_SMITH_ROOT='/absolute/path/to/datapack-smith'
test ! -e demo-cooldown && cp -R "$DATAPACK_SMITH_ROOT/templates/examples/cooldown-1.21.5" demo-cooldown
python3 "$DATAPACK_SMITH_ROOT/tools/datapack_harness.py" project-check --project demo-cooldown/datapack-project.json
python3 "$DATAPACK_SMITH_ROOT/tools/datapack_harness.py" validate-project --project demo-cooldown/datapack-project.json
```

`project-check`と`validate-project`が終了code 0、completed levelが`static`なら静的検査成功です。reportを渡していないためcommand root・registry照合は未実施で、全引数・codec・runtimeも未保証というwarningが出ます。これはserver検証成功を意味しません。

## fileと参照の対応

```text
cooldown-1.21.5/
├── datapack-project.json
└── pack/
    ├── pack.mcmeta
    └── data/
        ├── minecraft/tags/function/
        │   ├── load.json
        │   └── tick.json
        └── smith_demo/function/
            ├── load.mcfunction
            ├── tick.mcfunction
            ├── tick_ready.mcfunction
            ├── player/
            │   ├── tick.mcfunction
            │   └── activate.mcfunction
            └── admin/
                ├── reset_player.mcfunction
                └── uninstall.mcfunction
```

| 入口・file | contextと役割 |
|---|---|
| [pack.mcmeta](../templates/examples/cooldown-1.21.5/pack/pack.mcmeta) | format 71、説明。配布packのroot |
| [load tag](../templates/examples/cooldown-1.21.5/pack/data/minecraft/tags/function/load.json) → [load](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/load.mcfunction) | server context。objective作成、未設定schemaだけ初期化、未知schemaは稼働させない |
| [tick tag](../templates/examples/cooldown-1.21.5/pack/data/minecraft/tags/function/tick.json) → [tick](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/tick.mcfunction) | readyのときだけdispatcherを呼ぶ |
| [tick_ready](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/tick_ready.mcfunction) | player scoreの欠落初期化→減算→player別処理の順 |
| [player/tick](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/player/tick.mcfunction) | `as @a at @s`のため、各playerがexecutor・位置・dimensionの基準 |
| [player/activate](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/player/activate.mcfunction) | 内部入口。cooldownを先に100へ設定してから自分へ表示 |
| [admin/reset_player](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/admin/reset_player.mcfunction) | player executor必須。対象1人の状態をreset。成功はresult 1、前提不成立はfail |
| [admin/uninstall](../templates/examples/cooldown-1.21.5/pack/data/smith_demo/function/admin/uninstall.mcfunction) | 管理者が明示実行。自packの3 objectiveを全holder分削除 |

## 状態と時間の契約

| objective / holder | 型・寿命 | 意味 |
|---|---|---|
| `sd.meta` / `#schema` | dummy整数、world永続 | 1のみ実行可能。未知の新schemaを巻き戻さない |
| `sd.meta` / `#ready` | dummy整数、loadで再計算 | 1なら稼働。uninstall後は未設定となりtick入口は閉じる |
| `sd.cooldown` / player | dummy整数、player別永続 | 残りオンラインgame tick。未設定だけ0、正なら1減算 |
| `sd.request` / player | trigger整数、一時入力 | 1だけ受理。各tickの処理後0へ戻し再enable |

100tickは20 TPS時に5秒です。offlineとserver停止中は減算せず、低TPSでは実時間が長くなります。死亡・dimension移動ではresetしません。reloadもcooldownを保持します。入力は次にそのplayerを処理するtickで判定するため、処理前に切断した要求は復帰時に評価され得ます。

tick内では減算が先なので、1→0になったtickから次の要求を受理できます。cooldown中の要求や1以外の入力は消費して捨て、後で自動実行しません。playerが複数いても他人のcooldownを参照しません。共有stateはschemaとreadyだけです。

## 導入・削除

複製した1.21.5の検証worldの`datapacks/smith_demo/`へ`pack/`の**中身**を配置し、`/reload`を実行します。`/datapack list enabled`で有効化を確認し、logの`SMITH_DEMO_LOAD_OK`を確認します。markerはloadが到達した証拠であり、player処理の機能保証ではありません。

非OP playerの入力:

```text
/trigger sd.request set 1
```

管理者が自分だけresetする場合:

```text
/execute as @s at @s run function smith_demo:admin/reset_player
```

consoleからなら`@s`を対象player名に置き換えます。削除時は`/function smith_demo:admin/uninstall`後に実際のpack IDを`/datapack list enabled`で確認して無効化・削除します。packが残ったままreloadすると再インストールされます。objective削除はoffline playerのscoreも含み、取り消し機能はありません。他packの状態、effect、advancementは変更しません。

## 機能testの受入表

以下は**未実行の手順と期待値**です。対象serverで実行した行にだけ結果とlogを記録します。tickを正確に調べる場合は1.21.5の`/tick freeze`と`/tick step`を使用し、最後に`/tick unfreeze`へ戻します。

| 入力・前提 | 観測する期待値 |
|---|---|
| player 0人、loadを2回 | 入口errorなし、schema=1、ready=1。既存objective追加の失敗feedbackは想定内 |
| 新playerで初回tick後にtrigger 1 | 自分だけ表示、cooldown=100（処理tick末尾） |
| 次の99オンラインtick | cooldown=1。追加要求は発動しない |
| 100tick経過後にtrigger 1 | 再度発動。cooldown=100 |
| triggerを0・負数・2以上に設定 | 発動せず入力が0へ戻り、次回入力可能 |
| 2人が同時にtrigger 1 | 各人に1回、各scoreが100。互いの値に影響しない |
| cooldown途中でreload | 値を0へ戻さず、次のtickから減算継続 |
| 切断・再接続、server再起動 | 保存値を保持。停止・offline時間だけでは減算しない |
| 別dimensionへ移動して発動 | 移動先の本人位置に表示 |
| schemaを2へ変更してreload（検証worldのみ） | schema=2のまま、ready=0、発動なし。schemaを1に復元してreloadすると再開 |
| 1人だけreset | その人だけcooldown=0、他人は保持 |
| uninstall後にtick、その後packを無効化 | 3 objectiveがなく、処理・表示・scheduleが残らない |

Minecraft実行環境がない場合はこの表を未実施として渡します。[設計ガイド](implementation-contract.md)の契約を利用者の要件へ変え、全packへこの例の仕様を押し付けないでください。
