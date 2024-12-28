import streamlit as st
import requests
import os
from dotenv import load_dotenv

# カタカナからひらがなへの変換テーブル
KATAKANA_TO_HIRAGANA_TABLE = {
    "ア": "あ", "イ": "い", "ウ": "う", "エ": "え", "オ": "お",
    "カ": "か", "キ": "き", "ク": "く", "ケ": "け", "コ": "こ",
    "サ": "さ", "シ": "し", "ス": "す", "セ": "せ", "ソ": "そ",
    "タ": "た", "チ": "ち", "ツ": "つ", "テ": "て", "ト": "と",
    "ナ": "な", "ニ": "に", "ヌ": "ぬ", "ネ": "ね", "ノ": "の",
    "ハ": "は", "ヒ": "ひ", "フ": "ふ", "ヘ": "へ", "ホ": "ほ",
    "マ": "ま", "ミ": "み", "ム": "む", "メ": "め", "モ": "も",
    "ヤ": "や", "ユ": "ゆ", "ヨ": "よ",
    "ラ": "ら", "リ": "り", "ル": "る", "レ": "れ", "ロ": "ろ",
    "ワ": "わ", "ヲ": "を", "ン": "ん",
    "ガ": "が", "ギ": "ぎ", "グ": "ぐ", "ゲ": "げ", "ゴ": "ご",
    "ザ": "ざ", "ジ": "じ", "ズ": "ず", "ゼ": "ぜ", "ゾ": "ぞ",
    "ダ": "だ", "ヂ": "ぢ", "ヅ": "づ", "デ": "で", "ド": "ど",
    "バ": "ば", "ビ": "び", "ブ": "ぶ", "ベ": "べ", "ボ": "ぼ",
    "パ": "ぱ", "ピ": "ぴ", "プ": "ぷ", "ペ": "ぺ", "ポ": "ぽ",
    "ヴ": "ゔ",
    "ヷ": "わ", "ヸ": "ゐ", "ヹ": "ゑ", "ヺ": "を",
    "ァ": "ぁ", "ィ": "ぃ", "ゥ": "ぅ", "ェ": "ぇ", "ォ": "ぉ",
    "ャ": "ゃ", "ュ": "ゅ", "ョ": "ょ", "ッ": "っ",
}

LIMITHIRAGANA = 15


def katakana_to_hiragana(katakana_text: str) -> str:
    """カタカナ文字列をひらがな文字列に変換する"""
    return "".join(KATAKANA_TO_HIRAGANA_TABLE.get(char, char) for char in katakana_text)


def parse_text_to_morphemes(query: str, api_key: str) -> set[str]:
    """Yahoo APIで形態素解析を実行"""
    url = "https://jlp.yahooapis.jp/MAService/V2/parse"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Yahoo AppID: {api_key}",
    }
    params = {
        "id": "toufu",
        "jsonrpc": "2.0",
        "method": "jlp.maservice.parse",
        "params": {"q": query},
    }
    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()
    return {token[0] for token in response.json()["result"]["tokens"]}


def convert_text_to_hiragana(query: str, api_key: str) -> str:
    """Yahoo APIでひらがな変換を実行"""
    url = "https://jlp.yahooapis.jp/FuriganaService/V2/furigana"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Yahoo AppID: {api_key}",
    }
    params = {
        "id": "toufu",
        "jsonrpc": "2.0",
        "method": "jlp.furiganaservice.furigana",
        "params": {"q": query, "grade": 1},
    }
    response = requests.post(url, headers=headers, json=params)
    response.raise_for_status()

    word_list = response.json()["result"]["word"]
    return "".join(word.get("furigana", word["surface"]) for word in word_list)


def get_substrings(text: str) -> list[str]:
    """文字列の部分文字列を取得"""
    substrings = {
        text[i:j] for i in range(len(text)) for j in range(i + 2, len(text) + 1)
    }
    return sorted(substrings, key=len, reverse=True)


def transliterate_substrings(substrings: list[str], api_key: str) -> set[str]:
    """Yahoo APIで部分文字列を日本語変換"""
    url = "https://jlp.yahooapis.jp/JIMService/V2/conversion"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"Yahoo AppID: {api_key}",
    }
    transliterated: set = set()

    for i in range(0, len(substrings), 10):
        batch = " ".join(substrings[i : i + 10])
        params = {
            "id": "toufu",
            "jsonrpc": "2.0",
            "method": "jlp.jimservice.conversion",
            "params": {"q": batch, "results": 1},
        }
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        transliterated.update(
            candidate
            for segment in response.json()["result"]["segment"]
            for candidate in segment["candidate"]
        )

    return transliterated


def filter_existing_words(words: list[str]) -> list[str]:
    """MediaWiki APIを利用して存在する単語のみを抽出"""
    url = "https://ja.wikipedia.org/w/api.php"
    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": "word-finder(https://substring-word-finder.onrender.com/)",
    }
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "titles": "|".join(words),
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    pages = response.json()["query"]["pages"]
    return [page["title"] for page in pages.values() if page.get("missing") is None]


def main():
    # .envファイルを読み込む
    load_dotenv()

    st.title("「○○の△△の部分」の○○を入力すると△△を出力します")
    st.markdown(
        '<a href="https://github.com/toufu-24/Substring-Word-Finder" target="_blank">GitHubリポジトリ</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
    <div style='text-align: right; margin-top: 50px;'>
        <span style='margin:15px;'><a href="https://developer.yahoo.co.jp/sitemap/">Webサービス by Yahoo! JAPAN</a></span><br>
        <a href="https://www.mediawiki.org/wiki/API:Main_page/ja">Powered by MediaWiki</a>
    </div>
    """,
        unsafe_allow_html=True,
    )

    input_text = st.text_input("テキストを入力してください")
    if not input_text:
        st.write("テキストを入力してから送信してください")
        return

    if len(input_text) > LIMITHIRAGANA:
        st.write(f"{LIMITHIRAGANA}文字以下にしてください")
        return

    api_key = os.getenv("YahooAPIkey")
    if not api_key:
        st.write("Yahoo APIキーが設定されていません")
        return

    # 形態素解析
    morphemes: set[str] = parse_text_to_morphemes(input_text, api_key)

    # ひらがな変換
    hiragana_text: str = katakana_to_hiragana(
        convert_text_to_hiragana(input_text, api_key)
    )

    # ひらがな文字列の長さ制限
    if len(hiragana_text) > LIMITHIRAGANA:
        st.write(f"ひらがなで{LIMITHIRAGANA}文字以下にしてください")
        return
    if len(hiragana_text) < 3:
        st.write("ひらがなで3文字以上にしてください")
        return

    # 部分文字列取得
    substrings: list[str] = get_substrings(hiragana_text)

    # 日本語変換
    transliterated: set[str] = transliterate_substrings(substrings, api_key)

    # Wikipediaで存在する単語をフィルタリング
    existing_words: list[str] = filter_existing_words(transliterated)

    # 形態素解析での単語を除外
    result: list[str] = [word for word in existing_words if word not in morphemes]

    # 結果のソート
    result.sort(key=len, reverse=True)

    # 結果の表示
    st.write(result)
    if st.button("詳細を表示"):
        st.write("入力テキスト:", input_text)
        st.write("ひらがなテキスト:", hiragana_text)
        st.write("形態素リスト:")
        st.write(morphemes)
        st.write("result候補:")
        st.write(transliterated)


if __name__ == "__main__":
    main()
