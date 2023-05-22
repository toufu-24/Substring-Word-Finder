from flask import Flask, request, render_template
import requests
import json
from urllib import request as req
import os

LIMITHIRAGANA = 15
app = Flask(__name__)
message = ""

katakana_to_hiragana_table = {
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


@app.route("/")
def index():
    global message
    message = ""
    return render_template("index.html", error_message=message)


@app.route("/", methods=["POST"])
def submit():
    global message
    input_text = request.form["input_text"]
    if input_text == "":
        message = "テキストを入力してから送信してください"
        return render_template("index.html", error_message=message)
    APIkeys = os.getenv("YahooAPIkey")
    # 形態素のsetを作成
    morpheme_set = set()
    YahooAPIkey = APIkeys

    def parse_post(query):
        morphemeAPIep = "https://jlp.yahooapis.jp/MAService/V2/parse"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Yahoo AppID: {}".format(YahooAPIkey),
        }
        param_dic = {
            "id": "toufu",
            "jsonrpc": "2.0",
            "method": "jlp.maservice.parse",
            "params": {"q": query},
        }
        params = json.dumps(param_dic).encode()
        requ = req.Request(morphemeAPIep, params, headers)
        with req.urlopen(requ) as res:
            body = res.read()
        return body.decode()

    morpheme_res = parse_post(input_text)
    # 形態素の配列
    morpheme_res = json.loads(morpheme_res)["result"]["tokens"]
    morpheme_list = [morpheme[0] for morpheme in morpheme_res]
    for i in range(len(morpheme_list)):
        morpheme_set.add(morpheme_list[i])

    # ひらがな変換API
    def post(query):
        hiraganaAPIep = "https://jlp.yahooapis.jp/FuriganaService/V2/furigana"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Yahoo AppID: {}".format(YahooAPIkey),
        }
        param_dic = {
            "id": "1234-1",
            "jsonrpc": "2.0",
            "method": "jlp.furiganaservice.furigana",
            "params": {"q": query, "grade": 1},
        }
        params = json.dumps(param_dic).encode()
        requ = req.Request(hiraganaAPIep, params, headers)
        with req.urlopen(requ) as res:
            body = res.read()
        return body.decode()

    response = post(input_text)
    parsed_data = json.loads(response)
    word = parsed_data["result"]["word"]
    hiragana_text = ""
    for w in word:
        if "furigana" in w:
            hiragana_text += w["furigana"]
        else:
            hiragana_text += w["surface"]

    def katakana_to_hiragana(katakana_text):
        hiragana_text = ""
        for char in katakana_text:
            if char in katakana_to_hiragana_table:
                hiragana_text += katakana_to_hiragana_table[char]
            else:
                hiragana_text += char
        return hiragana_text

    hiragana_text = katakana_to_hiragana(hiragana_text)

    if len(hiragana_text) >= LIMITHIRAGANA:
        message = "ひらがなで" + LIMITHIRAGANA + "文字以下してください"
        return render_template("index.html", error_message=message)
    elif len(hiragana_text) <= 2:
        message = "ひらがなで3文字以上にしてください"
        return render_template("index.html", error_message=message)

    # 連続部分文字列を1文字のもの以外全て抽出
    subStrings = []
    for i in range(len(hiragana_text)):
        for j in range(i + 2, len(hiragana_text) + 1):
            subStrings.append(hiragana_text[i:j])
    subStrings = list(set(subStrings))
    subStrings.sort(key=len, reverse=True)
    subStrings.pop(0)
    row_subStrings = subStrings.copy()

    # 日本語変換API
    def conversion_post(query):
        APPID = APIkeys
        URL = "https://jlp.yahooapis.jp/JIMService/V2/conversion"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Yahoo AppID: {}".format(APPID),
        }
        param_dic = {
            "id": "toufu",
            "jsonrpc": "2.0",
            "method": "jlp.jimservice.conversion",
            "params": {"q": query, "results": 1},
        }
        params = json.dumps(param_dic).encode()
        requ = req.Request(URL, params, headers)
        with req.urlopen(requ) as res:
            body = res.read()
        return body.decode()

    length_watcher = True
    transliterated_subStrings = []
    i = 0
    while length_watcher:
        string = ""
        for j in range(i, len(subStrings)):
            if len(string + subStrings[j]) >= 70:
                j -= 1
                break
            string += subStrings[j] + " "
        if j == len(subStrings) - 1:
            length_watcher = False
        i = j + 1
        post_res = conversion_post(string)
        parsed_data = json.loads(post_res)
        segment = parsed_data["result"]["segment"]
        for s in segment:
            transliterated_subStrings.extend(s["candidate"])
    # 重複を削除
    transliterated_subStrings = list(set(transliterated_subStrings))
    transliterated_subStrings.sort(key=len, reverse=True)

    # Wikipediaに存在する語であるかの判定
    exist_wikipedia = []
    wikipedia_input_str = ""
    for i in range(len(transliterated_subStrings) - 1):
        wikipedia_input_str += transliterated_subStrings[i] + "|"
    wikipedia_input_str += transliterated_subStrings[len(transliterated_subStrings) - 1]

    headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": "word-finder(https://toufu.pythonanywhere.com)",
    }
    base_url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "titles": wikipedia_input_str,
    }
    WikiResponse = requests.get(base_url, headers=headers, params=params)
    data = WikiResponse.json()
    pages = data["query"]["pages"]
    for page in pages.values():
        if page.get("missing") is None:
            exist_wikipedia.append(page["title"])

    # 重複を削除
    result = list(set(exist_wikipedia))
    result.sort(key=len, reverse=True)
    # 形態素解析で抽出した語を削除
    for i in range(len(result)):
        if result[i] in morpheme_set:
            result[i] = ""
    result = [x for x in result if x != ""]
    return render_template(
        "index.html",
        input_text=input_text,
        output_text=hiragana_text,
        morpheme_list=morpheme_list,
        row_subStrings=row_subStrings,
        subStrings=transliterated_subStrings,
        result=result,
    )


if __name__ == "__main__":
    app.run(debug=True)
