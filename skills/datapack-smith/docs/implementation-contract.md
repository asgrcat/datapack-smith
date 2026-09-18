# 実装設計と受入条件

対象バージョンを解決した後、要件を「どの入口で、誰の状態を、何に変えるか」へ落とします。新規packでは下の表を短い設計メモとして残します。小さな変更では影響する行だけ更新し、調査依頼では実装fileを生成する必要はありません。

## 要件から参照先を選ぶ

| 利用者の要件 | 最初に決めること | 実装の入口・参照先 |
|---|---|---|
| playerが操作して能力を使う | 非OP入力、許容値、連打、cooldown | `/trigger`は[scoreboard](reference/scoreboards-and-results.md)、entity操作は[content hooks](content-hooks.md)、1.21.6以降のUIは[dialog](reference/dialogs-and-actions.md) |
| itemを使った・取引した・倒した | 正確なeventか定期観測か、誰が対象か | [advancement](advancements.md)。存在しないtrigger名を作らない |
| 独自item・recipe・報酬 | 新IDの登録か既存itemへのcomponent付与か | [items](json-parameters/items.md)、[loot/recipe](json-parameters/loot-recipes.md)。任意のblock/item typeやserializerをJSONだけで新設できるとは扱わない |
| 範囲・人数・タイマー | dimension、離脱者、オンライン時間かworld時間か | [複合要件](gameplay-requirements.md)、[実行モデル](execution-model.md)、[状態](state-management.md) |
| 地形・構造物 | 既存chunkへの配置か今後の生成か | [worldgen](reference/worldgen.md)、[structure](reference/structures-and-jigsaw.md)。新規world・未生成chunkを検証対象へ含める |
| 移行・複数バージョン | 入力と出力の完全ID、保存dataの互換性 | [compatibility](compatibility.md)、両方のprofile、変更するfamilyのreference |
| 読み込めない・動かない | 最初の失敗log、pack有効化、実行context | [診断手順](troubleshooting.md) |

## 実装前に決める契約

| 項目 | 記録する内容 | 欠けると起きる問題 |
|---|---|---|
| 対象 | exact version、vanilla/server種別、namespace、pack root | formatだけ同じ別リリースの構文を混ぜる |
| 受入条件 | 入力、観測する結果、期待値、確認時点 | 「動く」の意味が実装者と利用者で異なる |
| 入口 | load/tick/reward/API/schedule、executor、位置、dimension | serverの`@s`が空、別dimensionを検索 |
| 状態 | owner、型・単位、初期値、未設定、永続性、正本 | player間混線、reloadで進捗消失 |
| 遷移 | 前提、状態更新、副作用、失敗時の扱い | 同tick二重実行、報酬重複 |
| 外部依存 | pack名・対応version・namespace・公開function、順序 | 別packのIDを自packの参照切れと誤判定 |
| 運用 | 導入、reload、更新、reset、uninstall | 削除後もschedule・objective・tagが残る |
| 検証 | 要求level、実行コマンド、期待結果、残る未検証 | static成功をgameplay成功と誤認 |

namespaceは全resource種別を束ねる名前であり、`example:ready`というfunctionとpredicateは別resourceです。参照表は`種別 + ID → file/vanilla/外部pack`で作り、文字列が一致しただけで解決済みにしません。独自resourceは公式registry reportに載っていなくても、追加可能なresource種別で自packが定義していれば利用できます。

## 判断が分かれる場合

- バージョン未指定: 既存project、依頼、server設定の順に調べる。確定できなければ対象IDを確認し、その間は要件整理まで進める。`pack_format`を逆引きした1件を勝手に選ばない。
- projectと新しい依頼が不一致: 変更先が明示された移行依頼なら設定と成果物を一緒に更新する。意図が不明なら不一致を示し、黙って片方を無視しない。
- namespace・配置先未指定: 既存規約を使い、新規なら衝突しない値を選んで記録する。templateの`example`や対象versionをそのまま採用しない。
- 検証指定なし: 実行できるなら`static`を既定として記録する。Pythonがなければ手動のJSON・path・参照確認を記録し、CLIを実行したとは報告しない。
- playerの死亡・離脱・offline進行等: 要件を左右するものは確認する。それ以外は選んだ挙動を明示する。[完全例](worked-example.md)ではオンラインtickだけを減算する。
- 未確認のcodec: 対象versionの公式資料・既存生成物を調べる。不明fieldを推測しない。確認できた独立部分は進め、不明点と確認手段を限定して報告する。

## functionの契約例

```text
ID: example:api/activate
対象: 1.21.5
呼出元: execute as <player> at @s run function example:api/activate
入力: @sのexample.cooldown（tick単位、0のみ利用可能）
状態: @sのcooldownを100へ更新。共有holderへ書かない
result: 成功はreturn 1、前提不成立はreturn fail
副作用: 呼出playerに表示。消費item・他packの状態変更なし
再実行: cooldown中の呼出しは副作用なし
```

これはAPI設計の例です。実体のないfunctionを納品物から参照しません。`return run`などの構文は対象versionで利用できる場合に限ります。通常のruntime failureでfunction全体が自動停止するとは考えず、成否判定が必要なcommandは`execute store success`等で明示します。

## 報酬とqueueの保証

command列はtransactionではありません。scoreを先に配布済みにすると副作用の失敗時に欠配し、後に記録すると再試行時に重複し得ます。永続scoreだけで、server crashをまたぐ厳密なexactly-onceを保証しません。

通常のeventではevent generationとplayerごとの処理済みgenerationを使い、同一eventの再入を抑えます。失敗を許容しない報酬は「予約→実行→確認→完了」の状態を持ち、曖昧な失敗は管理者が照合できるよう残します。queueの先頭を消してから処理する例は自動再試行を持たず、削除後の失敗でeventを失います。再試行する場合はin-flight状態と重複時の処理を設計します。

## 変更・配布・受入

1. 必要なresourceと参照先を列挙し、load/tick tagを含めて生成する。説明用の省略記号や未定義functionを配布packへ残さない。
2. 既存packでは不要になった旧path・旧ID・旧scheduleも確認する。追加だけの移行で古い入口を二重登録しない。
3. [ハーネス](harness.md)で静的検査する。overlay、外部pack、macro、codec等の検証範囲を確認する。
4. server検証を実施する場合は対象IDの隔離worldで有効化、reload、入口を確認する。worldgenや保存形式変更は再起動と専用worldで確認する。
5. 要件ごとに入力と期待結果を照合する。対象0件、2人同時、reload、再参加などは関係するものだけ追加する。
6. 配布zipの直下に`pack.mcmeta`と`data/`を置く。project設定、cache、report、開発testはpack外へ置く。導入後のpack IDは`datapack list`で確認する。

納品時は[生成契約](ai-authoring.md)の報告形式を使い、変更file、実行コマンドと結果、warning、未実施testを示します。要求levelに届かない場合は未完了部分を具体的に残します。全fileの内容を会話へ再掲する必要はなく、実際に作成したfileへ案内します。
