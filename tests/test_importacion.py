import json, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import actualizar as a

class Reglas(unittest.TestCase):
    def test_clave_incluye_socio(self):
        self.assertNotEqual(a.key('BODEGA',41),a.key('PROMODA',41))
        self.assertEqual(a.key(' bodega ',201.0),a.key('BODEGA','0201'))
    def test_division_sin_base(self):
        self.assertIsNone(a.ratio(5,0))
        self.assertIsNone(a.ratio(None,10))
        self.assertEqual(a.ratio(0,10),0)
    def test_duplicados(self):
        with self.assertRaises(ValueError):a.unique([('x',1),('x',2)],'prueba')

@unittest.skipUnless((a.ROOT/'config.local.json').exists(),'Requiere fuentes locales')
class Fuentes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((a.ROOT/'config.local.json').read_text(encoding='utf-8-sig'))
        cls.d=a.build(cls.config)
    def test_universo_y_columnas(self):
        d=self.d
        self.assertEqual(len(d['tiendas']),18)
        self.assertEqual(len(d['productividad']['personas']),20)
        self.assertTrue(all('numero' in s and 'socio' in s for s in d['tiendas']))
        self.assertEqual(len({s['id'] for s in d['tiendas']}),len(d['tiendas']))
    def test_cortes(self):
        d=self.d
        self.assertTrue(all(r['fecha'][:7]==d['corteAsistencia'][:7] and r['fecha']<=d['corteAsistencia'] for r in d['asistencia']))
        self.assertEqual(d['productividad']['periodoTramites'][1],'2026-11-08')
        self.assertEqual(d['productividad']['periodoActivaciones'][1],'2026-11-07')
    def test_totales_bi_con_base(self):
        rr=a.rows(self.config['bi'],'BI_BETTER'); ids={r['id'] for r in self.d['tiendas']}
        raw=[r for r in rr[7:] if r[0] and r[1] and a.key(r[0],r[1]) in ids]
        out=self.d['productividad']['tiendas']
        for field,col in [('tramites',8),('aprobadas',16),('activadas',26),('metaDia',27),('metaMes',29),('amd',40)]:
            self.assertEqual(sum(r[col] or 0 for r in raw),sum(r.get(field) or 0 for r in out),field)
    def test_staff_y_nrt_no_se_suman(self):
        p=self.d['productividad'];raw=a.rows(self.config['txh'],'Staff BETTER')[11:]
        self.assertEqual(sum(r['aprobadas'] for r in p['personas']),sum(r[15] or 0 for r in raw if r[1]))
        nrt=a.rows(self.config['nrt'],'ProductividadPromotor')[2:]
        self.assertEqual(sum(r['tramites'] for r in p['nrt']),sum(r[28] for r in nrt if r[0]))
    def test_sin_datos_sensibles_innecesarios(self):
        for p in self.d['plantilla']:
            self.assertEqual(set(p),{'store','nombre','perfil','estatus','jornada','horario','corte'})

if __name__=='__main__':unittest.main()
