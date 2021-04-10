import requests
from bs4 import BeautifulSoup as bs
from threading import Thread
import sys
import os

class server(object):
    def __init__(self,term):
        self.term=term
        self.ep0=False
        self.highest=False

    def search(self):
        keyw=self.term.lower().split()
        req=requests.get('https://vidstreaming.io/ajax-search.html?keyword={}'.format('+'.join(keyw)),headers={"x-requested-with": "XMLHttpRequest"})
        req_page=bs(req.text,'html.parser')
        if req_page.content=='':
            print('Could not find the desired term in vidstreaming, try with a more specific search')
        else:
            name=req_page.a['href'].split('videos')[1].split('-episode')[0]
            # print(name)
            name=name.strip("\ ").strip('/')
            self.name=name
        self.saveName=' '.join(name.split('-'))

    def get_no(self):
        w=' '.join(self.name.split('+'))
        print(w)
        try:
            page=requests.get('https://vidstreaming.io/videos/{}-episode-0'.format(w))
            soup=bs(page.text,'html.parser')
            no_ep=len(soup.find_all('ul')[1].find_all('li'))
            lastep=no_ep-1
            print('Connected!')
            self.ep0=True
            return(lastep)
        except:
            page=requests.get('https://vidstreaming.io/videos/{}-episode-1'.format(w))
            print('Connected!')
            self.ep0=False
            soup=bs(page.text,'html.parser')
            no_ep=len(soup.find_all('ul')[1].find_all('li'))
            return(no_ep)

    def get_ep(self,st,stop):
        self.urls={}
        self.search()
        lastep=self.get_no()
        # if self.ep0:
        #    self.urls=['0' for i in range(st)]
        # else:
        #    self.urls=['0' for i in range(1,st)]
        print('Discovered {} episodes.'.format(lastep))
        if stop>lastep:
            stop=lastep
        start=st
        if self.ep0 and start==1:
            start=0
        for i in range(start,stop+1):
            print(i)
            pageu=requests.get('https://vidstreaming.io/videos/{}-episode-{}'.format(self.name,i))
            soup=bs(pageu.text,'html.parser')
            vkey=soup.find_all('iframe')[0].attrs['src'].split('id=')[1].split('=')[0]
            vreq=requests.get('https://vidstreaming.io/ajax.php?id={}'.format(vkey))
            soup1=vreq.json()
            self.urls[i]=soup1['source'][0]['file']

    def m3u8parse(self,u):
        r=requests.get(u)
        l=r.text.split('\n')
        l.pop()
        resd={}
        for k in l:
            if (k.startswith('#EXT')==False):
                t=k.split('.')
                resd[t[2]]=k
        resl=list(resd.keys())
        if self.highest==False:
            reqres=input('The available resolutions are {}. \nIf you want the highest quality in all of \nthe following episodes, enter "highest".'.format(resl))
        if reqres=='highest':
            self.highest=True
            reqres=resl[-1]
        resurlend=resd[reqres]
        u=u.split('/')
        u.pop()
        u.append(resurlend)
        resurl='/'.join(u)
        r=requests.get(resurl)
        poi=-1
        l=r.text.split('\n')
        l.pop()
        while l[poi].startswith('#'):
            poi-=1
        something=l[poi]
        tot=something.split('.')[2][3:]
        something=l[poi].split('.')
        tot=int(tot)
        something[2]=something[2][:3]
        endl=something
        return(endl,tot)
    
    def m3u8download(self,u,endl,st,en,tot):
        i=st
        while i < en:
            somv=endl[0]+'.'+endl[1]+'.'+endl[2]+str(i)+'.ts'
            u.pop()
            u.append(somv)
            r=requests.get('/'.join(u))
            if (r.status_code == 200):
                for piece in r.iter_content(chunk_size=1024*250):
                    if piece:
                        if i not in self.partsbuffer.keys():
                            self.partsbuffer[i]=piece
                        else:
                            self.partsbuffer[i]+=piece
                i+=1
                sys.stdout.write('\r{} of {} parts downloaded.'.format(len(self.partsbuffer),tot+1))
            
                
                
    def download1(self,st,en):
        highest=False
        for i in range(st-1,en):
            if (self.urls[i].endswith('m3u8') or self.urls[i].endswith('m3u')):
                r=requests.get(self.urls[i])
                u=self.urls[i]
                l=r.text.split('\n')
                l.pop()
                resd={}
                for k in l:
                    if (k.startswith('#EXT')==False):
                        t=k.split('.')
                        resd[t[2]]=k
                resl=list(resd.keys())
                if highest==False:
                    reqres=input('The available resolutions are {}. If you want the highest quality in all of the following episodes, enter "highest".'.format(resl))
                if reqres=='highest':
                    highest=True
                    reqres=resl[-1]
                resurlend=resd[reqres]
                u=u.split('/')
                u.pop()
                u.append(resurlend)
                resurl='/'.join(u)
                r=requests.get(resurl)
                poi=-1
                l=r.text.split('\n')
                l.pop()
                while l[poi].startswith('#'):
                    poi-=1
                something=l[poi]
                tot=something.split('.')[2][3:]
                something=l[poi]
                tot=int(tot)
                endl=something.split('.')
                parent_dir=os.mkdir(self.name)
                file_name=self.name+' ep '+str(i+1)
                try:
                    os.mkdir(parent_dir)
                except:
                    continue
                file_path=os.path.join(parent_dir,file_name)
                with open(file_path,'wb') as f:
                    for somx in range(tot+1):
                        somv=endl[0]+'.'+endl[1]+'.'+reqres+str(somx)+'.ts'
                        u.pop()
                        u.append(somv)
                        r=requests.get('/'.join(u),stream=True)
                        print(r.status_code)
                        for piece in r.iter_content():
                            if piece:
                                f.write(piece)
                        sys.stdout.write('\r{} of {} pieces downloaded.'.format(somx,tot))
                print('done ep!',i+1)
            else:
                chunk_s=1024*1024
                r=requests.get(self.urls[i],stream=True)
                chunks=1+int(r.headers['content-length'])//chunk_s
                count=0
                print('now downloading episode',i+1,end='\n')
                with open('{}/{} ep {}.mp4'.format(self.name,self.name,i+1),'wb') as f:
                    for piece in r.iter_content(chunk_size=chunk_s):
                        if piece:
                            f.write(piece)
                            count+=1
                            sys.stdout.write('\r {}% downloaded.'.format((count/chunks)*100))
                    print('Done!')

    def download(self,st,en):
        highest=False
        start=st
        if (self.ep0 and st==1):
            start=0
        for i in range(start,en+1):
            if (self.urls[i].endswith('m3u8') or self.urls[i].endswith('m3u')):
                no_threads=8#  int(input('no of threads: '))
                u=self.urls[i]
                endl,tot=self.m3u8parse(u)
                self.partsbuffer={}
                u=u.split('/')
                sp=tot//no_threads
                tset=[Thread(target=self.m3u8download,args=(u,endl,(sp*i),(sp*(i+1))+1,tot)) for i in range(no_threads)]
                print('Now downloading episode {}.'.format(i))
                for th in tset:
                    th.start()
                for th in tset:
                    th.join()
                parent_dir=self.saveName
                file_name=self.saveName+' ep '+str(i)+'.ts'
                if not os.path.exists(parent_dir):
                    os.mkdir(parent_dir)
                file_path=os.path.join(parent_dir,file_name)
                with open(file_path,'wb') as f:
                    for i,data in sorted(self.partsbuffer.items()):
                        f.write(data)
                print('Done!')

            else:
                chunk_s=1024*1024
                r=requests.get(self.urls[i],stream=True)
                chunks=1+int(r.headers['content-length'])//chunk_s
                count=0
                parent_dir=os.path.join('Downloads',self.saveName)
                file_name=self.saveName+' ep '+str(i)+'.mp4'
                if not os.path.exists(parent_dir):
                    os.mkdir(parent_dir)
                file_path=os.path.join(parent_dir,file_name)
                print('now downloading episode',i,end='\n')
                with open(file_path,'wb') as f:
                    for piece in r.iter_content(chunk_size=chunk_s):
                        if piece:
                            f.write(piece)
                            count+=1
                            sys.stdout.write('\r {}% downloaded.'.format(round((count/chunks)*100)))
                    print('Done!')
