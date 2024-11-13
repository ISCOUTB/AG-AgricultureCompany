from datetime import date

from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from agriculture.user.database import SessionLocal, get_db, engine, Base
from agriculture.user.models import User, Cultivo, Cosecha, Silo, PuntoVenta, Venta, Vehiculo, Encargo
from pydantic import BaseModel, EmailStr

# Crear todas las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)
app = FastAPI()


# Path to the templates folder
templates = Jinja2Templates(directory="templates")


# Función para verificar si el usuario está autenticado
def get_current_user_id(request: Request):
    return request.cookies.get("user_id")

def is_logged_in(request: Request):
    return get_current_user_id(request) is not None

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
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("index.html", {"request": request, "user_logged_in": user_logged_in})

# About Us page
@app.get("/about_us", response_class=HTMLResponse)
async def about_us(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("about_us.html", {"request": request, "user_logged_in": user_logged_in})

# Contact Us page
@app.get("/contact", response_class=HTMLResponse)
async def contact_us(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("contact_us.html", {"request": request, "user_logged_in": user_logged_in})

# Página de login
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Registro de usuario
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
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if hashed_password != confirm_password:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Passwords do not match."})

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
        return templates.TemplateResponse("login.html", {"request": request, "message": "User created successfully! Please log in."})
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse("register.html", {"request": request, "error": "The email is already registered. Please use another one."})

# Ruta para iniciar sesión
@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()

    if not db_user or db_user.hashed_password != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password."})

    # Si las credenciales son correctas, guarda el user_id en una cookie de sesión
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(db_user.id), httponly=True)
    return response

# Endpoint para cerrar sesión
@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("user_id")  # Elimina la cookie de user_id para cerrar sesión
    return response

# Perfil del usuario
@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")  # Redirige a login si no está autenticado

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return RedirectResponse(url="/login")  # Redirige a login si el usuario no existe

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_logged_in": True,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "email": db_user.email,
        "phone": db_user.phone
    })

