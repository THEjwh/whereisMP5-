import csv
import shutil
from curses import meta
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
import makeplaylisturl as mkurl

def delspecial(strs):
     if strs.find('"') != -1:
          strs = strs.replace('"', '˝')
     if strs.find(':') != -1:
          strs = strs.replace(':', '：')
     if strs.find('/') != -1:
          strs = strs.replace('/', '／')
     if strs.find('*') != -1:
          strs = strs.replace('*','')
     if strs.find('?') != -1:
          strs = strs.replace('?','？')
     if strs.find('|') != -1:
          strs = strs.replace('|', '｜')
     
     return strs

def returnMetaDic(path):
     f = open(path, 'rt', encoding='UTF8')
     songdec = f.read()
     desp = songdec.split('\n\n')
     
     chks = 0
     if desp[0].find('Provided to YouTube') == -1:
          chks = 1
     #2번째 문단에 곡 이름과 아티스트 이름 있음 근데 아닌경우도 있더라
     desp2 = desp[1 - chks].split(' · ')
     
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
          'Albumname' : desp[2 - chks]
          #'Albumname' : delspecial(desp[2 - chks]),.
          #'Albumartistname' : desp[3 - chks].replace('℗ ', ''),
          #'Year' : year,
          #'Date' : date,
     }
     
     #앨범아티스트 따로 없는 설명도 있어서
     sk = 0
     #desp[3 - chks] = delspecial(desp[3 - chks])
     if desp[3 - chks].find('℗ ') != -1:
          desp[3 - chks] = desp[3 - chks].replace('℗ ', '')
          
          #일부 연도 + 배급사 이름이 적힌 경우 그냥 앨범아티스트 이름에 아티스트 이름넣기   
          if desp[3 - chks].find('19') != -1 and (desp[3 - chks].find('19') < desp[3 - chks].find('20') or desp[3 - chks].find('20') == -1):
               b = 0
               try:
                    a = desp[3 - chks][desp[3 - chks].find('19'):desp[3 - chks].find('19') + 4]
                    aa = int(a)
               except ValueError:
                    b = 1
               
               if b == 0:
                    dic['Albumartistname'] = dic['Artistname']
               else:
                    dic['Albumartistname'] = desp[3 - chks]
          elif desp[3 - chks].find('20') != -1:
               b = 0
               try:
                    a = desp[3 - chks][desp[3 - chks].find('20'):desp[3 - chks].find('20') + 4]
                    aa = int(a)
               except ValueError:
                    b = 1
                    
               if b == 0:
                    dic['Albumartistname'] = dic['Artistname']
               else:
                    dic['Albumartistname'] = desp[3 - chks]
          else:
               dic['Albumartistname'] = desp[3 - chks]
     else:
          dic['Albumartistname'] = dic['Artistname']
          #3번째칸에 출시 날짜가 적혀있는 설명도 있어서
          if desp[3 - chks].find('Released on: ') != -1:
               ab = desp[3 - chks].replace('Released on: ', '')
               dic['Date'] = ab
               dic['Year'] = ab[:4]
               sk = 1
     
     
     #출시 날짜가 안적혀있는 영상 설명도 있어서
     if len(desp) > 4 and desp[4 - chks].find('Released on: ') != -1 and sk == 0:
          abc = desp[4 - chks].replace('Released on: ', '')
          dic['Date'] = abc
          dic['Year'] = abc[:4]
     
    # dic['Albumartistname'] = delspecial(dic['Albumartistname'])
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

def createCoverFile2(path):
     img = cv2.imread(path)
     retval, buf = cv2.imencode(".webp", img, [cv2.IMWRITE_WEBP_QUALITY, 100])
     img = cv2.imdecode(buf,1)
     crop = img[0:720, 280:280+720]
     cv2.imwrite("cover.jpg", crop)

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
               lloc = lloc + '/' + delspecial(metadic['Albumartistname']) + '/' + delspecial(metadic['Albumname']) + '/'
               
          
          
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
          try:
               i = i.replace('\\\\', '/')
               loc = loc.replace('*', '')
               i = i.replace('\\','/')
               aaa = i.replace(loc, lloc)
               if not os.path.exists(lloc):
                    os.makedirs(lloc)
               os.rename(i, aaa)
               print(aaa + ' 으로 작업됨')
          except:
               pass
          
     try:
          shutil.rmtree(loc)
          os.rmdir(loc)
     except:
          print('')
          pass
     
     print('작업 완료.')

