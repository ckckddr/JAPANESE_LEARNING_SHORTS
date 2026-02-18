"""
여행업 B2B/B2C 상황 생성 모듈
중복 방지를 위해 히스토리 파일에 사용된 상황을 기록합니다.
"""
import json
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import HISTORY_FILE

# ── 여행업 상황 풀 ─────────────────────────────────────────
B2B_SITUATIONS = [
    {"situation": "ホテルの団体予約と料金交渉", "channel": "電話", "difficulty": "N1"},
    {"situation": "航空会社との座席ブロック契約更新", "channel": "対面会議", "difficulty": "N1"},
    {"situation": "旅行代理店への新パッケージ商品提案", "channel": "プレゼン", "difficulty": "N1"},
    {"situation": "ホテルのオーバーブッキング対応と代替手配", "channel": "電話", "difficulty": "N1"},
    {"situation": "バス会社との長期契約条件交渉", "channel": "メール", "difficulty": "N2"},
    {"situation": "現地ランドオペレーターとの精算・クレーム処理", "channel": "電話", "difficulty": "N1"},
    {"situation": "旅行保険会社との提携条件確認", "channel": "対面", "difficulty": "N2"},
    {"situation": "レストランの団体食事予約とメニュー調整", "channel": "電話", "difficulty": "N2"},
    {"situation": "観光バス会社への緊急手配依頼", "channel": "電話", "difficulty": "N2"},
    {"situation": "ホテルとの年間契約書の内容確認と修正依頼", "channel": "メール", "difficulty": "N1"},
    {"situation": "航空券の団体割引条件の問い合わせ", "channel": "電話", "difficulty": "N2"},
    {"situation": "現地ガイド会社との品質改善ミーティング", "channel": "対面", "difficulty": "N1"},
    {"situation": "旅行代理店向けインセンティブ制度の説明", "channel": "プレゼン", "difficulty": "N1"},
    {"situation": "クルーズ会社との団体乗船手続き確認", "channel": "メール", "difficulty": "N2"},
    {"situation": "免税店との送客手数料交渉", "channel": "対面", "difficulty": "N1"},
    {"situation": "ホテルのアーリーチェックイン・レイトチェックアウト交渉", "channel": "電話", "difficulty": "N2"},
    {"situation": "旅行代理店への緊急キャンセル通知と代替案提示", "channel": "電話", "difficulty": "N1"},
    {"situation": "現地送迎会社との新路線開拓ミーティング", "channel": "対面", "difficulty": "N2"},
    {"situation": "ホテルとの特別食（アレルギー対応）事前確認", "channel": "メール", "difficulty": "N2"},
    {"situation": "航空会社との遅延補償交渉", "channel": "電話", "difficulty": "N1"},
    {"situation": "旅行代理店向け新商品の価格設定説明", "channel": "メール", "difficulty": "N2"},
    {"situation": "現地体験アクティビティ会社との契約締結", "channel": "対面", "difficulty": "N1"},
    {"situation": "ホテルの会議室・宴会場の予約と設備確認", "channel": "電話", "difficulty": "N2"},
    {"situation": "旅行代理店との販売目標達成に向けた戦略会議", "channel": "対面", "difficulty": "N1"},
    {"situation": "現地病院との緊急対応マニュアル確認", "channel": "メール", "difficulty": "N1"},
]

