# 連続部分文字列の単語判定
このURLで使用することが出来ます.  
https://substring-word-finder.onrender.com

# 概要
連続部分文字列をとり，それが単語として存在するかどうかを判定します．

# 実装方法
streamlitを用いて実装しています．  
入力された文字列をひらがなに変換し，それを連続部分文字列に分割します．それに対してそれぞれ日本語の変換をおこない，Wikipediaのページが存在するならば単語として成立しているとみなします．


# 使用させていただいたapi
<!-- Begin Yahoo! JAPAN Web Services Attribution Snippet -->
<span><a href="https://developer.yahoo.co.jp/sitemap/">Webサービス by Yahoo! JAPAN</a></span>
<!-- End Yahoo! JAPAN Web Services Attribution Snippet -->

<a href="https://www.mediawiki.org/wiki/API:Main_page/ja" >Powered by MediaWiki</a>
