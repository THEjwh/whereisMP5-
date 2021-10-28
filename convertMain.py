import csv
import glob
import os
import eyed3
import cv2
import moviepy.editor as mp
import numpy as np
import pandas as pd
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, error
from mutagen.mp3 import MP3
from pytube import Playlist, YouTube

import ytdlpfunc as ytf

def delspecial(strs):
     if strs.find('"') != -1:
          strs = strs.replace('"', '˝')
     if strs.find(':') != -1:
          strs = strs.replace(':', '：')
     if strs.find('/') != -1:
          strs = strs.replace('/', '／')
     
     return strs

def returnMetaDic(path):
     f = open(path, 'rt', encoding='UTF8')
     songdec = f.read()
     desp = songdec.split('\n\n')
     
     #2번째 문단에 곡 이름과 아티스트 이름 있음
     desp2 = desp[1].split(' · ')
     
     songname = ''
     artistname = ''
     p = 0
     for ii in desp2:
          if p == 0:
               songname = ii
               p = 1
          else:
               if p == 1:
                    artistname = artistname + ii
                    p = p + 1
                    #참여 아티스트 태그에 다 넣으려 했는데 난잡해져서 대표 하나만 넣기로함
                    break
               else:
                    artistname = artistname + '/' + ii
               
     
     dic = {
          'Songname' : songname,
          'Artistname' : artistname,
          'Albumname' : delspecial(desp[2]),
          #'Albumartistname' : desp[3].replace('℗ ', ''),
          #'Year' : year,
          #'Date' : date,
     }
     
     #앨범아티스트 따로 없는 설명도 있어서
     sk = 0
     desp[3] = delspecial(desp[3])
     if desp[3].find('℗ ') != -1:
          desp[3] = desp[3].replace('℗ ', '')
          
          #일부 연도 + 배급사 이름이 적힌 경우 그냥 앨범아티스트 이름에 아티스트 이름넣기   
          if desp[3].find('19') != -1:
               b = 0
               try:
                    a = desp[3][desp[3].find('19'):desp[3].find('19') + 4]
                    aa = int(a)
               except ValueError:
                    b = 1
               
               if b == 0:
                    dic['Albumartistname'] = dic['Artistname']
               else:
                    dic['Albumartistname'] = desp[3]
          elif desp[3].find('20') != -1:
               b = 0
               try:
                    a = desp[3][desp[3].find('20'):desp[3].find('20') + 4]
                    aa = int(a)
               except ValueError:
                    b = 1
                    
               if b == 0:
                    dic['Albumartistname'] = dic['Artistname']
               else:
                    dic['Albumartistname'] = desp[3]
          else:
               dic['Albumartistname'] = desp[3]
     else:
          dic['Albumartistname'] = dic['Artistname']
          #3번째칸에 출시 날짜가 적혀있는 설명도 있어서
          if desp[3].find('Released on: ') != -1:
               ab = desp[3].replace('Released on: ', '')
               dic['Date'] = ab
               dic['Year'] = ab[:4]
               sk = 1
     
     
     #출시 날짜가 안적혀있는 영상 설명도 있어서
     if desp[4].find('Released on: ') != -1 and sk == 0:
          abc = desp[4].replace('Released on: ', '')
          dic['Date'] = abc
          dic['Year'] = abc[:4]
          
     f.close()
     
     return dic

def createMetamp3(path, item):
     audio = eyed3.load(path)
     audio.tag.artist = item['Artistname']
     audio.tag.title = item['Songname']
     audio.tag.album_artist = item['Albumartistname']
     audio.tag.album = item['Albumname']
     audio.tag.track_num = (item['Tracknum'], item['MaxTracknum'])
     audio.tag.save()
     audio2 = MP3(path, ID3=EasyID3)
     if 'Year' in item:
          audio2['date'] = item['Year']
     audio2.save()
     
     

def createCoverFile(path):
     vid = cv2.VideoCapture(path)
     while(vid.isOpened()):
          ret, frame = vid.read()
          resizeImage = cv2.resize(frame, (720,720))
          cv2.imwrite("cover.jpg", resizeImage)
          break
     vid.release()

def inputAlbumCover(path, option):
     audio = MP3(path, ID3=ID3)
     if option == 1:
          name = path.replace('./outputs\\', '')
          name = name.replace('.mp3', '')
     
     try:
          audio.add_tags()
     except error:
          pass
     
     
     audio.tags.add(APIC(mime='image/jpeg', type=3,desc=u'Cover',data=open('cover.jpg', 'rb').read()))
     audio.save()

def createMp3File(path):
     clip = mp.VideoFileClip(path)
     path2 = path.replace("videos", 'outputs')
     path2 = path2.replace("mp4", "mp3")
     clip.audio.write_audiofile(path2, bitrate="320k")
     inputAlbumCover(path2, 1)
     os.remove('cover.jpg')
     clip.close()
     
