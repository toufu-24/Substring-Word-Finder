from flask import Flask, request, render_template
import requests
import pandas as pd
from tqdm import tqdm
import json
from urllib import request as req

LIMITHIRAGANA = 15
app = Flask(__name__)
message = ""


@app.route("/")
def index():
    global message
    message = ""
    return render_template("index.html", error_message=message)


@app.route("/", methods=["POST"])
def submit():
    global message
    APIkeys = pd.read_csv("api_keys.csv", header=None).values.tolist()
    input_text = request.form["input_text"]
    if input_text == "":
        message = "テキストを入力してから送信してください"
        return render_template("index.html", error_message=message)
    # 形態素のsetを作成
    morpheme_set = set()
    morphemeAPIep = "https://labs.goo.ne.jp/api/morph"
    data = {
        "app_id": APIkeys[0][0],
        "sentence": input_text,
    }
    morpheme_res = requests.post(morphemeAPIep, data=data)
    morpheme_res = morpheme_res.json()["word_list"]
    for i in range(len(morpheme_res)):
        for j in range(len(morpheme_res[i])):
            morpheme_set.add(morpheme_res[i][j][0])
    # 形態素の配列
    morpheme_list = []
    for i in range(len(morpheme_res)):
        for j in range(len(morpheme_res[i])):
            morpheme_list.append(morpheme_res[i][j][0])

    # ひらがな変換API
    hiraganaAPIep = "https://labs.goo.ne.jp/api/hiragana"
    data = {
        "app_id": APIkeys[0],
        "request_id": "hiragana",
        "sentence": input_text,
        "output_type": "hiragana",
    }
    hiragana_res = requests.post(hiraganaAPIep, data=data)
    hiragana_text = hiragana_res.json()["converted"]
    hiragana_text = hiragana_text.replace(" ", "")

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
    def post(query):
        Apikeys = pd.read_csv("api_keys.csv", header=None).values.tolist()
        APPID = Apikeys[1][0]
        URL = "https://jlp.yahooapis.jp/JIMService/V2/conversion"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Yahoo AppID: {}".format(APPID),
        }
        param_dic = {
            "id": "1234-1",
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
        post_res = post(string)
        parsed_data = json.loads(post_res)
        segment = parsed_data["result"]["segment"]
        for s in segment:
            transliterated_subStrings.extend(s["candidate"])

    # Wikipediaに存在する語であるかの判定
    exist_wikipedia = []
    wikipedia_input_str = ""
    for i in range(len(transliterated_subStrings) - 1):
        wikipedia_input_str += transliterated_subStrings[i] + "|"
    wikipedia_input_str += transliterated_subStrings[len(transliterated_subStrings) - 1]

    base_url = "https://ja.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "titles": wikipedia_input_str,
    }
    WikiResponse = requests.get(base_url, params=params)
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
