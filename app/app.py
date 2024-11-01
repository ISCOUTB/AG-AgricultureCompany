from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Path to the templates folder
templates = Jinja2Templates(directory="templates")


# Home page - Index
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# About Us page
@app.get("/about_us", response_class=HTMLResponse)
async def about_us(request: Request):
    return templates.TemplateResponse("about_us.html", {"request": request})


# Contact Us page
@app.get("/contact", response_class=HTMLResponse)
async def contact_us(request: Request):
    return templates.TemplateResponse("contact_us.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/cultivation", response_class=HTMLResponse)
async def cultivation(request: Request):
    return templates.TemplateResponse("cultivation.html", {"request": request})

@app.get("/crop", response_class=HTMLResponse)
async def crop(request: Request):
    return templates.TemplateResponse("crop.html", {"request": request})

@app.get("/harvested", response_class=HTMLResponse)
async def harvested(request: Request):
    return templates.TemplateResponse("harvested.html", {"request": request})

@app.get("/silocreation", response_class=HTMLResponse)
async def silocreation(request: Request):
    return templates.TemplateResponse("silocreation.html", {"request": request})

@app.get("/productcreation", response_class=HTMLResponse)
async def productcreation(request: Request):
    return templates.TemplateResponse("productcreation.html", {"request": request})

@app.get("/silo", response_class=HTMLResponse)
async def silo(request: Request):
    return templates.TemplateResponse("silo.html", {"request": request})

app.mount("/styles", StaticFiles(directory="styles"), name="login")