#만들다 만 함수
def downloadUser(getpath):
     #유튜브 뮤직의 앨범 플레이리스트를 일반 유튜브 플레이리스트 링크로 바꾸기
     #if getpath.find('music.') != -1:
       #   getpath = getpath.replace('music.', '')
     
     #if getpath.find('/playlists') == -1:
      #    getpath = getpath + '/playlists'
          
     ytf.downloaduserplaylist(getpath)
     albumlist = glob.glob('./playlist/artist_temp/*/', recursive = False)
     r_albumlist = []
     for i in albumlist:
          dummy = []
          covercount = 1
          trackcount = 1
          mp3_listed = [file for file in i if file.endswith('.mp3')]
          maxtrack = len(mp3_listed)
          for j in os.listdir(i):
               dummy.append(i+j)
          r_albumlist.append(dummy)
     for i in r_albumlist:
          mp3_listed = [file for file in i if file.endswith('.mp3')]
          maxtrack = len(mp3_listed)
          print(mp3_listed[0].replace('mp3', 'mp4.webp'))
          shutil.copy(mp3_listed[0].replace('mp3', 'mp4.webp'), 'cover.webp')
          createCoverFile2('cover.webp')

          
          for j in range(1, maxtrack+1):
               k = j - 1
               print(mp3_listed[k] + '의 커버와 메타데이터 등록중')
               depath = mp3_listed[k].replace('mp3', 'mp4.description')
               metadic = returnMetaDic(depath)
               print(metadic)
               metadic['Tracknum'] = j
               metadic['MaxTracknum'] = maxtrack

               inputAlbumCover(mp3_listed[k], 0)
               createMetamp3(mp3_listed[k], metadic)

               deti = './outputs/' + delspecial(metadic['Albumartistname']) + '/' + delspecial(metadic['Albumname'])
               if not os.path.exists(deti):
                    os.makedirs(deti)
               shutil.move(mp3_listed[k], deti)
          os.remove('cover.jpg')
          os.remove('cover.webp')

     shutil.rmtree('./playlist/artist_temp')
                    


               
   
def init():
     if not os.path.exists('./outputs'):
          os.makedirs('./outputs')
     if not os.path.exists('./videos'):
          os.makedirs('./videos')
     if not os.path.exists('./playlist'):
          os.makedirs('./playlist')
     if not os.path.exists('./cover'):
          os.makedirs('./cover')
     if not os.path.exists('./video'):
          os.makedirs('./video')
     if not os.path.exists('./ffmpeg'):
          os.makedirs('./ffmpeg')
          
print('start')
init()

print('1. videos의 폴더의 mp4 파일을 mp3로 변환, mp4 파일의 첫 프레임을 커버로 사용 \n2. 유튜브 앨범 플레이리스트 링크로 앨범 받기.\n3. list.txt파일의 플레이리스트 링크 받기.(줄띄움으로 구분)')
print('4. video 폴더에 링크 영상 받기\n5. artlist.txt로 각 채널의 모든 플레이리스트 받고 mp3 변환하기\n6. artlist.txt의 각 채널 링크로 그 채널의 모든 앨범 플레이 리스트 list.txt로 출력')


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
          if i == '':
               continue
          downloadPlaylist(i)
          print('완료')
          a =  a + 1
     
     print ('전부 완료!')
     f.close()
elif choose == '4':
     lehu = 1
     while lehu == 1:
          getpath = input('\n(-1 is quit)link:')
          if getpath == '-1':
               break
          ytf.downloadvideo(getpath)
elif choose == '5':
     print('오래 걸릴수 잇습니다...')
     f = open('artlist.txt', 'r')
     lists = f.read().split('\n')
     print (str(len(lists)) + '개 아티스트 채널 감지')
     hyperlist = mkurl.makeurllist(lists)
     print(str(len(hyperlist)) + '개 앨범 링크 수집됨')

     counting = 0
     for i in hyperlist :
          counting = counting + 1
          print(i + '의 작업을 시작합니다.')
          print(str(counting) + ' / ' + str(len(hyperlist)))
          if i == '':
               continue
          downloadPlaylist(i)
          print('완료')
     print('작업이 완료되었습니다.')
     f.close()
     #getpath = input('\n(-1 is quit)link:')
     #downloadUser(getpath)
     #print('ended')
elif choose == '6':
     print('오래 걸릴수 잇습니다...')
     f = open('artlist.txt', 'r')
     lists = f.read().split('\n')
     print (str(len(lists)) + '개 아티스트 채널 감지')
     hyperlist = mkurl.makeurllist(lists)
     print(str(len(hyperlist)) + '개 앨범 링크 수집됨')

     f2 = open('list.txt', 'w' )
     for i in hyperlist:
          f2.write(i + '\n')

     print('작업이 완료되었습니다.')
     f.close()
     f2.close()

else:
     print('')

     