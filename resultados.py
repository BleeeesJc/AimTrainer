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

        return redirect(url_for('/'))

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
            return redirect(url_for('modo'))
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

@app.route('/seguimiento')
def seguimiento():
    return render_template('seguimiento.html')

@app.route('/reto')
def reto():
    return render_template('reto.html')
@app.route('/modo')
def modo():
    return render_template('modo.html')

@app.route('/guardar_resultados', methods=['POST'])
def guardar_resultados():
    if 'idUsuario' not in session:
        return "Error: Usuario no autenticado."
    
    if 'idTipo' not in session:
        return "Error: Tipo de juego no seleccionado."

    idUsuario = session['idUsuario']
    idTipo = session['idTipo']  # Recuperar el idTipo de la sesión
    
    try:
        aciertos = int(request.form['aciertos'])  # Asegúrate de que 'aciertos' sea un entero
        tiempo = int(request.form['tiempo'])      # Asegúrate de que 'tiempo' sea un entero
        precision = float(request.form['precision'])  # Asegúrate de que 'precision' sea un float

    except ValueError as ve:
        return f"Error: Los datos proporcionados no son válidos - {ve}"

    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Guardar los resultados junto con el idTipo
        query = """
        INSERT INTO resultados (idUsuario, idTipo, aciertos, tiempo, pre) 
        VALUES (%s, %s, %s, %s, %s)
        """ 
        values = (idUsuario, idTipo, aciertos, tiempo, precision)
        cursor.execute(query, values)
        conn.commit()

        return Response(status=204)
    except Exception as e:
        conn.rollback()
        return f"Error al guardar los resultados: {e}"
    finally:
        cursor.close()
        conn.close()

@app.route('/guardar_dificultad', methods=['POST'])
def guardar_dificultad():
    if 'idUsuario' not in session:
        return "Error: Usuario no autenticado.", 403
    
    data = request.get_json()

    nombre = data.get('nombre')  # Nombre del juego
    descripcion = data.get('descripcion')  # Descripción del juego
    dificultad = data.get('dificultad')  # Dificultad seleccionada
    
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Insertar los datos en la tabla tipo_juego
        query = """
        INSERT INTO tipo_juego (nombre, descripcion, dificultad) 
        VALUES (%s, %s, %s)
        """
        values = (nombre, descripcion, dificultad)
        cursor.execute(query, values)
        
        # Obtener el id del último registro insertado (idTipo)
        idTipo = cursor.lastrowid
        
        conn.commit()

        # Guardar el idTipo en la sesión
        session['idTipo'] = idTipo

        return {"status": "success", "idTipo": idTipo}, 200

    except Exception as e:
        conn.rollback()
        return f"Error al guardar la dificultad: {e}", 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)