"""Importa las cinco fuentes Bradescard sin modificar los Excel originales."""
from pathlib import Path
import argparse, calendar, collections, datetime as dt, json, re, sys, unicodedata

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.deps'))
from openpyxl import load_workbook

def norm(v):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(v or '')) if not unicodedata.combining(c)).upper().split())

def ident(v):
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v or '').strip().lstrip('0') or '0'

def key(socio, tienda): return norm(socio) + ':' + ident(tienda)

def ratio(a, b): return a / b if a is not None and b is not None and b > 0 else None

def rows(path, sheet):
    with_book = load_workbook(path, read_only=True, data_only=True)
    try: return list(with_book[sheet].values)
    finally: with_book.close()

def unique(items, label):
    out = {}
    for k, v in items:
        if k in out: raise ValueError(f'Clave duplicada en {label}: {k}')
        out[k] = v
    return out

def base(path):
    rr = rows(path, 'BASE BRADESCARD'); h = [norm(x) for x in rr[0]]
    result = []
    for r in rr[1:]:
        def get(n): return r[h.index(n)]
        if norm(get('PROYECTO')) != 'BRADESCARD': continue
        pro, sub, total = (int(get(n) or 0) for n in ['PROMOTORES REQUERIDOS','SUBLIDER','TOTAL DE PLANTILLA AUTORIZA'])
        if min(pro, sub, total) < 0 or pro + sub != total: raise ValueError('Plantilla inconsistente')
        socio, num = norm(get('SOCIO')), ident(get('NUMERO DE TIENDA/DETERMINANTE'))
        result.append((key(socio,num), dict(id=key(socio,num), numero=num, socio=socio,
            tienda=get('TIENDA'), region=get('REGION ADMINISTRATIVA'), estado=get('ESTADO'),
            ciudad=get('CIUDAD'), grupo=get('CATEGORIA/GRUPO'), estatus=norm(get('ESTATUS')),
            promotores=pro, sublideres=sub, requerida=total)))
    return unique(result, 'base')

def attendance(path, cutoff, stores):
    from pyxlsb import open_workbook
    months = dict(zip('ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC'.split(),range(1,13)))
    people, records, conflicts, unmatched = {}, {}, 0, set()
    with open_workbook(str(path)) as book:
        weeks = []
        for name in book.sheets:
            m = re.search(r'ASISTENCIA DEL .* AL (\d+) (?:DE )?([A-Z]{3})', norm(name))
            if not m: continue
            end = dt.date(cutoff.year, months[m[2]], int(m[1]))
            if end > cutoff + dt.timedelta(days=6): continue
            weeks.append((end,name))
        if not weeks: raise ValueError('No hay semanas de asistencia válidas')
        for end,name in sorted(weeks, reverse=True):
            with book.get_sheet(name) as sheet:
                header = None; seen = {}
                for raw in sheet.rows(sparse=True):
                    r = {c.c:c.v for c in raw}
                    if header is None:
                        if 'NOMBRE COMPLETO' not in [norm(v) for v in r.values()]: continue
                        header = {norm(v):i for i,v in r.items() if isinstance(v,str)}
                        daycols = [(i,int(v)) for i,v in r.items() if isinstance(v,(int,float)) and 1<=v<=31 and norm(r.get(i+1))=='ENTR']
                        dates = [(col,end-dt.timedelta(days=len(daycols)-1-j)) for j,(col,_) in enumerate(daycols)]
                        if any(day != d.day for (_,day),(_,d) in zip(daycols,dates)): raise ValueError('Fechas inconsistentes: '+name)
                        continue
                    def get(n): return r.get(header.get(n))
                    person_name = get('NOMBRE COMPLETO')
                    if not person_name: continue
                    store = key(get('SOCIO'),get('NUMERO DE TIENDA'))
                    if store not in stores: unmatched.add(store); continue
                    identity = (ident(get('NUM DE NOMINA')),norm(person_name))
                    signature = (store,norm(get('PERFIL DE PUESTO BANCO')),norm(get('ESTATUS')))
                    if identity in seen:
                        if seen[identity] != r: raise ValueError('Persona duplicada contradictoria en '+name)
                        continue
                    seen[identity] = r
                    if identity not in people:
                        people[identity] = dict(store=store,nombre=str(person_name).strip(),perfil=signature[1],estatus=signature[2],
                            jornada=get('JORNADA'),horario=get('HORARIO'),corte=end.isoformat())
                    for col,day in dates:
                        if day > cutoff or day.strftime('%Y-%m') != cutoff.strftime('%Y-%m'): continue
                        code = norm(r.get(col)) or 'SIN CAPTURA'
                        k=(identity,day.isoformat())
                        value = dict(fecha=day.isoformat(),store=store,perfil=signature[1],codigo=code)
                        if k in records:
                            if records[k]['codigo'] != code: conflicts += 1
                            continue
                        records[k]=value
    counted=collections.Counter((v['fecha'],v['store'],v['perfil'],v['codigo']) for v in records.values())
    return list(people.values()), [dict(fecha=k[0],store=k[1],perfil=k[2],codigo=k[3],cantidad=v) for k,v in sorted(counted.items())], dict(hojas=len(weeks),diferencias=conflicts,tiendasFueraBase=sorted(unmatched))

