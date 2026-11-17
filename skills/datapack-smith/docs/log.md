# Knowledge更新履歴

## 2026-11-18

- **追加**: [26.4 Snapshot 9](snapshots/26.4-snapshot-9.md)（format 128.0）と[Dispenser behavior](reference/dispense-behaviors.md)を収録。公式JARの生成物・codecを照合。
- **更新**: 2D local座標、文字列引数report、particle field、entity_data、honeycomb transformerとslot sourceの修正を各referenceへ反映。
- **検証範囲**: 2D parserとbehaviorのlist codecをserver起動なしで確認。server reload／ゲーム内動作と、取得できなかったMinecraft Wikiの照合は未実施。

## 2026-11-17

- **移行**: 既存の日本語仕様資料125 conceptをOKF v0.2へ移行し、metadataと各階層の[index.md](index.md)を整備。
- **整理**: 案内文書を`guide.md`、正式／開発バージョンの対応表を`catalog.md`へ改名し、[スキルの参照手順](ai-authoring.md)を更新。
- **改善**: 取り込み漏れの出典と内部出典・生成物の参照範囲を`sources`へ記録し、本文の出典参照を安定したIDの脚注へ変更。ゲーム内挙動を新たに検証した記録ではない。
- **検査**: [OKF運用規約](okf.md)の検査を、必須要件への適合とこのbundleの保守規約に分離。予約ファイル、出典ID、脚注、任意の信頼・鮮度metadataも検査。
