#!/usr/bin/env python
# coding: utf-8

# In[1]:


#必要なライブラリをインポート
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from urllib.parse import urljoin


# In[2]:


def ParseRoomDetail(EstateElem):
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
    HeaderInfo = [EstateName, EstateAddress, EstateLocation, EstageAge, EstageHight]
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
        #Add Header Info
        Roomtable.extend(HeaderInfo)
        RoomDetail.append(Roomtable)
    return RoomDetail


# In[3]:


def Parsedistrict(PageFullURLs, RoomDetails):
    for icount, url in enumerate(PageFullURLs):
        print("    Room Detail Status: " + str(icount + 1) + "/" + str(len(PageFullURLs)))
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
            RoomDetails.extend(ParseRoomDetail(EstateElem))
        time.sleep(10)
    print("total # of Rooms: " + str(len(RoomDetails)))
    return RoomDetails


# In[12]:


#URL（賃貸住宅情報 検索結果の1ページ目） #12万円以下 15分以内 15年以内 2階以上／室内洗濯機置場／バス・トイレ別 管理費・共益費込み 鉄筋系／鉄骨系／ブロック・その他
BaseURLs = []
for i in range(23):
    BaseURLs.append("https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=131" + str(i+1).zfill(2) + "&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1")
BaseURLs


# In[13]:


RoomDetails = []
for iMcount, url in enumerate(BaseURLs):
    print("District Status: " + str(iMcount + 1) + "/" + str(len(BaseURLs)))
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
    #1ページ目を先頭に格納
    PageURLs.insert(0, url)
    PageFullURLs = [urljoin("https://suumo.jp/", relative) for relative in PageURLs] #相対パス -> 絶対パス
    PageFullURLs = list(dict.fromkeys(PageFullURLs)) #重複削除
    RoomDetails = Parsedistrict(PageFullURLs, RoomDetails)


# In[14]:


#Header Name
RoomtableHeadElem =  body.find("div",{'class':'cassetteitem'}).find("thead").find_all("th")
HeaderNames = [temp.get_text() for temp in RoomtableHeadElem]
HeaderNames.append("NewArrival")
HeaderNames.extend(["マンション名", "住所", "最寄り駅", "築年数", "建物高さ"])
HeaderNames = [temp.replace("\xa0", str(i)) for i, temp in enumerate(HeaderNames)] #空白の場合行番号で置き換え


# In[15]:


df = pd.DataFrame(RoomDetails, columns = HeaderNames)
filename = "SUMMO_Room.csv"
df.to_csv(filename)

BaseURLs = [
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #千代田区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13102&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #中央区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13103&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #港区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13104&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #新宿区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13105&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #文京区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13113&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #渋谷区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13106&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #台東区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13107&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #墨田区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13108&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #江東区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13118&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #荒川区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13121&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #足立区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13122&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1", #葛飾区
    "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13123&cb=0.0&ct=12.0&co=1&et=15&cn=15&mb=0&mt=9999999&kz=1&kz=2&kz=4&tc=0400101&tc=0400501&tc=0400301&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1" #江戸川区
]


BaseURLs = [
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
    "", #
]