def downloadPlaylist(getpath):
     
     #유튜브 뮤직의 앨범 플레이리스트를 일반 유튜브 플레이리스트 링크로 바꾸기
     if getpath.find('music.') != -1:
          getpath = getpath.replace('music.', '')
     ytf.downloadplaylist(getpath)
     loc = ytf.Getloc().replace("\\", '/')
     
     #커버파일 만들기
     createCoverFile('./cover/cover.mp4')
     loc = loc[:loc.find('/') + loc[loc.find('/') + 1:].find('/') + 2]
     #최종적으로 저장될 저장경로 미리 세팅
     lloc = './' + loc[:loc.find('/')]
     loc = './' + loc + '*'
     
     #mp3 파일 불러오기
     mp3_list = glob.glob(loc)
     mp3_listed = [file for file in mp3_list if file.endswith('.mp3')]
     
     #파일 개수로 총 트랙수 
     maxtrack = len(mp3_listed)
     
     first = 1
     for i in range(1, maxtrack+1):
          print(mp3_listed[i-1] + '의 커버와 메타데이터 등록중')
          
          #메타데이터 뽑아낼 영상 설명파일 들고오기
          depath = mp3_listed[i - 1].replace('mp3', 'mp4.description')
          metadic = returnMetaDic(depath)
          
          if first == 1:
               first = 0
               lloc = lloc + '/' + metadic['Albumartistname'] + '/' + metadic['Albumname'] + '/'
               
          
          
          #반복한 횟수로 트랙 순서 넣기. 짜피 다운로드 받은 순서대로 이름앞에 순서 붙어서 정렬할필요없음
          metadic['Tracknum'] = i
          metadic['MaxTracknum'] = maxtrack
          
          #커버 넣고 메타데이터도 넣기
          inputAlbumCover(mp3_listed[i-1],0)
          createMetamp3(mp3_listed[i-1], metadic)
          
          print('메타데이터 삽입')
     print('메타데이터 처리 완료')
     print('파일 정리')
     
     #쓸모없는 메타 데이터 관련 파일들 다 지우기
     dec_list = [file for file in mp3_list if file.endswith('.description')]
     for i in dec_list:
          os.remove(i)
     os.remove('cover.jpg')
     os.remove('./cover/cover.mp4')
     
     #받고 처리된 mp3들 다 /앨범아티스트명/앨범이름 폴더에 넣고 기존 폴더 지우기
     for i in mp3_listed:
          i = i.replace('\\\\', '/')
          loc = loc.replace('*', '')
          i = i.replace('\\','/')
          aaa = i.replace(loc, lloc)
          if not os.path.exists(lloc):
               os.makedirs(lloc)
          os.rename(i, aaa)
          
     try:
          os.rmdir(loc)
     except:
          print('')
          pass
     
     print('작업 완료.')
   
   
def init():
     if not os.path.exists('./outputs'):
          os.makedirs('./outputs')
     if not os.path.exists('./videos'):
          os.makedirs('./videos')
     if not os.path.exists('./playlist'):
          os.makedirs('./playlist')
     if not os.path.exists('./cover'):
          os.makedirs('./cover')
          
print('start')
init()

print('1.videos의 폴더의 mp4 파일을 mp3로 변환, mp4 파일의 첫 프레임을 커버로 사용 \n2. 유튜브 앨범 플레이리스트 링크로 앨범 받기.\n3. list.txt파일의 플레이리스트 링크 받기.(줄띄움으로 구분)')

choose = '0'

choose = input(": ")
if choose == '1' :
     path = "./videos/*"
     mp4_list = glob.glob(path)
     mp4_listed = [file for file in mp4_list if file.endswith(".mp4")]
     
     if len(mp4_listed) >= 1:      
          for i in mp4_listed:
               createCoverFile(i)
               createMp3File(i)
               os.remove(i)
     
     print('done')

elif choose == '2':
     lehu = 1
     while lehu == 1:
          getpath = input('\n(-1 is quit)link:')
          if getpath == '-1':
               break
          downloadPlaylist(getpath)
          
     

elif choose == '3':
     f = open('list.txt', 'r')
     lists = f.read().split('\n')
     print (str(len(lists)) + '개 리스트 감지')
     a = 1
     for i in lists:
          print(str(a) + '번째 작업 시작')
          print(i + ' 다운로드 시작')
          downloadPlaylist(i)
          print('완료')
          a =  a + 1
     
     print ('전부 완료!')
     f.close()
elif choose == '0':
     abc = '1910'
     abcd = '19ab'
     
     print(abc.find('19'))
     print(abc[abc.find('19'):abc.find('19') + 4])
     print(int(abc[abc.find('19'):abc.find('19') + 4]))
     
     try:
          print(int(abcd[abcd.find('19'):abcd.find('19') + 4]))
     except ValueError:
          print('swag')
     