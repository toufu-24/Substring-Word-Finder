from flask import Flask, request, render_template
import requests
import pandas as pd
import sqlite3

conn = sqlite3.connect("wnjpn.db")
app = Flask(__name__)
error_message = ""

@app.route("/")
def index():
    global error_message
    error_message = ""
    return render_template("index.html", error_message=error_message)


@app.route("/", methods=["POST"])
def submit():
    APIkeys =  pd.read_csv("api_keys.csv", header=None).values.tolist()
    hiraganaAPIep = "https://labs.goo.ne.jp/api/hiragana"
    input_text = request.form["input_text"]
    if input_text == "":
        global error_message
        error_message = "テキストを入力してから送信してください"
        return render_template("index.html", error_message=error_message)

    # ひらがな変換API
    data = {
        "app_id": APIkeys[0],
        "request_id": "request",
        "sentence": input_text,
        "output_type": "hiragana",
    }
    res = requests.post(hiraganaAPIep, data=data)
    output_text = res.json()["converted"]
    output_text = output_text.replace(" ", "")
    # サブストリングを1-2文字のもの以外全て抽出
    subStrings = []
    for i in range(len(output_text)):
        for j in range(i + 3, len(output_text) + 1):
            subStrings.append(output_text[i:j])
    subStrings = list(set(subStrings))
    subStrings.sort(key=len, reverse=True)

    # Wordnetに存在する語であるかの判定
    cur = conn.execute("select wordid from word where lemma='%s'" % output_text)
    word_id = -1
    for row in cur:
        word_id = row[0]
    if word_id == -1:
        print("「%s」は、Wordnetに存在しない単語です。" % output_text)
    return render_template(
        "result.html",
        input_text=input_text,
        output_text=output_text,
        subStrings=subStrings,
    )


if __name__ == "__main__":
    app.run(debug=True)
