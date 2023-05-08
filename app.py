from flask import Flask, request, render_template
import requests
import pandas as pd
import sqlite3

app = Flask(__name__)
error_message = ""

@app.route("/")
def index():
    global error_message
    error_message = ""
    return render_template("index.html", error_message=error_message)


@app.route("/", methods=["POST"])
def submit():
    conn = sqlite3.connect("wnjpn.db")
    APIkeys =  pd.read_csv("api_keys.csv", header=None).values.tolist()
    input_text = request.form["input_text"]
    if input_text == "":
        global error_message
        error_message = "テキストを入力してから送信してください"
        return render_template("index.html", error_message=error_message)

    # ひらがな変換API
    hiraganaAPIep = "https://labs.goo.ne.jp/api/hiragana"
    data = {
        "app_id": APIkeys[0],
        "request_id": "request",
        "sentence": input_text,
        "output_type": "hiragana",
    }
    hiragana_res = requests.post(hiraganaAPIep, data=data)
    hiragana_text = hiragana_res.json()["converted"]
    hiragana_text = hiragana_text.replace(" ", "")
    # サブストリングを1文字のもの以外全て抽出
    subStrings = []
    for i in range(len(hiragana_text)):
        for j in range(i + 3, len(hiragana_text) + 1):
            subStrings.append(hiragana_text[i:j])
    subStrings = list(set(subStrings))
    subStrings.sort(key=len, reverse=True)

    #変換API
    transliterateAPIep = "http://www.google.com/transliterate"

    # Wordnetで存在する語であるかの判定
    result = []
    for i in range(len(subStrings)):
        subStrings[i] = requests.get(transliterateAPIep, params={"langpair": "ja-Hira|ja", "text": subStrings[i]})
        subStrings[i] = subStrings[i].text.split("\t")[0]
        subStrings[i] = subStrings[i].split(",")[1].split("\"")[1]
        cur = conn.execute("select wordid from word where lemma='%s'" % subStrings[i])
        word_id = -1
        for row in cur:
            word_id = row[0]
        if word_id != -1:
            result.append(subStrings[i])
    conn.close()
    # 重複を削除
    result = list(set(result))
    result.sort(key=len, reverse=True)
    return render_template(
        "result.html",
        input_text=input_text,
        output_text=hiragana_text,
        subStrings=subStrings,
        result=result
    )


if __name__ == "__main__":
    app.run(debug=True)