B2C_SITUATIONS = [
    {"situation": "新婚旅行パッケージの相談と提案", "channel": "対面", "difficulty": "N2"},
    {"situation": "家族旅行の日程変更とキャンセル料の説明", "channel": "電話", "difficulty": "N2"},
    {"situation": "海外旅行保険の加入案内", "channel": "対面", "difficulty": "N2"},
    {"situation": "ビザ申請手続きの説明と必要書類案内", "channel": "対面", "difficulty": "N2"},
    {"situation": "航空券の座席アップグレード案内", "channel": "電話", "difficulty": "N2"},
    {"situation": "旅行中のトラブル（パスポート紛失）対応", "channel": "電話", "difficulty": "N1"},
    {"situation": "ホテルの部屋タイプ変更リクエスト対応", "channel": "電話", "difficulty": "N2"},
    {"situation": "シニア向け旅行パッケージの説明", "channel": "対面", "difficulty": "N2"},
    {"situation": "旅行後のクレーム（サービス不満）対応", "channel": "電話", "difficulty": "N1"},
    {"situation": "団体旅行の幹事への旅程説明", "channel": "対面", "difficulty": "N2"},
    {"situation": "子連れ旅行の注意事項と特別サービス案内", "channel": "対面", "difficulty": "N2"},
    {"situation": "旅行キャンセル保険の適用条件説明", "channel": "電話", "difficulty": "N1"},
    {"situation": "現地での緊急医療サポートの説明", "channel": "対面", "difficulty": "N1"},
    {"situation": "ハネムーナー向け特別演出リクエスト対応", "channel": "メール", "difficulty": "N2"},
    {"situation": "旅行代金の分割払い・ローン案内", "channel": "対面", "difficulty": "N2"},
    {"situation": "出発前の最終確認と持ち物チェック案内", "channel": "電話", "difficulty": "N2"},
    {"situation": "旅行中の現地緊急連絡先と対応手順説明", "channel": "対面", "difficulty": "N2"},
    {"situation": "帰国後の旅行満足度調査と次回提案", "channel": "電話", "difficulty": "N2"},
    {"situation": "障害者・高齢者向けバリアフリー旅行の相談", "channel": "対面", "difficulty": "N1"},
    {"situation": "個人旅行と団体旅行の違いと選択アドバイス", "channel": "対面", "difficulty": "N2"},
    {"situation": "旅行中の食物アレルギー対応の事前確認", "channel": "メール", "difficulty": "N2"},
    {"situation": "格安航空券と正規航空券の違いの説明", "channel": "対面", "difficulty": "N2"},
    {"situation": "旅行積立プランの案内と申し込み手続き", "channel": "対面", "difficulty": "N2"},
    {"situation": "現地ツアーのオプション追加と料金説明", "channel": "電話", "difficulty": "N2"},
    {"situation": "旅行中の盗難・事故時の保険請求手続き説明", "channel": "電話", "difficulty": "N1"},
]


def _load_history() -> list:
    """사용된 상황 히스토리 로드"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(situations: list):
    """사용된 상황을 히스토리에 추가"""
    history = _load_history()
    for s in situations:
        key = f"{s['type']}:{s['situation']}"
        if key not in history:
            history.append(key)
    # 히스토리가 너무 길면 오래된 것 제거 (전체 풀의 80% 이상이면 리셋)
    max_history = int((len(B2B_SITUATIONS) + len(B2C_SITUATIONS)) * 0.8)
    if len(history) > max_history:
        history = history[len(history) - max_history // 2:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def generate_situations() -> list:
    """
    B2B 1개 + B2C 1개 상황 선택 (히스토리 기반 중복 방지)
    반환: [{"type": "B2B", "situation": ..., "channel": ..., "difficulty": ...}, ...]
    """
    history = _load_history()

    def pick(pool, ep_type):
        used_keys = {h.split(":", 1)[1] for h in history if h.startswith(f"{ep_type}:")}
        available = [s for s in pool if s["situation"] not in used_keys]
        if not available:
            # 모두 사용했으면 전체에서 랜덤 선택
            available = pool
        chosen = random.choice(available)
        return {**chosen, "type": ep_type}

    b2b = pick(B2B_SITUATIONS, "B2B")
    b2c = pick(B2C_SITUATIONS, "B2C")
    return [b2b, b2c]


if __name__ == "__main__":
    situations = generate_situations()
    for s in situations:
        print(f"[{s['type']}] {s['situation']} / {s['channel']} / {s['difficulty']}")
