#!/usr/bin/env python3
"""App-owned byte/status/filesystem oracles; unchanged process harness v1."""
import csv, hashlib, io, json, os, random, subprocess, time
from pathlib import Path
from mmay_acceptance import Application
ROOT = Path(__file__).resolve().parents[1]
APP = Application(ROOT, timeout=180)
WORK = ROOT / 'build' / 'acceptance'
WORK.mkdir(parents=True, exist_ok=True)
DATA, OUTPUT = WORK/'вход ü.txt', WORK/'выход.txt'
started = time.monotonic()
engines = APP.engines(WORK, 'app', ['--allow-read', str(WORK), '--allow-write', str(WORK), '--max-heap-bytes', '67108864'])
results = []
def encoded(value): return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()+b'\n'
def err(message): return (ROOT.name+': '+message+'\n').encode()
def case(arguments, data, expected, selected=None, prepare=None, extra=None):
    def verify(engine, result):
        assert (result.stdout, result.stderr) == expected[1:], (arguments, engine, result.stdout, result.stderr, expected)
        if extra is not None: extra()
    APP.compare(engines if selected is None else selected, arguments, expected[0], data=data, verify=verify, prepare=prepare)
    results.append({'arguments':arguments, 'data_sha256':hashlib.sha256(data or b'').hexdigest(), 'status':expected[0], 'stdout_sha256':hashlib.sha256(expected[1]).hexdigest(), 'stderr':expected[2].decode()})
def output_is(value): assert OUTPUT.read_bytes() == value
def table(rows): return encoded({'version':1, 'rows':rows})
error_status, base, small = 1, ['csv-to-json'], b'a,b\n'
expected_small = table([['a','b']])
for source, rows in [(b'', []), (b'\n', [['']]), (b',', [['','']]), (b'a,b,\r\nc,d,\n', [['a','b',''],['c','d','']]), ('"Привет, 🌍","x\r\ny"\n"""",z'.encode(), [['Привет, 🌍','x\r\ny'],['"','z']]), (b'a\0b', [['a\0b']]), ('\ufeffa'.encode(), [['\ufeffa']])]:
    case([*base,'-'], source, (0,table(rows),b''))
case(['tsv-to-json','-'], b'a\t"b\tc"\n', (0,table([['a','b\tc']]),b''))
rng = random.Random(9007)
alphabet = ['a', ',', '\t', '\n', '\r', '"', 'я', '🌍', '\0', ' ']
rows = [[''.join(rng.choice(alphabet) for _ in range(rng.randrange(18))) for _ in range(8)] for _ in range(40)]
for delimiter, name in [(',', 'csv'), ('\t', 'tsv')]:
    buf = io.StringIO(newline=''); csv.writer(buf,delimiter=delimiter,quoting=csv.QUOTE_ALL,lineterminator='\n').writerows(rows)
    raw = buf.getvalue().encode()
    case([name+'-to-json','-'],raw,(0,table(rows),b''))
    case(['json-to-'+name,'-'],table(rows),(0,raw,b''))
for source, offset, message in [(b'a"',1,'Кавычка внутри некавыченного поля'),(b'"a"b',3,'После кавычки ожидается разделитель или конец строки'),(b'"a',2,'Незакрытая кавычка'),(b'a\rb',1,'Одиночный CR вне кавычек'),(b'a,b\nc',5,'Неодинаковое число столбцов'),(b'a\xff',1,'Недопустимый UTF-8')]:
    case([*base,'-'],source,(1,b'',err(f'байт {offset}: {message}')))
case([*base,'-','--max-field','2'],'я'.encode(),(0,table([['я']]),b''))
case([*base,'-','--max-field','2'],'яя'.encode(),(1,b'',err('байт 4: Превышен лимит байт поля')))
case([*base,'-','--max-rows','1'],b'a\nb',(1,b'',err('байт 3: Превышен лимит строк')))
case([*base,'-','--max-columns','1'],b'a,b',(1,b'',err('байт 3: Превышен лимит столбцов')))
for value,message in [({'version':2,'rows':[]},'Ожидается version: 1'),({'version':1,'rows':[[]]},'Строка должна содержать хотя бы одно поле'),({'version':1,'rows':[['a'],['b','c']]},'Неодинаковое число столбцов')]:
    case(['json-to-csv','-'],encoded(value),(1,b'',err(message)))
