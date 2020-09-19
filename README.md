# npb_scraping
NPBの各年度の選手の野手成績，投手成績（Stats）を[https://www.baseball-reference.com](https://www.baseball-reference.com)から取得し，Pandas.DataFrame形式に変換するライブラリ。
分析例はexamples参照。

## How to Use
* 野手成績を取得する`ScrapingNPBBatter`と投手成績を取得する`ScrapingNPBPitcher`クラスを用意
* リーグの指定，取得年度の指定，チームの指定を行うことが可能

* 利用例: 横浜ベイスターズの2012年の野手成績，投手成績を取得する

```
from npb_scraping import player

# バッターの場合
dena_scrap = player.ScrapingNPBBatter(year_list=[2012], team='Yokohama Bay Stars')
dena_batter_data = dena_scrap.get_table() # データを取得

print(dena_batter_data)
                                          Age    G   PA   AB   R    H  2B 3B  \
team               year Name                                                   
Yokohama Bay Stars 2012 Carlos Alvarado    34    8   11   11   0    3   0  0   
                        Sho Aranami        26  141  550  504  53  135  16  7   
                        Bobby Cramer       32    2    3    3   0    0   0  0   
                        Hitoshi Fujie      26   52    2    2   0    0   0  0   
                        Shugo Fujii        35   16   22   18   3    4   0  0    

# ピッチャーの場合
dena_scrap = player.ScrapingNPBPitcher(year_list=[2012, 2015], team='Yokohama Bay Stars')
dena_pitcher_data = dena_scrap.get_table() # データを取得

# 省略
```

## Future Work
* 最低限の前処理
* 守備指標の取得
* チーム成績の取得
* 球団名が変わった場合の対応