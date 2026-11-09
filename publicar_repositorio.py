"""Crea un repositorio privado nuevo. Usa la sesión existente de Git Credential Manager."""
from pathlib import Path
import argparse,json,os,subprocess,urllib.request,urllib.error

ROOT=Path(__file__).resolve().parent
NAME='bradescard-cobertura-productividad'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--crear',action='store_true');args=parser.parse_args()
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=env,timeout=30,check=True)
    fields=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    token=fields.get('password')
    if not token:raise RuntimeError('No hay sesión de GitHub disponible')
    def api(method,path,payload=None):
        req=urllib.request.Request('https://api.github.com'+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'Bradescard-setup'})
        try:
            with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code==404:return None
            raise RuntimeError('GitHub HTTP '+str(error.code)) from None
    user=api('GET','/user')['login'];existing=api('GET',f'/repos/{user}/{NAME}')
    if not args.crear:
        print(json.dumps({'cuenta':user,'nombre':NAME,'existe':existing is not None}));return
    if existing:raise RuntimeError('El repositorio ya existe; no se modifica automáticamente')
    info=api('POST','/user/repos',{'name':NAME,'private':True,'description':'Control de cobertura, plantilla, asistencia y productividad Bradescard','auto_init':False})
    def git(*args):subprocess.run(['git',*args],cwd=ROOT,env=env,check=True)
    if not (ROOT/'.git').exists():git('init','-b','main')
    git('add','--','site','tests','actualizar.py','publicar_repositorio.py','requirements.txt','README.md','.gitignore','config.example.json','ACTUALIZAR_BRADESCARD.bat')
    git('commit','-m','Crear control Bradescard con cobertura y productividad')
    git('remote','add','origin',info['clone_url']);git('push','-u','origin','main')
    print(json.dumps({'repositorio':info['html_url'],'privado':info['private']},ensure_ascii=False))

if __name__=='__main__':main()
