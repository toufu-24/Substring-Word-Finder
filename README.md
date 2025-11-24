# 部分文字列の単語判定
このURLで使用することが出来ます.  
https://substring-word-finder.toufu24.dev


# 概要
部分文字列をとり，それが単語として存在するかどうかを判定します．

# 実行方法
.envファイルを作成し，以下のように記述してください．
```
YahooAPIkey=<あなたのYahooAPIkey>
```
その後，以下のコマンドを実行してください．
```
streamlit run src/substring_word_finder/main.py
```

# 実装方法
[記事](https://qiita.com/toufu24/items/e521341f182ee6a4c792)にある程度書きました
streamlitを用いて実装しています．  
入力された文字列をひらがなに変換し，それを部分文字列に分割します．それに対してそれぞれ日本語の変換をおこない，Wikipediaのページが存在するならば単語として成立しているとみなします．


# 使用させていただいたapi
<!-- Begin Yahoo! JAPAN Web Services Attribution Snippet -->
<span><a href="https://developer.yahoo.co.jp/sitemap/">Webサービス by Yahoo! JAPAN</a></span>
<!-- End Yahoo! JAPAN Web Services Attribution Snippet -->

<a href="https://www.mediawiki.org/wiki/API:Main_page/ja" >Powered by MediaWiki</a>
