from vidstreaming import server as srv
import os

sterm=input('enter name or keywords ')
st=int(input('enter starting episode '))
en=int(input('enter ending episode '))

obj=srv(sterm)

obj.get_ep(st,en)
print('done')
if not os.path.exists('Downloads'):
    os.mkdir('Downloads')
obj.download(st,en)