def productivity(bi_path, txh_path, nrt_path, stores):
    raw=rows(bi_path,'BI_BETTER'); header=[norm(v) for v in raw[6]]
    def period(text):
        dates=re.findall(r'\d{2}[-/]\d{2}[-/]\d{4}',text)
        if len(dates)<2: raise ValueError('Falta periodo explícito en productividad')
        return [dt.datetime.strptime(d.replace('/','-'),'%d-%m-%Y').date().isoformat() for d in dates[:2]]
    tramites_period=period(str(raw[4][3])); activation_period=period(str(raw[5][3]))
    bi={}; outside=[]
    for r in raw[7:]:
        if not r[0] or not r[1]: continue
        k=key(r[0],r[1])
        if k not in stores:
            outside.append(k); continue
        def get(n): return r[header.index(norm(n))]
        if k in bi: raise ValueError('Tienda duplicada en BI: '+k)
        bi[k]=dict(ticket=get('Ticket Estimado'),conversion=get('Tasa de conversión'),tramites=get('Trámites Totales'),
            aprobadas=get('Tarjeta Aprobada Total'),tasaAprobacion=get('Tasa de aprobación PLCC & VISA'),
            activadas=get('Activación Total'),metaDia=get('Meta al dia'),alcanceDia=get('Alcance al dia'),
            metaMes=get('Meta Mensual_ACT'),alcanceMes=get('Alcance Mensual'),amd=get('AMD PLCC & VISA'),
            amdPct=get('% AMD PLCC & VISA'),grupoBI=get('Grupo'),
            correctosPV=(get('Trámites correctos Visa') or 0)+(get('Trámites correctos PLCC') or 0),
            aprobadasPV=get('Tarjeta Aprobada PLCC + VISA'))
    tx=rows(txh_path,'Tiendas BETTER'); txperiod=period(str(tx[7][4]))
    if txperiod != tramites_period: raise ValueError('BI y TXH tienen periodos de trámites diferentes')
    txmap=unique([(key(r[1],r[2]),r) for r in tx[11:] if r[1] and r[2]],'TXH tiendas')
    store_rows=[]
    for k,s in stores.items():
        b=bi.get(k,{}); t=txmap.get(k)
        store_rows.append(dict(s,**b,txh=t[6] if t else None,fuenteBI=k in bi,fuenteTXH=t is not None))
    staff_rows=[]
    for r in rows(txh_path,'Staff BETTER')[11:]:
        if not r[1] or not r[5]: continue
        k=key(r[1],r[2]); s=stores.get(k)
        if s is None: continue
        staff_rows.append(dict(s,nombre=r[5],perfil=r[6],estatusPersona=r[7],txh=r[11],activadas=r[12],
            correctos=r[14],aprobadas=r[15],tasaAprobacion=ratio(r[15],r[14]),amdPct=r[16],
            diarios=[dict(fecha=(dt.date.fromisoformat(txperiod[0])+dt.timedelta(days=i)).isoformat(),tramites=r[17+2*i],txh=r[18+2*i]) for i in range((dt.date.fromisoformat(txperiod[1])-dt.date.fromisoformat(txperiod[0])).days+1)]))
    nrt=[]; nrt_date=None
    for r in rows(nrt_path,'Diccionario'):
        m=re.search(r'Fecha del reporte: (\d{4}-\d{2}-\d{2})',str(r[0]))
        if m: nrt_date=m[1]
    if not nrt_date: raise ValueError('NRT sin fecha explícita')
    for r in rows(nrt_path,'ProductividadPromotor')[2:]:
        if not r[0]: continue
        k=key(r[0],r[1]); s=stores.get(k)
        if s is None: continue
        nrt.append(dict(s,nombre=r[6],perfil=r[7],tramites=r[28],correctos=r[29],aprobadas=r[31],
            rechazadas=r[32],enProceso=r[33],embosadas=r[35],tasaAprobacion=r[36]))
    return dict(tiendas=store_rows,personas=staff_rows,nrt=nrt,periodoTramites=tramites_period,
        periodoActivaciones=activation_period,fechaNRT=nrt_date,tiendasBIFueraBase=outside)

def build(config):
    def path(k):
        p=Path(config[k]); return p if p.is_absolute() else ROOT/p
    cutoff=dt.date.fromisoformat(config['corte_asistencia'])
    stores=base(path('base')); people,daily,quality=attendance(path('asistencia'),cutoff,stores)
    prod=productivity(path('bi'),path('txh'),path('nrt'),stores)
    if prod['periodoTramites'][1][:7] != cutoff.strftime('%Y-%m'): raise ValueError('Asistencia y productividad no pertenecen al mismo mes')
    return dict(actualizado=dt.datetime.now(dt.timezone.utc).isoformat(),corteAsistencia=cutoff.isoformat(),
        tiendas=list(stores.values()),plantilla=people,asistencia=daily,calidad=quality,productividad=prod,
        fuentes={k:path(k).name for k in ['base','asistencia','bi','txh','nrt']})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',default=str(ROOT/'config.local.json'));args=parser.parse_args()
    data=build(json.loads(Path(args.config).read_text(encoding='utf-8-sig')))
    target=ROOT/'site'/'data.js';target.parent.mkdir(exist_ok=True)
    temp=target.with_suffix('.tmp');temp.write_text('window.BRADESCARD = '+json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')+';\n',encoding='utf-8');temp.replace(target)
    print(json.dumps(dict(tiendas=len(data['tiendas']),personas=len(data['plantilla']),productividadPersonas=len(data['productividad']['personas']),calidad=data['calidad']),ensure_ascii=False))

if __name__=='__main__': main()