wide = 'x'*4094+'🌍"\r\nя'
case([*base,'-'],('"'+wide.replace('"','""')+'"\n').encode(),(0,table([[wide]]),b''))
large = ((b'a'*31+b',')*7+b'a'*31+b'\n')*2048
case([*base,'-'],large,(0,table([['a'*31]*8]*2048),b''))
case([],b'',(2,b'',err('Нужны РЕЖИМ и ФАЙЛ; см. --help')))
bad_data, bad_error = b'"unterminated', err('байт 13: Незакрытая кавычка')
file_output = expected_small
case([*base,'-','--max-input','1'],b'ab',(error_status,b'',err('-: standard input exceeds 1-byte limit')))
case([*base,'-','--max-input',str(len(small))],small,(0,expected_small,b''))
case([*base,'-','--wat'],b'',(2,b'',err('unknown option --wat at argument 2')))
case(['json-to-csv','-'],b'{',(1,b'',err('expected a JSON string before byte 1')))
DATA.write_bytes(small)
case([*base,str(DATA)],None,(0,file_output,b''))
case([*base,str(DATA),'--max-input','1'],None,(error_status,b'',err(str(DATA)+': file exceeds 1-byte limit')))
case([*base,'-','--output',str(OUTPUT)],small,(0,b'',b''),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(expected_small))
case([*base,'-','--output',str(OUTPUT)],bad_data,(error_status,b'',bad_error),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
case([*base,'-','--max-output','0','--output',str(OUTPUT)],small,(error_status,b'',err('Превышен лимит вывода 0 байт')),prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
missing = WORK/'missing'
case([*base,str(missing)],None,(error_status,b'',err(str(missing)+': filesystem path was not found')))
for value,message in [('-1','--max-input: допустимо 0..1048576'),('1048577','--max-input: допустимо 0..1048576'),('no','--max-input: ожидается целое число')]:
    case([*base,'-','--max-input='+value],b'',(2,b'',err(message)))
def verify_help(engine,result):
    assert not result.stderr and ROOT.name.encode() in result.stdout and b'--max-input' in result.stdout
APP.compare(engines,['--help'],0,verify=verify_help)
denied_bin = WORK/'denied'
APP.successful([APP.compiler,'build','.','--release','--output',str(denied_bin)])
denied = {'vm':[APP.compiler,'run','.','--'],'release':[str(denied_bin)]}
case([*base,str(DATA)],None,(error_status,b'',err(str(DATA)+': fs.read capability denied for '+str(DATA))),selected=denied)
case([*base,'-','--output',str(OUTPUT)],small,(error_status,b'',err('fs.write capability denied for '+str(OUTPUT))),selected=denied,prepare=lambda:OUTPUT.write_bytes(b'original'),extra=lambda:output_is(b'original'))
pipes = []
if os.name != 'nt':
    link=WORK/'link'
    if link.is_symlink(): link.unlink()
    link.symlink_to(DATA)
    case([*base,str(link)],None,(error_status,b'',err(str(link)+': symbolic links are not followed')))
    case([*base,'-','--output',str(link)],small,(error_status,b'',err('symbolic links are not followed')))
    assert DATA.read_bytes()==small
    for engine,prefix in engines.items():
        read_fd,write_fd=os.pipe(); os.close(read_fd)
        try: child=subprocess.Popen([*prefix,*base,'-'],cwd=ROOT,stdin=subprocess.PIPE,stdout=write_fd,stderr=subprocess.PIPE)
        finally: os.close(write_fd)
        _,error=child.communicate(small,timeout=180)
        assert child.returncode==error_status and (b'standard stream write failed' in error or b'standard stream flush failed' in error),(engine,child.returncode,error)
        pipes.append({'engine':engine,'status':child.returncode,'stderr':error.decode()})
assert DATA.read_bytes()==small
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*.my'))}
report_data={'schema':ROOT.name+'.acceptance/1','harness':APP.metadata(engines),'sources':sources,'cases':results,'closed_pipes':pipes,'large_bytes':len(large),'managed_heap_limit':67108864,'elapsed_seconds':time.monotonic()-started}
(WORK/'report.json').write_text(json.dumps(report_data,ensure_ascii=False,indent=2)+'\n')
print(f'{ROOT.name}: {len(results)} cases + help; VM/native Debug/Release; {len(pipes)} closed pipes; {len(large)}-byte input')
