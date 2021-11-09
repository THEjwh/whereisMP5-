import json
import yt_dlp
from yt_dlp.postprocessor.common import PostProcessor


class MyLogger:
    def debug(self, msg):
        # For compatability with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class MyCustomPP(PostProcessor):
    def run(self, info):
        self.to_screen('Doing stuff')
        return [], info

#마지막 다운받은 경로 저장해놔서 나중에 mp3파일 찾을때 쓰는놈
def Fswag(a):
    if a == 0:
        return Fswag.kimchi
    Fswag.kimchi = a

#mp3 찾을때 쓰는놈을 이쁘게 쓰는놈
def Getloc():
    return Fswag(0)

def my_hook(d):
    if d['status'] == 'finished':
        Fswag(d['filename'])
        print(d['filename'] + ' 다운 완료 mp3 변환중')
        


def downloadplaylist(path):
    #940 940
    
    #일단 작동하는 파폭의 쿠키를 들고오게 해놧음
    ydl_opts = {
    #    'format': '(mp4)[height>=721]',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320'
        }],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
        'cookiesfrombrowser': ('firefox', ),
        'ffmpeg_location': 'C:/Users/user/Downloads/Compressed/ffmpeg-2021-10-14-git-c336c7a9d7-full_build/bin',
        #'outtmpl': './playlist/%(playlist_title)s/%(playlist_index)s.%(title)s.mp4',
        'outtmpl': './playlist/temp/%(playlist_index)s.%(title)s.mp4',
        'writedescription' : 1
    }
    
    #커버받는놈
    ydl_opts2 = {
        'format': 'mp4/bestvideo',
        'logger': MyLogger(),
        'cookiesfrombrowser': ('firefox', ),
        'ffmpeg_location': 'C:/Users/user/Downloads/Compressed/ffmpeg-2021-10-14-git-c336c7a9d7-full_build/bin',
        'outtmpl': './cover/cover.mp4',
        'playlist_items' : '1'
    }
    print('구성중...')
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_processor(MyCustomPP())
        print('start the download the ' + path)
        try:
            ydl.download([path])
        except yt_dlp.utils.DownloadError:
            print('다운로드 에러')
    print('playlist downlaod end start download cover mp4')
    with yt_dlp.YoutubeDL(ydl_opts2) as ydl2:
        print('start download cover')
        ydl2.download([path])
    print('다운로드 종료')
    