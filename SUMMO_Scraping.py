#!/usr/bin/env python
# coding: utf-8

# #  SUMMOスクレイピングメイン

# In[1]:


#必要なライブラリをインポート
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from urllib.parse import urljoin


# In[2]:


def Recursive_PageNum(All_PageFullURLs, url):
    #データ取得
    result = requests.get(url)
    c = result.content
    #HTMLを元に、オブジェクトを作る
    soup = BeautifulSoup(c, "html.parser")
    #ページ数を取得
    body = soup.find("body")
    pages = body.find("div",{'class':'pagination pagination_set-nav'}) #Page数の部分のhtmlを抜き出す
    links = pages.select("a[href]") #link付きaタグを抜き出す
    #ページ選択で数値になっているリンクを引っ張ってくる（"次へ"を除く）
    PageURLs = [link.get("href") for link in links if link.get_text().isdigit()]
    PageFullURLs = [urljoin("https://suumo.jp/", relative) for relative in PageURLs] #相対パス -> 絶対パス
    #1ページ目を先頭に格納
    PageFullURLs.insert(0, url)
    PageFullURLs = list(dict.fromkeys(PageFullURLs)) #重複削除
    nPages = [int(link.get_text()) for link in links if link.get_text().isdigit()]
    All_PageFullURLs.extend(PageFullURLs)
    All_PageFullURLs = list(dict.fromkeys(All_PageFullURLs)) #重複削除
    #再帰関数Exit条件 1 pageしかない場合 / 2 pageしかない場合 / MaxとMax-1番目のページ数の差が1の場合
    if len(nPages) == 0 or len(nPages) == 1 or (sorted(nPages)[-1] - sorted(nPages)[-2]) ==1:
        print("Exit recursive loop! # of URLs are    " + str(len(All_PageFullURLs)))
        time.sleep(5)
        return All_PageFullURLs
    #再帰関数 ページ数が２番目に大きいURLを次の読み込みURLに指定
    time.sleep(5)
    return Recursive_PageNum(All_PageFullURLs, PageFullURLs[-2])

def PageNum_Easy(url):
    #データ取得
    result = requests.get(url)
    c = result.content
    #HTMLを元に、オブジェクトを作る
    soup = BeautifulSoup(c, "html.parser")
    #ページ数を取得
    body = soup.find("body")
    pages = body.find("div",{'class':'pagination pagination_set-nav'}) #Page数の部分のhtmlを抜き出す
    links = pages.select("a[href]") #link付きaタグを抜き出す
    #ページ選択で数値になっているものを引っ張ってくる（"次へ"を除く / 1のみの場合は空リスト）
    nPages = [int(link.get_text()) for link in links if link.get_text().isdigit()]
    if len(nPages) == 0:
        PageFullURLs = [url]
    else:
        MaxPages = sorted(nPages)[-1] #Max page数
        PageFullURLs = []
        for ipg in range(MaxPages):
            base_URL = url + '&page=' + str(ipg+1)
            PageFullURLs.append(base_URL)
    return PageFullURLs


# In[3]:


def ParseRoomDetail(EstateElem, url):
    #マンション名取得
    EstateName = EstateElem.find("div",{'class':'cassetteitem_content-title'}).get_text()
    #住所取得
    EstateAddress = EstateElem.find("li",{'class':'cassetteitem_detail-col1'}).get_text()
    #最寄り駅取得
    EstateLocationElem = EstateElem.find("li",{'class':'cassetteitem_detail-col2'}).find_all("div",{'class':'cassetteitem_detail-text'})
    EstateLocations = [EstateLocation.get_text() for EstateLocation in EstateLocationElem] #リストで取得
    EstateLocation = ' --- '.join(EstateLocations)
    #築年数と建物高さを取得
    EstateCol3Elem = EstateElem.find("li",{'class':'cassetteitem_detail-col3'}).find_all("div")
    EstageAge = EstateCol3Elem[0].get_text()
    EstageHight = EstateCol3Elem[1].get_text()
    #Header Info をListに
    HeaderInfo = [EstateName, EstateAddress, EstateLocation, EstageAge, EstageHight, url]
    #階、賃料、管理費、敷/礼/保証/敷引,償却、間取り、専有面積が入っているtableを全て抜き出し
    RoomtableElem =  EstateElem.find("table",{'class':'cassetteitem_other'})
    RoomDetail = []
    #Contents
    for rooms in RoomtableElem.find_all("tbody"):
        Roomtable = [temp.get_text() for temp in rooms.findAll('td')]
        if "cassetteitem_other-checkbox--newarrival" in rooms.td['class']:
            Roomtable.append("New")
        else:
            Roomtable.append("Exsiting")
        Roomlinks = EstateElem.select("a[href]") #link付きaタグを抜き出す
        #"詳細を見る"の表示になっているリンクを引っ張ってくる
        RoomDetailURL = [link.get("href") for link in Roomlinks if link.get_text() == "詳細を見る"][0]
        RoomFullDetailURL = urljoin("https://suumo.jp/", RoomDetailURL) #相対パス -> 絶対パス
        Roomtable.append(RoomFullDetailURL)
        #Add Header Info
        Roomtable.extend(HeaderInfo)
        RoomDetail.append(Roomtable)
    return RoomDetail


