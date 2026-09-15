"""Testes dos riscos principais: lacunas, divisão por zero e continuidade."""
import unittest
import numpy as np
import pandas as pd
from analise_aa2 import (interpolar_lacunas_curtas, suporte_profundidade,
    resumir_intervalos, calcular_atributos, carregar_config, resumo_numerico)


class TestAnalise(unittest.TestCase):
    def test_lacunas_sem_extrapolacao(self):
        s=pd.Series([np.nan,1,np.nan,3,np.nan,np.nan,np.nan,7,np.nan],
                    index=np.arange(9)*0.15)
        r=interpolar_lacunas_curtas(s,0.5)
        self.assertAlmostEqual(r.iloc[2],2)
        self.assertTrue(r.iloc[[0,4,5,6,8]].isna().all())

    def test_distancia_real(self):
        s=pd.Series([1.,np.nan,3.],index=[0.,0.1,5.])
        self.assertTrue(np.isnan(interpolar_lacunas_curtas(s,.5).iloc[1]))

    def test_intervalos_nao_unem_falhas(self):
        d=pd.DataFrame({'POTENCIAL':[True,True,False,True,True,True],
                        'AVALIAVEL':[True]*6,'PHIE':[.2]*6,'SW':[.3]*6,
                        'VCL':[.1]*6,'SW_ACIMA_1':[False]*6},index=[0.,1.,2.,3.,10.,11.])
        c=carregar_config();t=resumir_intervalos(d,c)
        self.assertEqual(len(t),3)
        self.assertAlmostEqual(t.espessura_md_m.sum(),3.)
        self.assertAlmostEqual(suporte_profundidade(d.index)[2].sum(),4.)
        self.assertAlmostEqual(resumo_numerico(d,t)['fracao_potencial_sobre_avaliavel'],.75)

    def test_archie_caso_conhecido_e_ausentes(self):
        c=carregar_config()
        d=pd.DataFrame({'GR':[30.,30.,30.,np.nan], 'NPHI':[.2,0.,-.1,.2],
                        'RHOB':[2.3]*4,'RT':[10.]*4})
        r=calcular_atributos(d,c)
        self.assertAlmostEqual(r.PHIE.iloc[0],.2)
        self.assertAlmostEqual(r.SW.iloc[0],.5)
        self.assertTrue(r.SW.iloc[1:].isna().all())
        self.assertFalse(r.AVALIAVEL.iloc[1:].any())

    def test_zero_potencial(self):
        d=pd.DataFrame({'POTENCIAL':[False,False],'AVALIAVEL':[False,False],
                        'PHIE':[np.nan]*2,'SW':[np.nan]*2,'VCL':[np.nan]*2,
                        'SW_ACIMA_1':[False]*2},index=[0.,1.])
        t=resumir_intervalos(d,carregar_config())
        self.assertTrue(t.empty)
        self.assertIsNone(resumo_numerico(d,t)['fracao_potencial_sobre_avaliavel'])


if __name__=='__main__': unittest.main()
