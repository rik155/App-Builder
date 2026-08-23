import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

BASE=Path(__file__).parent; DATA=BASE/'data'; UP=BASE/'uploads'; DATA.mkdir(exist_ok=True); UP.mkdir(exist_ok=True)
engine=create_engine(f"sqlite:///{DATA/'reports.db'}")
with engine.begin() as c:
 c.execute(text('CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY AUTOINCREMENT,created TEXT,project TEXT,address TEXT,customer TEXT,employee TEXT,description TEXT)'))
 c.execute(text('CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY AUTOINCREMENT,report_id INTEGER,filename TEXT,note TEXT)'))
app=FastAPI(title='Projectrapport'); app.mount('/static',StaticFiles(directory=BASE/'static'),name='static'); app.mount('/uploads',StaticFiles(directory=UP),name='uploads'); templates=Jinja2Templates(directory=BASE/'templates')
@app.get('/',response_class=HTMLResponse)
def home(request:Request):
 with engine.begin() as c: rows=c.execute(text('SELECT * FROM reports ORDER BY id DESC')).mappings().all()
 return templates.TemplateResponse('index.html',{'request':request,'rows':rows})
@app.get('/nieuw',response_class=HTMLResponse)
def new(request:Request): return templates.TemplateResponse('new.html',{'request':request})
@app.post('/nieuw')
async def save(project:str=Form(...),address:str=Form(...),customer:str=Form(''),employee:str=Form(...),description:str=Form(...),photos:list[UploadFile]=File(default=[]),notes:list[str]=Form(default=[])):
 fs=[f for f in photos if f.filename]
 if len(fs)>10: raise HTTPException(400,'Maximaal 10 foto’s per rapport.')
 with engine.begin() as c:
  r=c.execute(text('INSERT INTO reports(created,project,address,customer,employee,description) VALUES(:d,:p,:a,:c,:e,:o)'),{'d':datetime.now().isoformat(timespec='minutes'),'p':project,'a':address,'c':customer,'e':employee,'o':description}); i=r.lastrowid
  for x,f in enumerate(fs):
   ext=Path(f.filename).suffix.lower() or '.jpg'; name=f'{i}_{uuid.uuid4().hex}{ext}'; (UP/name).write_bytes(await f.read()); note=notes[x] if x<len(notes) else ''
   c.execute(text('INSERT INTO photos(report_id,filename,note) VALUES(:i,:f,:n)'),{'i':i,'f':name,'n':note})
 return RedirectResponse(f'/rapport/{i}',303)
def get(i):
 with engine.begin() as c:
  r=c.execute(text('SELECT * FROM reports WHERE id=:i'),{'i':i}).mappings().first(); ps=c.execute(text('SELECT * FROM photos WHERE report_id=:i ORDER BY id'),{'i':i}).mappings().all()
 return r,ps
@app.get('/rapport/{i}',response_class=HTMLResponse)
def detail(i:int,request:Request):
 r,ps=get(i); return templates.TemplateResponse('detail.html',{'request':request,'r':r,'photos':ps})
@app.get('/rapport/{i}/pdf')
def pdf(i:int):
 r,ps=get(i); buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=16*mm,bottomMargin=16*mm); st=getSampleStyleSheet(); story=[Paragraph('PROJECTRAPPORT',st['Title']),Paragraph(f"Rapport PR-{i:05d} · {r['created'].replace('T',' ')}",st['Normal']),Spacer(1,7*mm)]
 data=[['Project',r['project']],['Adres',r['address']],['Klant',r['customer'] or '-'],['Medewerker',r['employee']]]; t=Table(data,colWidths=[35*mm,125*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eef4fb')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#cbd5e1')),('PADDING',(0,0),(-1,-1),7)])); story += [t,Spacer(1,7*mm),Paragraph('Werkzaamheden / bevindingen',st['Heading2']),Paragraph(r['description'].replace('\n','<br/>'),st['BodyText']),Spacer(1,7*mm)]
 for n,p in enumerate(ps,1):
  try: story += [Paragraph(f'Foto {n}',st['Heading2']),Image(str(UP/p['filename']),width=145*mm,height=95*mm),Spacer(1,2*mm),Paragraph(p['note'] or 'Geen toelichting.',st['BodyText']),Spacer(1,7*mm)]
  except: pass
 doc.build(story); buf.seek(0); return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'inline; filename=projectrapport-PR-{i:05d}.pdf'})
