from cgi import test
import re
import requests
from bs4 import BeautifulSoup
from email import header
from urllib import response
import browser_cookie3
import urllib.request
import json
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#유튜브 앨범 채널 예)https://music.youtube.com/channel/UCYiYZYbDlyy17QiX5CxCTeQ
#링크를 올리면 바로 그 채널의 앨범 플레이리스트를 전부 합친 뒤, 리스트 리턴
#단 구현방식이 좀 조잡해서... 앨범이 적은 아티스트는 작동하긴 하는데 제대로 깔끔하게 안되고,
#속도도 참 느려서 아쉽다 아쉬워

def makeurllist(testlist):

    #channnel -> browse로. 사실상 둘다 똑같은데 걍 신경쓰여서...
    for i in testlist:
        i = i.replace('/channel/', '/browse/')
    
    print('아티스트 앨범 url 수집을 시작합니다. 곧 파이어폭스가 열립니다.')
    
    maxcount = len(testlist)
    ##items > ytmusic-two-row-item-renderer:nth-child(1) > div.details.style-scope.ytmusic-two-row-item-renderer > div > yt-formatted-string > a
    #  ytmusic-two-row-item-renderer.style-scope:nth-child(1) > div:nth-child(2) > div:nth-child(1) > yt-formatted-string:nth-child(2) > a:nth-child(1)
    
    #셀레니움으로 넣어줄 쿠키
    s = browser_cookie3.firefox(domain_name='.youtube.com')
    #나중에 쓸 브라우저 헤더
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
   
   #파이어폭스 띄운 후 내 로컬 파폭의 쿠키 넣기.
    service = FirefoxService(executable_path=GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    
    driver.get('https://www.youtube.com/')
    cookie = None

    for c in s:
        if c.domain == '.youtube.com':
            cookie = {'domain': c.domain, 'name': c.name, 'value': c.value, 'secure': c.secure and True or False}
        driver.add_cookie(cookie)

    driver.get('https://www.youtube.com/')

    #browse 형태의 링크 받아둘 놈
    reallist = []
    counting = 0
    #testlist 각 링크의 아티스트의 앨범 받기
    for i in testlist:
        counting = counting + 1
        print(i + ' 작업 시작')
        print(str(counting) + ' / ' + str(maxcount))
        if i == '':
            continue
        driver.get(i)
        driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN) 

        #동적 사이트라 쬐금 기다리고
        time.sleep(2)
        #앨범 버튼 눌러서 전체 보기... 동적 사이트라 앨범 다보기 링크같은게 따로 없어...
        try:
            driver.find_element(By.XPATH, '/html/body/ytmusic-app/ytmusic-app-layout/div[3]/ytmusic-browse-response/ytmusic-section-list-renderer/div[2]/ytmusic-carousel-shelf-renderer[1]/ytmusic-carousel-shelf-basic-header-renderer/h2/div/yt-formatted-string/a').click()
        except:
            pass

        time.sleep(2)

        #앨범 전체 띄운후 html 뜯어오기
        html = driver.page_source
        html = html.encode('utf-8')
        finalhtml = html.decode('utf-8')
        totalalbums = []
        cucu = 1

        #html에서 링크부분 무식하게 다 뜯어오기. 아니 뭔 선택자로 지정이 안돼
        while cucu == 1:
            if finalhtml.find('<a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href=') == -1:
                break
        
            ck = finalhtml.find('<a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href=')

            cck = ck + 87
            ccck = finalhtml[cck:].find('"') + cck
            album = finalhtml[cck:ccck]
            totalalbums.append(album)
            finalhtml = finalhtml.replace('<a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href=', '', 1)
        
        #링크 모음집에서 잡링크 덜어내고 찐링크 모음
        zinalbums = []

        for i in totalalbums:
            if i.find('browse/MPREb') != -1:
                zinalbums.append(i)

        #중복제거후 합치기
        zinzin = set(zinalbums)
        zinzinzin = list(zinzin)
        reallist.extend(zinzinzin)

    driver.quit()
    print('album total ended')

    Rcookie = browser_cookie3.firefox()
    changedlist = []

    #requests로 또 각 링크의 playlist 링크 얻어오기. 아니 html은 browse형태로 들어있는데.. 이게 yt_dlp에서 인식을 못해서 바꿔야함
    print('링크 얻어오는중...')
    rcount = 0
    for f in reallist:
        rcount = rcount + 1
        print(str(rcount) + ' / ' +  str(len(reallist)))
        #print('https://music.youtube.com/' + f)
        response = requests.get('https://music.youtube.com/' + f, headers = header,cookies= Rcookie)
        abc = response.text
        ck = abc.find('playlist?list')
        ckk = abc[ck+14:].find('\\')
        superdragon = abc[ck - 29: ck + 14 + ckk]
        superdragon = superdragon.replace('\\', '')
        superdragon = superdragon.replace('playlist?listx3d', 'playlist?list=')
        changedlist.append(superdragon)


    print('플레이리스트 링크 수집 완료')
    reallist.clear()
    return changedlist


        

#soup = BeautifulSoup(html, 'html.parser', from_encoding = 'utf-8')
#print(soup.text)

#<a class="yt-simple-endpoint style-scope yt-formatted-string" spellcheck="false" href=


