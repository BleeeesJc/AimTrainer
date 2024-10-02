from flask import Flask, request,render_template,redirect, url_for
import mysql.connector

app = Flask(__name__)

# Conectar a la base de datos MySQL
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",        # Tu host 
        user="root",             # Usuario de MySQL 
        password="",             # Contraseña de MySQL 
        database="juego"        # Nombre de la base 
    )
@app.route('/')
def index():
    return render_template('form.html')
@app.route('/register', methods=['POST'])
def register_user():
    # Obtener los datos del formulario
    usuario = request.form['usuario']
    email = request.form['email']
    contrasena = request.form['pswd']
    edad = request.form['edad']
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        query = "INSERT INTO usuarios (usuario, correo, password, edad) VALUES (%s, %s, %s, %s)"
        values = (usuario, email, contrasena, edad)

        cursor.execute(query, values)
        conn.commit()

        return "Registro exitoso"
    except Exception as e:
        conn.rollback() 
        return f"Error al registrar: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    usuario = request.form.get('usuario')  
    contrasena = request.form.get('pswd')  

    if not usuario or not contrasena:
        return "Error: Datos de usuario o contraseña faltantes."

    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM usuarios WHERE usuario = %s AND password = %s"
        cursor.execute(query, (usuario, contrasena))
        user = cursor.fetchone()

        if user:
            return redirect(url_for('aim'))
        else:
            return "Error: Usuario o contraseña incorrectos."
    except Exception as e:
        return f"Error al iniciar sesión: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/aim')
def aim():
    return render_template('Aim.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)