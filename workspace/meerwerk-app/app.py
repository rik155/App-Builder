import os, uuid, base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

BASE=Path(__file__).parent
DATA=BASE/'data'; UP=BASE/'uploads'; DATA.mkdir(exist_ok=True); UP.mkdir(exist_ok=True)
engine=create_engine(f"sqlite:///{DATA/'meerwerk.db'}")
with engine.begin() as c:
 c.execute(text('''CREATE TABLE IF NOT EXISTS meerwerk(id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, customer_name TEXT, address TEXT, phone TEXT, email TEXT, description TEXT, price REAL, vat_included INTEGER, signature TEXT)'''))
 c.execute(text('''CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY AUTOINCREMENT, meerwerk_id INTEGER, filename TEXT)'''))
app=FastAPI(title='Meerwerk')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static'); app.mount('/uploads',StaticFiles(directory=UP),name='uploads')
templates=Jinja2Templates(directory=BASE/'templates')

def get_one(i):
 with engine.begin() as c:
  row=c.execute(text('SELECT * FROM meerwerk WHERE id=:i'),{'i':i}).mappings().first()
  photos=c.execute(text('SELECT * FROM photos WHERE meerwerk_id=:i'),{'i':i}).mappings().all()
 return row,photos

@app.get('/',response_class=HTMLResponse)
def home(request:Request):
 with engine.begin() as c: rows=c.execute(text('SELECT * FROM meerwerk ORDER BY id DESC')).mappings().all()
 return templates.TemplateResponse('index.html',{'request':request,'rows':rows})
@app.get('/nieuw',response_class=HTMLResponse)
def new(request:Request): return templates.TemplateResponse('new.html',{'request':request})
@app.post('/nieuw')
async def save(customer_name:str=Form(...),address:str=Form(...),phone:str=Form(...),email:str=Form(...),description:str=Form(...),price:float=Form(...),vat_included:str=Form('1'),signature:str=Form(...),photos:list[UploadFile]=File(default=[])):
 with engine.begin() as c:
  r=c.execute(text('INSERT INTO meerwerk(created,customer_name,address,phone,email,description,price,vat_included,signature) VALUES(:d,:n,:a,:p,:e,:w,:pr,:v,:s)'),{'d':datetime.now().isoformat(timespec='minutes'),'n':customer_name,'a':address,'p':phone,'e':email,'w':description,'pr':price,'v':1 if vat_included=='1' else 0,'s':signature})
  i=r.lastrowid
  for f in photos:
   if not f.filename: continue
   ext=Path(f.filename).suffix.lower() or '.jpg'; name=f'{i}_{uuid.uuid4().hex}{ext}'; (UP/name).write_bytes(await f.read())
   c.execute(text('INSERT INTO photos(meerwerk_id,filename) VALUES(:i,:f)'),{'i':i,'f':name})
 return RedirectResponse(f'/meerwerk/{i}',303)
@app.get('/meerwerk/{i}',response_class=HTMLResponse)
def detail(i:int,request:Request):
 row,photos=get_one(i); return templates.TemplateResponse('detail.html',{'request':request,'m':row,'photos':photos})
@app.get('/meerwerk/{i}/pdf')
def pdf(i:int):
 m,photos=get_one(i); buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
 styles=getSampleStyleSheet(); story=[]
 story += [Paragraph('MEERWERK AKKOORD',styles['Title']),Paragraph(f"Meerwerkbon MW-{m['id']:05d} · {m['created'].replace('T',' ')}",styles['Normal']),Spacer(1,8*mm)]
 data=[['Klant',m['customer_name']],['Adres',m['address']],['Telefoon',m['phone']],['E-mail',m['email']]]
 t=Table(data,colWidths=[35*mm,120*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f1f5f9')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#cbd5e1')),('PADDING',(0,0),(-1,-1),7)])); story += [t,Spacer(1,7*mm),Paragraph('Omschrijving meerwerk',styles['Heading2']),Paragraph(m['description'].replace('\n','<br/>'),styles['BodyText']),Spacer(1,7*mm)]
 if photos:
  story.append(Paragraph('Foto’s van het meerwerk',styles['Heading2']))
  imgs=[]
  for p in photos:
   try:
    im=Image(str(UP/p['filename']),width=70*mm,height=52*mm); imgs.append(im)
   except: pass
  for x in range(0,len(imgs),2): story += [Table([imgs[x:x+2]],colWidths=[78*mm,78*mm]),Spacer(1,4*mm)]
 story += [Spacer(1,5*mm),Table([['Totaal meerwerk',f"€ {m['price']:,.2f}".replace(',','X').replace('.',',').replace('X','.') + (' incl. btw' if m['vat_included'] else ' excl. btw')]],colWidths=[90*mm,65*mm],style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#111827')),('TEXTCOLOR',(0,0),(-1,-1),colors.white),('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),13),('PADDING',(0,0),(-1,-1),10)]),Spacer(1,8*mm),Paragraph('Akkoord opdrachtgever',styles['Heading2']),Paragraph('De opdrachtgever verklaart bovenstaande werkzaamheden en prijs te hebben gezien en geeft akkoord voor uitvoering van dit meerwerk.',styles['BodyText']),Spacer(1,5*mm)]
 if m['signature'] and ',' in m['signature']:
  try:
   raw=base64.b64decode(m['signature'].split(',',1)[1]); story.append(Image(BytesIO(raw),width=65*mm,height=25*mm))
  except: pass
 story += [Paragraph(f"Ondertekend door: {m['customer_name']}",styles['Normal'])]
 doc.build(story); buf.seek(0); return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'inline; filename=meerwerk-MW-{i:05d}.pdf'})