# In[4]:


def Parsedistrict(PageFullURLs, RoomDetails):
    for icount, url in enumerate(PageFullURLs):
        print("    Room Detail Status: " + str(icount + 1) + "/" + str(len(PageFullURLs)))
        try:
            #データ取得
            result = requests.get(url)
            c = result.content
            #HTMLを元に、オブジェクトを作る
            soup = BeautifulSoup(c, "html.parser")
            #物件リストの部分を切り出し
            summary = soup.find("div",{'id':'js-bukkenList'})
            #マンション名、住所、立地（最寄駅/徒歩~分）、築年数、建物高さが入っているcassetteitemを全て抜き出し - デフォルト設定で最大30件の物件表示
            cassetteitems = summary.find_all("div",{'class':'cassetteitem'})
            #マンションの数でループ
            for EstateElem in cassetteitems:
                RoomDetails.extend(ParseRoomDetail(EstateElem, url))
        except requests.exceptions.RequestException as e:
            print("エラー : ",e)
        time.sleep(5)
    print("total # of Rooms: " + str(len(RoomDetails)))
    return RoomDetails


# In[5]:


#検索１ページ目
#ta=が都道府県コード
#sc=を無くせば都道府県単位の情報になる
#東京23区はsc=13101 ~ 13123
#条件：　12万円以下 15分以内 15年以内 2階以上／室内洗濯機置場／バス・トイレ別 管理費・共益費込み 鉄筋系／鉄骨系／ブロック・その他
BaseURLs = [
    #東京都
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?url=%2Fchintai%2Fichiran%2FFR301FC001%2F&ar=030&bs=040&pc=30&smk=&po1=25&po2=99&co=1&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&cb=0.0&ct=12.0&et=15&mb=0&mt=9999999&cn=15&ta=13",
    #神奈川県
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?url=%2Fchintai%2Fichiran%2FFR301FC001%2F&ar=030&bs=040&pc=30&smk=&po1=25&po2=99&co=1&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&cb=0.0&ct=12.0&et=15&mb=0&mt=9999999&cn=15&ta=14",
    #千葉県
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?url=%2Fchintai%2Fichiran%2FFR301FC001%2F&ar=030&bs=040&pc=30&smk=&po1=25&po2=99&co=1&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&cb=0.0&ct=12.0&et=15&mb=0&mt=9999999&cn=15&ta=12",
    #埼玉県
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?url=%2Fchintai%2Fichiran%2FFR301FC001%2F&ar=030&bs=040&pc=30&smk=&po1=25&po2=99&co=1&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&cb=0.0&ct=12.0&et=15&mb=0&mt=9999999&cn=15&ta=11"
]


# In[6]:

#Header Name
soup = BeautifulSoup(requests.get(BaseURLs[0]).content, "html.parser")
body = soup.find("body")
RoomtableHeadElem =  body.find("div",{'class':'cassetteitem'}).find("thead").find_all("th")
HeaderNames = [temp.get_text() for temp in RoomtableHeadElem]
HeaderNames.append("NewArrival")
HeaderNames.append("RoomDetailLink")
HeaderNames.extend(["マンション名", "住所", "最寄り駅", "築年数", "建物高さ","SearchURL"])
HeaderNames = [temp.replace("\xa0", str(i)) for i, temp in enumerate(HeaderNames)] #空白の場合行番号で置き換え


# In[7]:


#Scraping Main
# RoomDetails = []　　#BaseURLsのデータをまとまりで出したい場合
for iMcount, url in enumerate(BaseURLs):
    print("District Status: " + str(iMcount + 1) + "/" + str(len(BaseURLs)))
    All_PageFullURLs = []
#     All_PageFullURLs = Recursive_PageNum(All_PageFullURLs, url) #全てのページのURLを取得
    All_PageFullURLs = PageNum_Easy(url)
    RoomDetails = [] #データをBaseURLsごと出力
    RoomDetails = Parsedistrict(All_PageFullURLs, RoomDetails) #ページごとの物件情報取得 / Pageのループはこの中
    df = pd.DataFrame(RoomDetails, columns = HeaderNames)
    filename = "SUMMO_FullRoom_" + str(iMcount) + ".csv"
    df.to_csv(filename)
