from fastapi import FastAPI, Request, Form, Depends, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
from agriculture.user.database import SessionLocal, get_db, engine, Base
from agriculture.user.models import User, Cultivo, Cosecha, Silo, PuntoVenta, Vehiculo, Venta, Encargo
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import SQLAlchemyError

# Crear todas las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)
app = FastAPI()

# Path to the templates folder
templates = Jinja2Templates(directory="templates")

#Optimization
cultivation="cultivation.html"
cultivation2="/cultivation"
silo="silo.html"

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

# Endpoints de autenticación y perfil
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("index.html", {"request": request, "user_logged_in": user_logged_in})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

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

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user_id", value=str(db_user.id), httponly=True)
    return response

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("user_id")
    return response

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_logged_in": True,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "email": db_user.email,
        "phone": db_user.phone
    })

# Endpoints para cultivos
@app.get("/crop", response_class=HTMLResponse)
async def crop(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("crop.html", {"request": request, "user_logged_in": user_logged_in})

@app.post("/crop_detail", response_class=HTMLResponse)
async def register_crop(
    request: Request,
    id_crop: int = Form(...),
    crop_type: str = Form(...),
    area: float = Form(...),
    planting_date: date = Form(...),
    growing_state: str = Form(...),
    needs: str = Form(...),
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
            Estado_crecimiento=growing_state,
            Necesidades_tratamiento=needs,
            user_id=user_id
        )
        db.add(new_crop)
        db.commit()
        db.refresh(new_crop)
        return templates.TemplateResponse("crop_detail.html", {"request": request, "message": "Crop registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("crop.html", {"request": request, "error": f"Failed to register crop. Error: {str(e)}"})


@app.get("/crop_delete/{id_crop}", response_class=HTMLResponse)
async def delete_crop(request: Request, id_crop: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Obtener el cultivo específico del usuario autenticado
    crop = db.query(Cultivo).filter(Cultivo.ID_Cultivo == id_crop, Cultivo.user_id == user_id).first()
    if not crop:
        return templates.TemplateResponse(cultivation,
                                          {"request": request, "error": "Crop not found or unauthorized access."})


    try:
        # Eliminar todas las cosechas relacionadas
        db.query(Cosecha).filter(Cosecha.ID_Cultivo == id_crop).delete()

        # Eliminar todos los silos relacionados
        db.query(Silo).filter(Silo.ID_Cosecha == id_crop).delete()

        # Eliminar el cultivo principal
        db.delete(crop)
        db.commit()

        # Redirigir al usuario a la página de cultivos
        return RedirectResponse(url=cultivation2, status_code=302)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(cultivation,
                                          {"request": request, "error": f"Failed to delete crop. Error: {str(e)}"})
@app.get("/crop_update/{id_crop}", response_class=HTMLResponse)
async def get_crop_update(request: Request, id_crop: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Obtener el cultivo para el usuario autenticado
    crop1 = db.query(Cultivo).filter(Cultivo.ID_Cultivo == id_crop, Cultivo.user_id == user_id).first()
    if not crop1:
        print("Cultivo no encontrado o el usuario no tiene permiso.")
        return RedirectResponse(url=cultivation2)

    print("Cultivo encontrado:", crop1)  # Para confirmar que los datos existen

    # Cargar el formulario con los datos del cultivo
    return templates.TemplateResponse(f"crop_update/{id_crop}.html", {
        "request": request,
        "id_crop": id_crop,
        "crop": crop1
    })


@app.post("/crop_update", response_class=HTMLResponse)
async def post_crop_update(
    request: Request,
    id_crop: int,
    crop_type: str = Form(...),
    area: float = Form(...),
    planting_date: date = Form(...),
    growing_state: str = Form(...),
    needs: str = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Verificar que el cultivo existe y pertenece al usuario
    crop1 = db.query(Cultivo).filter(Cultivo.ID_Cultivo == id_crop, Cultivo.user_id == user_id).first()
    if not crop1:
        return templates.TemplateResponse(cultivation, {"request": request, "error": "Cultivo no encontrado o acceso no autorizado"})

    # Actualizar el cultivo con los nuevos datos
    crop1.Tipo = crop_type
    crop1.Area_cultivada = area
    crop1.Fecha_siembra = planting_date
    crop1.Estado_crecimiento = growing_state
    crop1.Necesidades_tratamiento = needs

    try:
        db.commit()
        db.refresh(crop1)
        return templates.TemplateResponse(cultivation, {"request": request, "message": "Crop updated succesfully!", "crop": crop1})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("crop_update.html", {"request": request, "error": f"Cannot update crop. Error: {str(e)}", "crop": crop1})

@app.get("/cultivation", response_class=HTMLResponse)
async def cultivation(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    user_crops = db.query(Cultivo).filter(Cultivo.user_id == user_id).all()
    crops_data = [
        (crop.ID_Cultivo, crop.Tipo, crop.Area_cultivada, crop.Fecha_siembra, crop.Estado_crecimiento, crop.Necesidades_tratamiento)
        for crop in user_crops
    ]

    return templates.TemplateResponse(cultivation, {
        "request": request,
        "user_logged_in": True,
        "value": crops_data
    })

# Endpoints para silos


@app.get("/silo", response_class=HTMLResponse)
async def silo(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse(silo, {"request": request, "user_logged_in": user_logged_in})

@app.get("/silocreation", response_class=HTMLResponse)
async def silocreation(request: Request, db: Session= Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")
    user_silos=db.query(Silo).filter(Silo.user_id==user_id).all()
    silos_data = [
        (silo.ID_Silo, silo.Capacidad)
        for silo in user_silos
    ]

    return templates.TemplateResponse("silocreation.html",{
        "request":request,
        "user_logged_in":True,
        "value":silos_data

    })

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
            ID_Silo=id_cosecha,
            user_id=user_id
        )
        db.add(new_silo)
        db.commit()
        db.refresh(new_silo)
        return templates.TemplateResponse(silo, {"request": request, "message": "Silo registered successfully!"})
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(silo, {"request": request, "error": f"Failed to register silo. Error: {str(e)}"})

@app.get("/silo_update/{id_silo}", response_class=HTMLResponse)
async def update_silo(request: Request, id_silo: int, db: Session = Depends(get_db)):
    silo = db.query(Silo).filter(Silo.ID_Silo == id_silo).first()
    if not silo:
        return RedirectResponse(url="/silocreation")
    return templates.TemplateResponse("silo_update.html", {"request": request, "id_silo": id_silo, "silo": silo})

# Endpoints para productos
@app.get("/productcreation", response_class=HTMLResponse)
async def productcreation(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    products = db.query(Cosecha).filter(Cosecha.user_id == user_id).all()
    value = [
        {
            "id_product": product.ID_Cosecha,
            "type": product.Tipo if hasattr(product, 'Tipo') else "N/A",
            "weight": product.Cantidad_cosecha if hasattr(product, 'Cantidad_cosecha') else 0.0,
            "sellprice": 0.0,
            "amount": product.Area if hasattr(product, 'Area') else 0
        }
        for product in products
    ]

    return templates.TemplateResponse("productcreation.html", {
        "request": request,
        "user_logged_in": True,
        "value": value
    })

# Endpoints para cosechas (harvests)
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

    return templates.TemplateResponse("harvested.html", {
        "request": request,
        "user_logged_in": True,
        "value": harvests_data
    })

@app.post("/harvest_detail", response_class=HTMLResponse)
async def register_harvest(
    request: Request,
    id_harvest: int = Form(...),
    area: float = Form(...),
    harvest_date: date = Form(...),
    quantity: float = Form(...),
    id_crop: int = Form(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        new_harvest = Cosecha(
            ID_Cosecha=id_harvest,
            Area=area,
            Fecha_cosecha=harvest_date,
            Cantidad_cosecha=quantity,
            ID_Cultivo=id_crop,
            user_id=user_id,
        )
        db.add(new_harvest)
        db.commit()
        db.refresh(new_harvest)
        return RedirectResponse(url="/harvested", status_code=302)
    except SQLAlchemyError as e:
        db.rollback()
        return templates.TemplateResponse("harvest.html", {
            "request": request,
            "error": f"Failed to register harvest. Error: {str(e)}"
        })

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

@app.get("/harvest/{id_crop}", response_class=HTMLResponse)
async def harvest_form(request: Request, id_crop: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Obtener el cultivo y verificar que pertenece al usuario actual
    crop = db.query(Cultivo).filter(Cultivo.ID_Cultivo == id_crop, Cultivo.user_id == user_id).first()
    if not crop:
        return RedirectResponse(url=cultivation2)

    # Cargar el formulario `harvest` con datos prellenados del cultivo
    return templates.TemplateResponse("harvest.html", {
        "request": request,
        "id_harvest": id_crop,
        "crop_type": crop.Tipo,
        "area": crop.Area_cultivada
    })

@app.get("/harvested", response_class=HTMLResponse)
async def harvested(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Obtener todas las cosechas del usuario
    user_harvests = db.query(Cosecha).filter(Cosecha.user_id == user_id).all()
    harvests_data = [
        (harvest.ID_Cosecha, harvest.Tipo, harvest.Fecha_cosecha, harvest.Cantidad_cosecha, harvest.Area)
        for harvest in user_harvests
    ]

    return templates.TemplateResponse("harvested.html", {
        "request": request,
        "user_logged_in": True,
        "value": harvests_data
    })



#Endpoints distribucion
@app.get("/distribution", response_class=HTMLResponse)
async def distribution(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("distribution.html", {"request": request, "user_logged_in": user_logged_in})

#Endpoints encargos
@app.get("/assignments", response_class=HTMLResponse)
async def assignmnets(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("assignments.html", {"request": request, "user_logged_in": user_logged_in})


# GET para listar todos los encargos del usuario
@app.get("/assignment_creation", response_class=HTMLResponse)
async def assignment_creation(request: Request, db: Session = Depends(get_db)):
    user_logged_in = is_logged_in(request)
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Filtrar encargos del usuario actual
    user_assignments = db.query(Encargo).filter(Encargo.user_id == user_id).all()
    return templates.TemplateResponse("assignment_creation.html", {
        "request": request,
        "user_logged_in": user_logged_in,
        "assignments": user_assignments
    })


# POST para registrar un nuevo encargo
@app.post("/assignment_detail", response_class=HTMLResponse)
async def register_assignment(
        request: Request,
        fecha: date = Form(...),
        cantidad_producto: float = Form(...),
        id_vehiculo: int = Form(...),
        punto_venta_id: int = Form(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        # Crear y agregar el nuevo encargo
        new_assignment = Encargo(
            Fecha=fecha,
            Cantidad_producto=cantidad_producto,
            ID_Vehiculo=id_vehiculo,
            Punto_Venta_ID=punto_venta_id,
            user_id=user_id
        )
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        return templates.TemplateResponse("assignment_detail.html", {
            "request": request,
            "message": "Assignment registered successfully!",
            "assignment": new_assignment
        })
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("assignment_detail.html", {
            "request": request,
            "error": f"Failed to register assignment. Error: {str(e)}"
        })
@app.get("/assignment_update", response_class=HTMLResponse)
async def assignment_update(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("assignment_update.html", {"request": request, "user_logged_in": user_logged_in})


#Endpoints vehiculos

@app.get("/vehicles", response_class=HTMLResponse)
async def vehicles(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("vehicles.html", {"request": request, "user_logged_in": user_logged_in})


# GET para listar todos los vehículos del usuario
@app.get("/vehicle_creation", response_class=HTMLResponse)
async def vehicle_creation(request: Request, db: Session = Depends(get_db)):
    user_logged_in = is_logged_in(request)
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Filtrar vehículos del usuario actual
    user_vehicles = db.query(Vehiculo).filter(Vehiculo.user_id == user_id).all()
    return templates.TemplateResponse("vehicle_creation.html", {
        "request": request,
        "user_logged_in": user_logged_in,
        "vehicles": user_vehicles
    })

# POST para registrar un nuevo vehículo
@app.post("/vehicle_detail", response_class=HTMLResponse)
async def register_vehicle(
        request: Request,
        matricula: str = Form(...),
        capacidad_carga: float = Form(...),
        id_cosecha: int = Form(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        # Crear y agregar el nuevo vehículo
        new_vehicle = Vehiculo(
            Matricula=matricula,
            Capacidad_Carga=capacidad_carga,
            ID_Cosecha=id_cosecha,
            user_id=user_id
        )
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        return templates.TemplateResponse("vehicle_detail.html", {
            "request": request,
            "message": "Vehicle registered successfully!",
            "vehicle": new_vehicle
        })
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("vehicle_detail.html", {
            "request": request,
            "error": f"Failed to register vehicle. Error: {str(e)}"
        })


@app.get("/vehicle_update", response_class=HTMLResponse)
async def vehicle_update(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("vehicle_update.html", {"request": request, "user_logged_in": user_logged_in})


@app.get("/pos", response_class=HTMLResponse)
async def pos(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("pos.html", {"request": request, "user_logged_in": user_logged_in})


# GET para listar todos los puntos de venta del usuario
@app.get("/pos_creation", response_class=HTMLResponse)
async def pos_creation(request: Request, db: Session = Depends(get_db)):
    user_logged_in = is_logged_in(request)
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    # Filtrar puntos de venta del usuario actual
    user_pos = db.query(PuntoVenta).filter(PuntoVenta.user_id == user_id).all()
    return templates.TemplateResponse("pos_creation.html", {
        "request": request,
        "user_logged_in": user_logged_in,
        "points_of_sale": user_pos
    })

# POST para registrar un nuevo punto de venta
@app.post("/pos_detail", response_class=HTMLResponse)
async def register_pos(
        request: Request,
        nombre: str = Form(...),
        direccion: str = Form(...),
        db: Session = Depends(get_db)
):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login")

    try:
        # Crear y agregar el nuevo punto de venta
        new_pos = PuntoVenta(
            Nombre=nombre,
            Direccion=direccion,
            user_id=user_id
        )
        db.add(new_pos)
        db.commit()
        db.refresh(new_pos)
        return templates.TemplateResponse("pos_detail.html", {
            "request": request,
            "message": "Point of Sale registered successfully!",
            "pos": new_pos
        })
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("pos_detail.html", {
            "request": request,
            "error": f"Failed to register Point of Sale. Error: {str(e)}"
        })
@app.get("/pos_update", response_class=HTMLResponse)
async def pos_update(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("pos_update.html", {"request": request, "user_logged_in": user_logged_in})


@app.get("/sales", response_class=HTMLResponse)
async def sales(request: Request):
    user_logged_in = is_logged_in(request)
    return templates.TemplateResponse("sales.html", {"request": request, "user_logged_in": user_logged_in})


# Montar archivos estáticos
app.mount("/styles", StaticFiles(directory="styles"), name="styles2")
app.mount("/images", StaticFiles(directory="images"), name="Miguel")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")
app.mount("/images", StaticFiles(directory="images"), name="Camila")
app.mount("/images", StaticFiles(directory="images"), name="Nestor")
