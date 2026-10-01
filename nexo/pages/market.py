import pandas as pd
import streamlit as st
from nexo.data.catalog import OCCUPATIONS,JOB_COUNTS,NEARBY_BY_OCC
from nexo.ui.theme import header

def render(ctx):
    header('MERCADO','Inteligência do mercado','Onde a demanda encontra escassez de competências.')
    rows=[]; gaps={'O001':2.1,'O002':2.8,'O003':3.4,'O004':.8,'O005':2.2,'O006':1.7,'O007':2.4,'O008':1.1}
    for oid,name in OCCUPATIONS: rows.append([name,JOB_COUNTS[oid],NEARBY_BY_OCC[oid],gaps[oid],'Alta' if oid in {'O001','O002','O003'} else 'Média'])
    st.dataframe(pd.DataFrame(rows,columns=['Ocupação','Demanda','Pessoas próximas','Gap médio','Prioridade']),use_container_width=True,hide_index=True)
