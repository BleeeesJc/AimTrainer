from flask import Flask, request,render_template,redirect, url_for,session,Response
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
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

        return redirect(url_for('form.html'))

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
            session['idUsuario'] = user[0]  # Guardar el idUsuario en la sesión
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

@app.route('/guardar_resultados', methods=['POST'])
def guardar_resultados():
    if 'idUsuario' not in session:
        return "Error: Usuario no autenticado."

    idUsuario = session['idUsuario']
    
    try:
        aciertos = int(request.form['aciertos'])  # Asegúrate de que 'aciertos' sea un entero
        tiempo = int(request.form['tiempo'])      # Asegúrate de que 'tiempo' sea un entero
        precision = float(request.form['precision'])  # Asegúrate de que 'precision' sea un float

    except ValueError as ve:
        return f"Error: Los datos proporcionados no son válidos - {ve}"

    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO resultados (idUsuario, aciertos, tiempo, pre) 
        VALUES (%s, %s, %s, %s)
        """ 
        values = (idUsuario, aciertos, tiempo, precision)
        cursor.execute(query, values)
        conn.commit()

        return Response(status=204)
    except Exception as e:
        conn.rollback()
        return f"Error al guardar los resultados: {e}"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)