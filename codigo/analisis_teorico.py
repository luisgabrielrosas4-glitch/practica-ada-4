import collections
import heapq
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent
(BASE/'resultados').mkdir(parents=True,exist_ok=True)
MENSAJE='ABRACADABRA_ALGORITMO_AVANZADO_ESCOM'
freq=collections.Counter(MENSAJE)
heap=[]
for s,n in sorted(freq.items()):
    heap.append((n,ord(s),ord(s),{'caracter':s,'f':n}))
heapq.heapify(heap)
pasos=[]
count=256
while len(heap)>1:
    a=heapq.heappop(heap); b=heapq.heappop(heap)
    label=lambda n: ''.join(sorted(x for x in n['chars'])) if 'chars' in n else n['caracter']
    nodes={'f':a[0]+b[0],'left':a[3],'right':b[3], 'chars': ''.join(sorted(set(label(a[3])+label(b[3]))))}
    heapq.heappush(heap,(a[0]+b[0],min(a[1],b[1]),count,nodes));count+=1
    def shown(t):
        return f'{label(t[3])}:{t[0]}'
    bosque=sorted(heap)
    pasos.append(dict(paso=len(pasos)+1,unidos=f'{shown(a)} + {shown(b)}',nuevo=f'{label(nodes)}:{nodes["f"]}',bosque=' | '.join(shown(q) for q in bosque)))
root=heap[0][3]
code={}
def make(node, prefix):
    if 'caracter' in node:
        code[node['caracter']]=prefix if prefix else '0'
    else:
        make(node['left'],prefix+'0');make(node['right'],prefix+'1')
make(root,'')
H=-sum((n/len(MENSAJE))*math.log2(n/len(MENSAJE)) for n in freq.values())
L=sum(n*len(code[c]) for c,n in freq.items())/len(MENSAJE)
B=sum(n*len(code[c]) for c,n in freq.items())
S=len(freq)
summary={'mensaje':MENSAJE,'longitud':len(MENSAJE),'simbolos':S,'frecuencias':[{'caracter':c,'frecuencia':n,'p':n/len(MENSAJE),'codigo':code[c],'bits':len(code[c])}for c,n in sorted(freq.items())], 'entropia':H,'longitud_promedio':L,'bits_codificados':B,'bytes_datos':math.ceil(B/8),'sobrecarga_tabla_bytes':1024,'arbol_bits':10*S-1,'arbol_bytes':math.ceil((10*S-1)/8),'bosque':pasos, 'arbol':root}
(BASE/'resultados'/'teoria.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('symbols',S,'H',H,'L',L,'bits',B,'bytes',math.ceil(B/8),'tree',10*S-1,'bytes',math.ceil((10*S-1)/8),'ineq',H<=L<H+1)
for r in summary['frecuencias']:print(repr(r['caracter']),r['frecuencia'],round(r['p'],6),r['codigo'])
for p in pasos:print(p['paso'],p['unidos'],'->',p['nuevo'])
