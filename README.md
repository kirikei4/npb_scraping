# npb_scraping
NPB data

## How to Use

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
```
