from flask import Flask, request, render_template
import requests
import pandas as pd
from tqdm import tqdm

app = Flask(__name__)
error_message = ""


@app.route("/")
def index():
    global error_message
    error_message = ""
    return render_template("index.html", error_message=error_message)


@app.route("/", methods=["POST"])
def submit():
    APIkeys = pd.read_csv("api_keys.csv", header=None).values.tolist()
    input_text = request.form["input_text"]
    if input_text == "":
        global error_message
        error_message = "テキストを入力してから送信してください"
        return render_template("index.html", error_message=error_message)

    # 形態素のsetを作成
    morpheme_set = set()
    morphemeAPIep = "https://labs.goo.ne.jp/api/morph"
    data = {
        "app_id": APIkeys[0],
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
    # 連続部分文字列を1文字のもの以外全て抽出
    subStrings = []
    for i in range(len(hiragana_text)):
        for j in range(i + 2, len(hiragana_text) + 1):
            subStrings.append(hiragana_text[i:j])
    subStrings = list(set(subStrings))
    subStrings.sort(key=len, reverse=True)
    subStrings.pop(0)
    row_subStrings = subStrings.copy()

    # 変換API
    transliterateAPIep = "http://www.google.com/transliterate"
    for i in tqdm(range(len(subStrings))):
        subStrings[i] = requests.get(
            transliterateAPIep, params={"langpair": "ja-Hira|ja", "text": subStrings[i]}
        )
        subStrings[i] = subStrings[i].text.split("\t")[0]
        subStrings[i] = subStrings[i].split(",")[1].split('"')[1]

    # Wikipediaに存在する語であるかの判定
    exist_wikipedia = []
    strings = ""
    for i in range(len(subStrings) - 1):
        strings += subStrings[i] + "|"
    strings += subStrings[len(subStrings) - 1]
    base_url = "https://ja.wikipedia.org/w/api.php"
    params = {"action": "query", "format": "json", "prop": "info", "titles": strings}
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
        "result.html",
        input_text=input_text,
        output_text=hiragana_text,
        morpheme_list=morpheme_list,
        row_subStrings=row_subStrings,
        subStrings=subStrings,
        result=result,
    )


if __name__ == "__main__":
    app.run(debug=True)
