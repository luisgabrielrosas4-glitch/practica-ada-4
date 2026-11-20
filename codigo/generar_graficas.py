import csv
import json
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
(ROOT/'graficas').mkdir(exist_ok=True)
p=json.loads((ROOT/'resultados'/'teoria.json').read_text(encoding='utf-8'))

lines=['digraph Huffman {','graph [rankdir=TB, bgcolor="white", ranksep="0.44", nodesep="0.19", splines=true];','node [fontname="Arial", fontsize=10, shape=circle, style=filled, fillcolor="#f2f5f8", color="#536679"];','edge [fontname="Arial",fontsize=10,color="#6b7c8e"];']
node_counter=[0]
def rec(node):
    i=node_counter[0];node_counter[0]+=1
    if 'caracter' in node:
        label=f'{node["caracter"]}\n{node["f"]}'
        lines.append(f'n{i} [label="{label}",shape=box,fillcolor="#e5f0f8"];')
    else:
        lines.append(f'n{i} [label="{node["f"]}"];')
        for key,bit in [('left','0'),('right','1')]:
            sub=rec(node[key]);lines.append(f'n{i} -> n{sub} [label="{bit}"];')
    return i
rec(p['arbol']);lines.append('}')
(ROOT/'graficas'/'arbol.dot').write_text('\n'.join(lines),encoding='utf-8')
subprocess.run(['dot','-Tpng','-Gdpi=175',str(ROOT/'graficas'/'arbol.dot'),'-o',str(ROOT/'graficas'/'arbol.png')],check=True)
with (ROOT/'resultados'/'benchmark.csv').open(encoding='utf-8')as f:r=list(csv.DictReader(f))
items=[x for x in r if x['caso'] in ('codigo_fuente.txt','binario_comprimido.zip','diez_millones_A.txt','mensaje.txt')]
labels=['Codigo fuente','ZIP comprimido','10 millones de A','Mensaje 36 chars']
values=[float(q['ratio_pct']) for q in items]
fig,ax=plt.subplots(figsize=(9,4.25))
ax.barh(labels,values,color=['#315f88','#7599bd','#467f69','#c38a56'])
ax.axvline(100,color='#b24c4c',ls='--',lw=1.5)
ax.set_xscale('symlog',linthresh=1)
ax.set_xlabel('Tamano comprimido respecto al original (%)')
ax.invert_yaxis()
for j,v in enumerate(values):ax.text(max(v,0.6)*1.08,j,f'{v:.5f} %',va='center',fontsize=9)
ax.set_xlim(0.00007,250)
fig.tight_layout();fig.savefig(ROOT/'graficas'/'ratios.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.3))
x=list(range(len(items)));w=.34
ax.bar([i-w/2 for i in x],[float(q['compresion_s']) for q in items],width=w,label='Compresion')
ax.bar([i+w/2 for i in x],[float(q['descompresion_s']) for q in items],width=w,label='Descompresion')
ax.set_xticks(x,labels)
ax.set_ylabel('Tiempo total del proceso (s)')
ax.legend();ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(ROOT/'graficas'/'tiempos.png',dpi=170);plt.close(fig)
