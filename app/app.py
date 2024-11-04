from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from agriculture.user.database import SessionLocal, get_db
from agriculture.user.models import User
from pydantic import BaseModel, EmailStr
from agriculture.user.database import engine, Base

# Crear todas las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)
app = FastAPI()


# Path to the templates folder
templates = Jinja2Templates(directory="templates")


# Esquemas de Pydantic para validar los datos de entrada
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Endpoints

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

# Endpoint para mostrar la página de registro
@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Ruta para procesar el registro de un usuario
@app.post("/register", response_class=HTMLResponse)
async def register_user(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        hashed_password: str = Form(...),
        confirm_password: str = Form(...),  # Campo de confirmación de contraseña
        db: Session = Depends(get_db)
):
    # Validación de coincidencia de contraseñas
    if hashed_password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request,
                                                            "error": "Passwords do not match."})

    # Crear el nuevo usuario
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return templates.TemplateResponse("login.html", {"request": request,
                                                         "message": "User created successfully! Please log in."})
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("register.html", {"request": request,
                                                            "error": "The email is already registered. Please use another one."})
# Ruta para iniciar sesión
@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()

    if not db_user or db_user.hashed_password != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password."})

    # Redirecciona a la página de inicio en caso de éxito
    return templates.TemplateResponse("index.html", {"request": request, "message": "Succesful login"})

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

app.mount("/styles", StaticFiles(directory="styles"), name="styles2")

app.mount("/images", StaticFiles(directory="images"), name="Miguel")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")
app.mount("/images", StaticFiles(directory="images"), name="Camila")
app.mount("/images", StaticFiles(directory="images"), name="Nestor")