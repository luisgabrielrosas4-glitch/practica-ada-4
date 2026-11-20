import csv
import hashlib
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'codigo' / 'huffman.cpp'
EXEC = BASE / 'codigo' / ('huffman.exe' if sys.platform == 'win32' else 'huffman')
PRUEBAS = BASE / 'pruebas'
RESULTADOS = BASE / 'resultados'
RESULTADOS.mkdir(parents=True, exist_ok=True)
PRUEBAS.mkdir(parents=True, exist_ok=True)

if not EXEC.exists():
    subprocess.run(['g++', '-std=c++17', '-O2', str(SOURCE), '-o', str(EXEC)], check=True)

src = SOURCE.read_bytes()
(PRUEBAS / 'codigo_fuente.txt').write_bytes(src * 30)
(PRUEBAS / 'mensaje.txt').write_bytes(b'ABRACADABRA_ALGORITMO_AVANZADO_ESCOM')

aleatorio = PRUEBAS / 'aleatorio.bin'
if not aleatorio.exists():
    aleatorio.write_bytes(os.urandom(1024 * 1024))
with zipfile.ZipFile(PRUEBAS / 'binario_comprimido.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(aleatorio, arcname='aleatorio.bin')

with (PRUEBAS / 'diez_millones_A.txt').open('wb') as f:
    chunk = b'A' * 1000000
    for _ in range(10):
        f.write(chunk)

(PRUEBAS / 'vacio.dat').write_bytes(b'')
(PRUEBAS / 'un_byte.dat').write_bytes(b'Z')
(PRUEBAS / 'relleno.dat').write_bytes(b'ABA')
(PRUEBAS / 'alfabeto_completo.dat').write_bytes(bytes(range(256)))

def run_mode(mode, source, destination):
    comando = [str(EXEC), mode, str(source), str(destination)]
    start = time.perf_counter()
    if sys.platform != 'win32' and Path('/usr/bin/time').exists():
        result = subprocess.run(['/usr/bin/time','-f','PICO_KIB=%M'] + comando,
                                text=True, capture_output=True, timeout=120, check=False)
        peak_line = next((x for x in result.stderr.splitlines() if x.startswith('PICO_KIB=')), None)
        memory = int(peak_line.split('=')[1]) / 1024 if peak_line else -1
        if result.returncode:
            raise RuntimeError(result.stderr)
    else:
        try:
            import psutil
        except ImportError:
            raise RuntimeError('Instala psutil para medir memoria: pip install psutil')
        process = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        watched = psutil.Process(process.pid)
        peak = 0
        while process.poll() is None:
            try:
                peak = max(peak, watched.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            time.sleep(0.001)
        stdout, stderr = process.communicate(timeout=120)
        if process.returncode:
            raise RuntimeError(stderr.decode(errors='replace'))
        memory = peak / 1048576
    return time.perf_counter() - start, memory

rows = []
for caso in ('codigo_fuente.txt', 'binario_comprimido.zip', 'diez_millones_A.txt',
             'vacio.dat', 'un_byte.dat', 'relleno.dat',
             'alfabeto_completo.dat', 'mensaje.txt'):
    before = PRUEBAS / caso
    packed = PRUEBAS / (caso + '.huf')
    after = PRUEBAS / (caso + '.restaurado')
    ct, cm = run_mode('c', before, packed)
    dt, dm = run_mode('d', packed, after)
    hash_in = hashlib.sha256(before.read_bytes()).hexdigest()
    hash_out = hashlib.sha256(after.read_bytes()).hexdigest()
    size_in, size_out = before.stat().st_size, packed.stat().st_size
    rows.append(dict(caso=caso,bytes_originales=size_in,bytes_comprimidos=size_out,
                     ratio_pct=round(100*size_out/size_in,5) if size_in else 'N/A',
                     compresion_s=ct,descompresion_s=dt,
                     memoria_compresion_MiB=round(cm,3),memoria_descompresion_MiB=round(dm,3),
                     identico='si' if hash_in==hash_out else 'no',sha256=hash_in))
    assert hash_in == hash_out, caso
    print(f'{caso}: {size_in} => {size_out}, ratio={rows[-1]["ratio_pct"]}%, correcto=si',flush=True)

with (RESULTADOS / 'benchmark.csv').open('w', newline='', encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

bad=PRUEBAS/'cabecera_corrupta.dat'
bad.write_bytes(b'XXXX'+b'\0'*16)
try:
    subprocess.run([str(EXEC),'d',str(bad),str(PRUEBAS/'corrupta.out')],check=True,capture_output=True)
    raise AssertionError('Acepto cabecera corrupta')
except subprocess.CalledProcessError:
    print('Cabecera invalida rechazada: si')
print('Pruebas completadas:',len(rows))
