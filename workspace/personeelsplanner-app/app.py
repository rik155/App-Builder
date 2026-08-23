from datetime import date,datetime,timedelta
from pathlib import Path
from fastapi import FastAPI,Request,Form
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine,text
BASE=Path(__file__).parent; DATA=BASE/'data'; DATA.mkdir(exist_ok=True); engine=create_engine(f"sqlite:///{DATA/'planner.db'}")
with engine.begin() as c:
 c.execute(text('CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,phone TEXT,active INTEGER DEFAULT 1)'))
 c.execute(text('CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,work_date TEXT,employee_id INTEGER,project TEXT,address TEXT,start_time TEXT,end_time TEXT,contact TEXT,phone TEXT,notes TEXT,status TEXT DEFAULT "planned")'))
app=FastAPI(title='Werkplan'); app.mount('/static',StaticFiles(directory=BASE/'static'),name='static'); templates=Jinja2Templates(directory=BASE/'templates')
def days(start=None):
 d=start or date.today(); d=d-timedelta(days=d.weekday()); return [d+timedelta(days=i) for i in range(5)]
def employees():
 with engine.begin() as c:return c.execute(text('SELECT * FROM employees WHERE active=1 ORDER BY name')).mappings().all()
def jobs_for(ds):
 with engine.begin() as c:return c.execute(text('SELECT j.*,e.name employee FROM jobs j JOIN employees e ON e.id=j.employee_id WHERE work_date IN :ds ORDER BY work_date,start_time'),{'ds':tuple(x.isoformat() for x in ds)}).mappings().all()
@app.get('/',response_class=HTMLResponse)
def home(request:Request,week:str=''):
 try:s=date.fromisoformat(week) if week else date.today()
 except:s=date.today()
 ds=days(s); return templates.TemplateResponse('index.html',{'request':request,'days':ds,'employees':employees(),'jobs':jobs_for(ds),'today':date.today()})
@app.get('/nieuw',response_class=HTMLResponse)
def new(request:Request,day:str=''):
 return templates.TemplateResponse('new.html',{'request':request,'employees':employees(),'day':day or date.today().isoformat()})
@app.post('/nieuw')
def save(work_date:str=Form(...),employee_id:int=Form(...),project:str=Form(...),address:str=Form(...),start_time:str=Form('07:30'),end_time:str=Form('16:00'),contact:str=Form(''),phone:str=Form(''),notes:str=Form('')):
 with engine.begin() as c:c.execute(text('INSERT INTO jobs(work_date,employee_id,project,address,start_time,end_time,contact,phone,notes) VALUES(:d,:e,:p,:a,:s,:t,:c,:ph,:n)'),{'d':work_date,'e':employee_id,'p':project,'a':address,'s':start_time,'t':end_time,'c':contact,'ph':phone,'n':notes})
 return RedirectResponse('/',303)
@app.get('/medewerkers',response_class=HTMLResponse)
def staff(request:Request):return templates.TemplateResponse('staff.html',{'request':request,'employees':employees()})
@app.post('/medewerkers')
def staff_add(name:str=Form(...),phone:str=Form('')):
 with engine.begin() as c:c.execute(text('INSERT INTO employees(name,phone) VALUES(:n,:p)'),{'n':name,'p':phone})
 return RedirectResponse('/medewerkers',303)
@app.get('/vandaag/{employee_id}',response_class=HTMLResponse)
def today(employee_id:int,request:Request):
 with engine.begin() as c:
  e=c.execute(text('SELECT * FROM employees WHERE id=:i'),{'i':employee_id}).mappings().first(); js=c.execute(text('SELECT * FROM jobs WHERE employee_id=:i AND work_date=:d ORDER BY start_time'),{'i':employee_id,'d':date.today().isoformat()}).mappings().all()
 return templates.TemplateResponse('today.html',{'request':request,'e':e,'jobs':js,'today':date.today()})
