import pytest
from fastapi.testclient import TestClient
from app.agriculture.user.models import User
from app import app


# Utilizamos un fixture para crear el cliente de prueba
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


# Testea la página de inicio ("/")
def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.content  # Busca un texto de bienvenida en el HTML


# Testea la página "about_us"
def test_about_us(client):
    response = client.get("/about_us")
    assert response.status_code == 200
    assert b"About Us" in response.content


# Testea la página de "contact"
def test_contact_us(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert b"Contact" in response.content


# Testea la página de login
def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.content


# Testea el registro de usuario (POST /register)
@pytest.fixture
def new_user_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "phone": "1234567890",
        "password": "securepassword",
        "confirm_password": "securepassword"
    }


def test_register_user(client, new_user_data):
    response = client.post("/register", data=new_user_data)
    assert response.status_code == 200
    assert b"User created successfully!" in response.content


# Testea el caso de que los correos duplicados no se puedan registrar (POST /register)
def test_register_duplicate_email(client, new_user_data):
    # Registrar el primer usuario
    client.post("/register", data=new_user_data)

    # Intentar registrar el mismo correo de nuevo
    response = client.post("/register", data=new_user_data)
    assert response.status_code == 200
    assert b"The email is already registered" in response.content


# Testea el login de usuario (POST /login)
def test_login(client, new_user_data):
    # Primero registrar al usuario
    client.post("/register", data=new_user_data)

    # Ahora intentamos iniciar sesión
    response = client.post("/login", data={"email": new_user_data["email"], "password": new_user_data["password"]})
    assert response.status_code == 302  # Redirige a la página de inicio
    assert "user_id" in response.cookies  # Debería haber una cookie de sesión


# Testea el inicio de sesión con credenciales incorrectas (POST /login)
def test_login_invalid_credentials(client, new_user_data):
    client.post("/register", data=new_user_data)

    # Intentar iniciar sesión con una contraseña incorrecta
    response = client.post("/login", data={"email": new_user_data["email"], "password": "wrongpassword"})
    assert response.status_code == 200
    assert b"Invalid email or password" in response.content


# Testea el endpoint de cerrar sesión (GET /logout)
def test_logout(client, new_user_data):
    # Registrar e iniciar sesión primero
    client.post("/register", data=new_user_data)
    login_response = client.post("/login",
                                 data={"email": new_user_data["email"], "password": new_user_data["password"]})

    # Verificar que la cookie 'user_id' está presente
    assert "user_id" in login_response.cookies

    # Ahora cerramos sesión
    response = client.get("/logout", cookies=login_response.cookies)
    assert response.status_code == 200
    assert "user_id" not in response.cookies  # La cookie 'user_id' debería haber sido eliminada


# Testea que si no estás autenticado, no puedes acceder al perfil del usuario (GET /profile)
def test_profile_no_login(client):
    response = client.get("/profile")
    assert response.status_code == 302  # Redirige a login
    assert response.headers["location"] == "/login"  # Verifica que redirige a la página de login


# Testea que si estás autenticado, puedes acceder a tu perfil (GET /profile)
def test_profile_logged_in(client, new_user_data):
    # Registrar e iniciar sesión
    client.post("/register", data=new_user_data)
    login_response = client.post("/login",
                                 data={"email": new_user_data["email"], "password": new_user_data["password"]})

    # Verifica que ahora puedes acceder al perfil
    response = client.get("/profile", cookies=login_response.cookies)
    assert response.status_code == 200
    assert b"First Name" in response.content  # Verifica que se muestra información del perfil


# Testea el acceso a un endpoint de página de cultivo (GET /cultivation)
def test_cultivation_page(client):
    response = client.get("/cultivation")
    assert response.status_code == 200
    assert b"Cultivation" in response.content  # Reemplazar con el contenido real de la página


# Testea el acceso a un endpoint de silo (GET /silo)
def test_silo_page(client):
    response = client.get("/silo")
    assert response.status_code == 200
    assert b"Silo" in response.content  # Reemplazar con el contenido real de la página


# Testea el acceso a una página de silo detail (GET /silo_detail)
def test_silo_detail_page(client):
    response = client.get("/silo_detail")
    assert response.status_code == 200
    assert b"Silo Details" in response.content  # Reemplazar con el contenido real de la página