# Endpoint para registrar cultivo
@app.post("/crop_detail", response_class=HTMLResponse)
async def register_crop(
    request: Request,
    id_crop: int = Form(...),
    crop_type: str = Form(...),
    area: float = Form(...),
    planting_date: date = Form(...),
    amount: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        new_crop = Cultivo(
            ID_Cultivo=id_crop,
            Tipo=crop_type,
            Area_cultivada=area,
            Fecha_siembra=planting_date,
            Estado_crecimiento="Inicial",  # Valor de ejemplo, puedes modificar según necesidad
            Necesidades_tratamiento="",
            user_id=user_id
        )
        db.add(new_crop)
        db.commit()
        db.refresh(new_crop)
        return templates.TemplateResponse("crop.html", {"request": request, "message": "Crop registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("crop.html", {"request": request, "error": f"Failed to register crop. Error: {str(e)}"})

# Endpoint para registrar un silo
@app.post("/silo_detail", response_class=HTMLResponse)
async def register_silo(
    request: Request,
    nombre: str = Form(...),
    capacidad: float = Form(...),
    contenido: float = Form(...),
    id_cosecha: int = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        new_silo = Silo(
            Nombre=nombre,
            Capacidad=capacidad,
            Contenido=contenido,
            ID_Cosecha=id_cosecha,
            user_id=user_id
        )
        db.add(new_silo)
        db.commit()
        db.refresh(new_silo)
        return templates.TemplateResponse("silo.html", {"request": request, "message": "Silo registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("silo.html", {"request": request, "error": f"Failed to register silo. Error: {str(e)}"})

# Otros endpoints de ejemplo
@app.get("/cultivation", response_class=HTMLResponse)
async def cultivation(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Obtener todos los cultivos del usuario autenticado
    user_crops = db.query(Cultivo).filter(Cultivo.user_id == user_id).all()

    # Formatear los cultivos para pasarlos a la plantilla
    crops_data = [
        (crop.ID_Cultivo,
         crop.Tipo,
         crop.Area_cultivada,
         crop.Fecha_siembra,
         crop.Estado_crecimiento,
         crop.Necesidades_tratamiento)
        for crop in user_crops
    ]

    return templates.TemplateResponse("cultivation.html", {
        "request": request,
        "user_logged_in": True,
        "value": crops_data  # Pasamos los datos de los cultivos a la plantilla
    })

@app.get("/crop", response_class=HTMLResponse)
async def crop(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("crop.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/harvested", response_class=HTMLResponse)
async def harvested(request: Request, db: Session = Depends(get_db)):
        user_id = get_current_user_id(request)
        if not user_id:
            return RedirectResponse(url="/login")

        user_harvests = db.query(Cosecha).filter(Cosecha.user_id == user_id).all()
        harvests_data = [
            (harvest.ID_Cosecha, harvest.Tipo, harvest.Fecha_recoleccion, harvest.Cantidad)
            for harvest in user_harvests
        ]

        return templates.TemplateResponse("harvest_list.html", {
            "request": request,
            "user_logged_in": True,
            "value": harvests_data
        })
@app.get("/silocreation", response_class=HTMLResponse)
async def silocreation(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("silocreation.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/productcreation", response_class=HTMLResponse)
async def productcreation(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("productcreation.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/silo", response_class=HTMLResponse)
async def create_silo(
    request: Request,
    nombre: str = Form(...),
    capacidad: int = Form(...),
    contenido: str = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    new_silo = Silo(Nombre=nombre, Capacidad=capacidad, Contenido=contenido, user_id=user_id)
    db.add(new_silo)
    db.commit()
    db.refresh(new_silo)

    return RedirectResponse(url="/silo", status_code=303)

@app.get("/silo_detail/{silo_id}", response_class=HTMLResponse)
async def silo_detail(request: Request, silo_id: int, db: Session = Depends(get_db)):
    # Obtenemos el ID del usuario actual
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Consultamos el silo específico para el usuario
    db_silo = db.query(Silo).filter(Silo.ID_Silo == silo_id, Silo.user_id == user_id).first()
    if not db_silo:
        return templates.TemplateResponse("silo_detail.html", {"request": request, "error": "Silo not found"})

    # Pasamos los detalles del silo al contexto de la plantilla
    return templates.TemplateResponse("silo_detail.html", {
        "request": request,
        "silo": db_silo
    })

@app.get("/silo_update", response_class=HTMLResponse)
async def update_silo(
    request: Request,
    silo_id: int = Form(...),
    nombre: str = Form(...),
    capacidad: float = Form(...),
    contenido: float = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    db_silo = db.query(Silo).filter(Silo.ID_Silo == silo_id, Silo.user_id == user_id).first()
    if not db_silo:
        return templates.TemplateResponse("silo_update.html", {"request": request, "error": "Silo not found or unauthorized access."})

    db_silo.Nombre = nombre
    db_silo.Capacidad = capacidad
    db_silo.Contenido = contenido

    try:
        db.commit()
        db.refresh(db_silo)
        return templates.TemplateResponse("silo_update.html", {"request": request, "message": "Silo updated successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("silo_update.html", {"request": request, "error": f"Failed to update silo. Error: {str(e)}"})@app.get("/show_product", response_class=HTMLResponse)
async def show_product(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("show_product.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/product_detail", response_class=HTMLResponse)
async def register_product(
        request: Request,
        product_name: str = Form(...),
        quantity: float = Form(...),
        price: float = Form(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        new_product = PuntoVenta(
            Nombre=product_name,
            Cantidad=quantity,
            Precio=price,
            user_id=user_id
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return templates.TemplateResponse("product_detail.html",
                                          {"request": request, "message": "Product registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("product_detail.html",
                                          {"request": request, "error": f"Failed to register product. Error: {str(e)}"})


@app.get("/product_update", response_class=HTMLResponse)
async def product_update(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("product_update.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/crop_detail", response_class=HTMLResponse)
async def crop_detail(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("crop_detail.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/crop_update", response_class=HTMLResponse)
async def update_crop(
    request: Request,
    id_crop: int = Form(...),
    crop_type: str = Form(...),
    area: float = Form(...),
    planting_date: date = Form(...),
    amount: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    db_crop = db.query(Cultivo).filter(Cultivo.ID_Cultivo == id_crop, Cultivo.user_id == user_id).first()
    if not db_crop:
        return templates.TemplateResponse("crop_update.html", {"request": request, "error": "Crop not found or unauthorized access."})

    db_crop.Tipo = crop_type
    db_crop.Area_cultivada = area
    db_crop.Fecha_siembra = planting_date
    db_crop.Cantidad = amount
    db_crop.Precio_estimado = price

    try:
        db.commit()
        db.refresh(db_crop)
        return templates.TemplateResponse("crop_update.html", {"request": request, "message": "Crop updated successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("crop_update.html", {"request": request, "error": f"Failed to update crop. Error: {str(e)}"})


@app.get("/harvest", response_class=HTMLResponse)
async def harvest(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("harvest.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/harvest_detail", response_class=HTMLResponse)
async def register_harvest(
        request: Request,
        id_harvest: int = Form(...),
        harvest_type: str = Form(...),
        harvest_date: date = Form(...),
        quantity: float = Form(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        new_harvest = Cosecha(
            ID_Cosecha=id_harvest,
            Tipo=harvest_type,
            Fecha_cosecha=harvest_date,
            Cantidad=quantity,
            user_id=user_id
        )
        db.add(new_harvest)
        db.commit()
        db.refresh(new_harvest)
        return templates.TemplateResponse("harvest_detail.html",
                                          {"request": request, "message": "Harvest registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("harvest_detail.html",
                                          {"request": request, "error": f"Failed to register harvest. Error: {str(e)}"})


@app.get("/harvest_update", response_class=HTMLResponse)
async def update_harvest(
    request: Request,
    id_harvest: int = Form(...),
    harvest_type: str = Form(...),
    harvest_date: date = Form(...),
    quantity: float = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    db_harvest = db.query(Cosecha).filter(Cosecha.ID_Cosecha == id_harvest, Cosecha.user_id == user_id).first()
    if not db_harvest:
        return templates.TemplateResponse("harvest_update.html", {"request": request, "error": "Harvest not found or unauthorized access."})

    db_harvest.Tipo = harvest_type
    db_harvest.Fecha_cosecha = harvest_date
    db_harvest.Cantidad = quantity

    try:
        db.commit()
        db.refresh(db_harvest)
        return templates.TemplateResponse("harvest_update.html", {"request": request, "message": "Harvest updated successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("harvest_update.html", {"request": request, "error": f"Failed to update harvest. Error: {str(e)}"})



# Montar archivos estáticos
app.mount("/styles", StaticFiles(directory="styles"), name="styles2")

app.mount("/images", StaticFiles(directory="images"), name="Miguel")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")
app.mount("/images", StaticFiles(directory="images"), name="Camila")
app.mount("/images", StaticFiles(directory="images"), name="Nestor")