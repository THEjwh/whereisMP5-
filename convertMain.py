import glob
import os
import cv2
import moviepy.editor as mp
import numpy as np
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

def createCoverFile(path):
     vid = cv2.VideoCapture(path)
     while(vid.isOpened()):
          ret, frame = vid.read()
          resizeImage = cv2.resize(frame, (720,720))
          cv2.imwrite("cover.jpg", resizeImage)
          break
     vid.release()

def inputAlbumCover(path):
     audio = MP3(path, ID3=ID3)
     
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
     inputAlbumCover(path2)
     os.remove('cover.jpg')
     clip.close()
   
   
def init():
     if not os.path.exists('./outputs'):
          os.makedirs('./outputs')
     if not os.path.exists('./videos'):
          os.makedirs('./videos')
          
print('start')
init()

path = "./videos/*"
mp4_list = glob.glob(path)
mp4_listed = [file for file in mp4_list if file.endswith(".mp4")]

for i in mp4_listed:
     createCoverFile(i)
     createMp3File(i)
     os.remove(i)

print('done')
