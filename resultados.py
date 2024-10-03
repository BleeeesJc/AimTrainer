import csv
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, send_file, url_for, session, Response
import mysql.connector
import plotly.graph_objects as go
import plotly.io as pio
import os

app = Flask(__name__)  # Inicializa una instancia de la aplicación Flask
app.secret_key = os.urandom(24)  # Genera una clave secreta aleatoria para manejar sesiones

# Función para conectar a la base de datos MySQL
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",  # Servidor MySQL local
        user="root",  # Usuario de MySQL
        password="",  # Contraseña de MySQL
        database="juego"  # Nombre de la base de datos donde se almacenan los datos del juego
    )

# Ruta principal que muestra el formulario HTML (página de inicio)
@app.route('/')
def index():
    return render_template('form.html')  # Renderiza el archivo 'form.html' como respuesta

# Función que exporta los resultados de los jugadores a un archivo CSV
def exportar_resultados_a_csv(nombre_archivo):
    try:
        conn = connect_to_database()  # Establece la conexión con la base de datos
        cursor = conn.cursor()  # Crea un cursor para ejecutar consultas

        # Consulta SQL para obtener los resultados de los jugadores
        query = """
            SELECT u.usuario AS nombre_usuario, tj.nombre AS tipo_juego, r.aciertos, r.pre AS `precision`, r.tiempo, r.fecha
            FROM resultados r
            JOIN usuarios u ON r.idUsuario = u.idUsuario
            JOIN tipo_juego tj ON r.idTipo = tj.idTipo
            ORDER BY u.usuario, r.fecha;
        """
        cursor.execute(query)  # Ejecuta la consulta
        resultados = cursor.fetchall()  # Recupera todos los resultados

        if not resultados:  # Si no hay resultados
            print("No se encontraron resultados.")
            return

        # Crea un archivo CSV y escribe los resultados
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(['nombre_usuario', 'tipo_juego', 'aciertos', 'precision', 'tiempo', 'fecha'])  # Encabezados del CSV
            for fila in resultados:
                escritor_csv.writerow(fila)  # Escribe cada fila en el archivo CSV

        print(f"Los resultados se han guardado correctamente en el archivo {nombre_archivo}")

        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión

    except Exception as e:
        print(f"Error al exportar los resultados a CSV: {e}")  # Manejo de errores

# Ruta que permite descargar el archivo CSV con los resultados de los jugadores
@app.route('/descargar_csv')
def descargar_csv():
    nombre_archivo = 'resultados_jugadores.csv'  # Nombre del archivo CSV a generar
    exportar_resultados_a_csv(nombre_archivo)  # Llama a la función que genera el CSV
    return send_file(nombre_archivo, as_attachment=True, download_name=nombre_archivo)  # Envía el archivo para su descarga

# Ruta que registra un nuevo usuario a partir de un formulario POST
@app.route('/register', methods=['POST'])
def register_user():
    # Obtiene los datos enviados en el formulario
    usuario = request.form['usuario']
    email = request.form['email']
    contrasena = request.form['pswd']
    edad = request.form['edad']

    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    try:
        query = "INSERT INTO usuarios (usuario, correo, password, edad) VALUES (%s, %s, %s, %s)"  # Consulta para insertar el usuario
        values = (usuario, email, contrasena, edad)
        cursor.execute(query, values)  # Ejecuta la consulta con los valores
        conn.commit()  # Confirma la transacción en la base de datos
        return redirect(url_for('/'))  # Redirige a la página principal si tiene éxito

    except Exception as e:
        conn.rollback()  # Revierte la transacción si hay un error
        return f"Error al registrar: {e}"  # Devuelve el error
    finally:
        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión a la base de datos

# Ruta que lista todos los usuarios en una tabla
@app.route('/usuarios', methods=['GET'])
def list_users():
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()
    query = "SELECT * FROM usuarios"  # Consulta para obtener todos los usuarios
    cursor.execute(query)
    usuarios = cursor.fetchall()  # Recupera todos los resultados

    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión a la base de datos

    return render_template('crud.html', usuarios=usuarios)  # Renderiza la tabla HTML con los usuarios

# Ruta que actualiza un usuario dado su ID
@app.route('/usuarios/update/<int:id>', methods=['POST'])
def update_user(id):
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json()  # Obtiene los datos enviados en formato JSON
        nuevo_usuario = data['usuario']
        nuevo_email = data['email']
        nueva_edad = data['edad']

        try:
            query = "UPDATE usuarios SET usuario = %s, correo = %s, edad = %s WHERE idUsuario = %s"  # Consulta para actualizar el usuario
            values = (nuevo_usuario, nuevo_email, nueva_edad, id)
            cursor.execute(query, values)  # Ejecuta la actualización
            conn.commit()  # Confirma la transacción
            return jsonify({"message": "Actualizado exitosamente"}), 200  # Respuesta exitosa
        except Exception as e:
            conn.rollback()  # Revierte la transacción si hay un error
            return jsonify({"error": str(e)}), 500  # Devuelve el error en formato JSON
        finally:
            cursor.close()  # Cierra el cursor
            conn.close()  # Cierra la conexión a la base de datos

# Ruta que elimina un usuario dado su ID
@app.route('/usuarios/delete/<int:id>', methods=['POST'])
def delete_user(id):
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    try:
        query = "DELETE FROM usuarios WHERE idUsuario = %s"  # Consulta para eliminar un usuario
        cursor.execute(query, (id,))
        conn.commit()  # Confirma la transacción
        return jsonify({"status": "success"}), 200  # Devuelve una respuesta de éxito
    except Exception as e:
        conn.rollback()  # Revierte la transacción si hay un error
        return jsonify({"error": str(e)}), 500  # Devuelve el error en formato JSON
    finally:
        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión a la base de datos

# Ruta que maneja el inicio de sesión de un usuario
@app.route('/login', methods=['POST'])
def login_user():
    usuario = request.form.get('usuario')  # Obtiene el nombre de usuario del formulario
    contrasena = request.form.get('pswd')  # Obtiene la contraseña del formulario

    if not usuario or not contrasena:  # Si falta el nombre de usuario o la contraseña
        return "Error: Datos de usuario o contraseña faltantes."

    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM usuarios WHERE usuario = %s AND password = %s"  # Consulta para verificar las credenciales
        cursor.execute(query, (usuario, contrasena))  # Ejecuta la consulta
        user = cursor.fetchone()  # Recupera el usuario si las credenciales coinciden

        if user:  # Si el usuario existe
            session['idUsuario'] = user[0]  # Almacena el idUsuario en la sesión
            return redirect(url_for('modo'))  # Redirige a la selección de modo de juego
        else:
            return "Error: Usuario o contraseña incorrectos."  # Error si las credenciales no coinciden
    except Exception as e:
        return f"Error al iniciar sesión: {e}"  # Devuelve el error si ocurre
    finally:
        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión a la base de datos

# Ruta que muestra la página del modo 'aim'
@app.route('/aim')
def aim():
    return render_template('Aim.html')  # Renderiza la página Aim.html

# Ruta que muestra la página del modo 'seguimiento'
@app.route('/seguimiento')
def seguimiento():
    return render_template('seguimiento.html')  # Renderiza la página seguimiento.html

# Ruta que muestra la página del modo 'reto'
@app.route('/reto')
def reto():
    return render_template('reto.html')  # Renderiza la página reto.html

# Ruta que muestra la página para seleccionar el modo de juego
@app.route('/modo')
def modo():
    return render_template('modo.html')  # Renderiza la página modo.html

# Ruta que guarda los resultados del juego en la base de datos
@app.route('/guardar_resultados', methods=['POST'])
def guardar_resultados():
    if 'idUsuario' not in session:  # Verifica si el usuario ha iniciado sesión
        return "Error: Usuario no autenticado."
    
    if 'idTipo' not in session:  # Verifica si el tipo de juego ha sido seleccionado
        return "Error: Tipo de juego no seleccionado."

    idUsuario = session['idUsuario']  # Recupera el ID del usuario de la sesión
    idTipo = session['idTipo']  # Recupera el ID del tipo de juego de la sesión
    
    try:
        # Obtiene los datos de la solicitud POST y verifica que sean válidos
        aciertos = int(request.form['aciertos'])  
        tiempo = int(request.form['tiempo'])  
        precision = float(request.form['precision'])  

    except ValueError as ve:
        return f"Error: Los datos proporcionados no son válidos - {ve}"

    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    try:
        # Inserta los resultados en la base de datos
        query = """
        INSERT INTO resultados (idUsuario, idTipo, aciertos, tiempo, pre) 
        VALUES (%s, %s, %s, %s, %s)
        """ 
        values = (idUsuario, idTipo, aciertos, tiempo, precision)
        cursor.execute(query, values)  # Ejecuta la consulta
        conn.commit()  # Confirma la transacción

        return Response(status=204)  # Devuelve una respuesta vacía con código 204 (sin contenido)
    except Exception as e:
        conn.rollback()  # Revierte la transacción si hay un error
        return f"Error al guardar los resultados: {e}"  # Devuelve el error
    finally:
        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión a la base de datos

# Ruta que guarda la dificultad del juego en la base de datos
@app.route('/guardar_dificultad', methods=['POST'])
def guardar_dificultad():
    if 'idUsuario' not in session:  # Verifica si el usuario está autenticado
        return "Error: Usuario no autenticado.", 403
    
    data = request.get_json()  # Obtiene los datos en formato JSON

    nombre = data.get('nombre')  # Nombre del juego
    descripcion = data.get('descripcion')  # Descripción del juego
    dificultad = data.get('dificultad')  # Nivel de dificultad
    
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    try:
        # Inserta los datos en la tabla tipo_juego
        query = """
        INSERT INTO tipo_juego (nombre, descripcion, dificultad) 
        VALUES (%s, %s, %s)
        """
        values = (nombre, descripcion, dificultad)
        cursor.execute(query, values)  # Ejecuta la consulta
        
        # Obtiene el ID del último registro insertado
        idTipo = cursor.lastrowid  
        
        conn.commit()  # Confirma la transacción

        # Guarda el ID del tipo de juego en la sesión
        session['idTipo'] = idTipo

        return {"status": "success", "idTipo": idTipo}, 200  # Respuesta exitosa
    except Exception as e:
        conn.rollback()  # Revierte la transacción si hay un error
        return f"Error al guardar la dificultad: {e}", 500  # Devuelve el error
    finally:
        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión a la base de datos

# Ruta que renderiza la página para mostrar gráficas
@app.route('/grafica')
def grafica():
    return render_template('grafica.html')  # Renderiza la página grafica.html

# Función que obtiene los datos de precisión promedio por edad para la gráfica
@app.route('/grafica_precision_edad', methods=['GET'])
def datos_precision_edad():
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    query = """SELECT u.edad, AVG(r.pre) AS media_precision
        FROM usuarios u
        JOIN resultados r ON u.idUsuario = r.idUsuario
        GROUP BY u.edad;"""  # Consulta para obtener el promedio de precisión por edad
    cursor.execute(query)
    resultados = cursor.fetchall()  # Recupera los resultados
        
    if not resultados:
        print("No se encontraron datos")
        return None, None
    
    edad = []
    pres = []

    for fila in resultados:
        edad.append(fila[0])  # Almacena las edades
        pres.append(fila[1])  # Almacena las precisiones promedio

    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión

    return edad, pres  # Devuelve las listas de edades y precisiones

# Función que obtiene el promedio de aciertos por edad
@app.route('/datos_aciertos_edad', methods=['GET'])
def datos_aciertos_edad():
    conn = connect_to_database()  # Conexión a la base de datos
    cursor = conn.cursor()

    query = """SELECT u.edad, AVG(r.aciertos) AS promedio_aciertos
                FROM usuarios u
                JOIN resultados r ON u.idUsuario = r.idUsuario
                GROUP BY u.edad;"""  # Consulta para obtener el promedio de aciertos por edad
    cursor.execute(query)
    resultados = cursor.fetchall()
        
    if not resultados:
        print("No se encontraron datos")
        return None, None
    
    edad = []
    aciertos = []

    for fila in resultados:
        edad.append(fila[0])  # Almacena las edades
        aciertos.append(fila[1])  # Almacena los aciertos promedio

    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión

    return edad, aciertos  # Devuelve las listas de edades y aciertos

# Función que obtiene la precisión por usuario y fecha
@app.route('/datos_pres_fecha_usuario', methods=['GET'])
def datos_pres_fecha_usuario(nombre):
    try:
        conn = connect_to_database()  # Conexión a la base de datos
        cursor = conn.cursor()

        query = """SELECT r.fecha, r.pre
                   FROM resultados r
                   JOIN usuarios u ON r.idUsuario = u.idUsuario
                   WHERE u.usuario = %s
                   ORDER BY r.fecha ASC;"""  # Consulta para obtener la precisión por usuario y fecha
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        fecha = []
        pres = []

        for fila in resultados:
            fecha.append(fila[0])  # Almacena las fechas
            pres.append(fila[1])  # Almacena las precisiones

        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión

        return fecha, pres  # Devuelve las listas de fechas y precisiones
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None

# Función que obtiene los aciertos por usuario y fecha
@app.route('/datos_aciertos_fecha_usuario', methods=['GET'])
def datos_aciertos_fecha_usuario(nombre):
    try:
        conn = connect_to_database()  # Conexión a la base de datos
        cursor = conn.cursor()

        query = """SELECT r.fecha, r.aciertos
                   FROM resultados r
                   JOIN usuarios u ON r.idUsuario = u.idUsuario
                   WHERE u.usuario = %s
                   ORDER BY r.fecha ASC;"""  # Consulta para obtener los aciertos por usuario y fecha
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        fecha = []
        aciertos = []

        for fila in resultados:
            fecha.append(fila[0])  # Almacena las fechas
            aciertos.append(fila[1])  # Almacena los aciertos

        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión

        return fecha, aciertos  # Devuelve las listas de fechas y aciertos
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None

# Función que obtiene los aciertos por usuario y tipo de juego
@app.route('/datos_aciertos_juego_usuario', methods=['GET'])
def datos_aciertos_juego_usuario(nombre):
    try:
        conn = connect_to_database()  # Conexión a la base de datos
        cursor = conn.cursor()

        query = """SELECT tj.nombre AS tipo_juego, SUM(r.aciertos) AS total_aciertos
                    FROM resultados r
                    JOIN tipo_juego tj ON r.idTipo = tj.idTipo
                    JOIN usuarios u ON r.idUsuario = u.idUsuario
                    WHERE u.usuario = %s
                    GROUP BY tj.nombre;"""  # Consulta para obtener los aciertos por tipo de juego
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        juego = []
        aciertos = []

        for fila in resultados:
            juego.append(fila[0])  # Almacena los tipos de juego
            aciertos.append(fila[1])  # Almacena los aciertos

        cursor.close()  # Cierra el cursor
        conn.close()  # Cierra la conexión

        return juego, aciertos  # Devuelve las listas de tipos de juego y aciertos
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None

# Ruta que genera la gráfica de aciertos por tipo de juego para un usuario
@app.route('/grafico_aciertos_juego_usuario', methods=['GET'])
def grafico_aciertos_juego_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)  # Obtiene el nombre del usuario

        juego, aciertos = datos_aciertos_juego_usuario(nombre)  # Llama a la función para obtener los datos

        if juego is None or aciertos is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Pie(labels=juego, values=aciertos)  # Genera un gráfico circular con Plotly

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   Aciertos por Juego de: {nombre}',
        )

        fig = go.Figure(data=[trace1], layout=layout)  # Crea la figura con los datos y el layout

        graph_json = pio.to_json(fig)  # Convierte el gráfico a formato JSON

        return jsonify(graph_json)  # Devuelve el gráfico en formato JSON
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500

# Ruta que genera la gráfica de aciertos por fecha para un usuario
@app.route('/grafico_aciertos_vs_fecha_usuario', methods=['GET'])
def grafico_aciertos_vs_fecha_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)  # Obtiene el nombre del usuario

        fecha, aciertos = datos_aciertos_fecha_usuario(nombre)  # Llama a la función para obtener los datos

        if fecha is None or aciertos is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Scatter(x=fecha, y=aciertos, mode='lines+markers', name='Aciertos vs Fecha')  # Genera un gráfico de líneas con Plotly

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   Aciertos por Fecha de: {nombre}',
            xaxis_title='Fecha',
            yaxis_title='Aciertos',
            legend=dict(x=0, y=1),
            margin=dict(l=40, r=40, t=40, b=40)
        )

        fig = go.Figure(data=[trace1], layout=layout)  # Crea la figura con los datos y el layout

        graph_json = pio.to_json(fig)  # Convierte el gráfico a formato JSON

        return jsonify(graph_json)  # Devuelve el gráfico en formato JSON
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500

# Ruta que genera la gráfica de precisión por fecha para un usuario
@app.route('/grafico_pres_vs_fecha_usuario', methods=['GET'])
def grafico_pres_vs_fecha_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)  # Obtiene el nombre del usuario

        fecha, pres = datos_pres_fecha_usuario(nombre)  # Llama a la función para obtener los datos

        if fecha is None or pres is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Scatter(x=fecha, y=pres, mode='lines+markers', name='Precisión vs Fecha')  # Genera un gráfico de líneas con Plotly

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                  Precisión por Fecha de: {nombre}',
            xaxis_title='Fecha',
            yaxis_title='Precisión',
            legend=dict(x=0, y=1),
            margin=dict(l=40, r=40, t=40, b=40)
        )

        fig = go.Figure(data=[trace1], layout=layout)  # Crea la figura con los datos y el layout

        graph_json = pio.to_json(fig)  # Convierte el gráfico a formato JSON

        return jsonify(graph_json)  # Devuelve el gráfico en formato JSON
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500

# Ruta que genera la gráfica de precisión por edad
@app.route('/grafico_pres_vs_edad', methods=['GET'])
def grafico_pres_vs_edad():

    edad, pres = datos_precision_edad()  # Llama a la función para obtener los datos de precisión por edad

    if edad is None or pres is None:
        return jsonify({"error": "No se encontraron datos"}), 404

    trace1 = go.Scatter(x=edad, y=pres, mode='lines+markers', name='Precisión vs Edad')  # Genera un gráfico de líneas con Plotly

    layout = go.Layout(
        title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}     Promedio de precisión por Edad',
        xaxis_title='Edad',
        yaxis_title='Precisión',
        legend=dict(x=0, y=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig = go.Figure(data=[trace1], layout=layout)  # Crea la figura con los datos y el layout

    graph_json = pio.to_json(fig)  # Convierte el gráfico a formato JSON

    return jsonify(graph_json)  # Devuelve el gráfico en formato JSON

# Ruta que genera la gráfica de aciertos por edad
@app.route('/grafico_aciertos_vs_edad', methods=['GET'])
def grafico_aciertos_vs_edad():

    edad, pres = datos_aciertos_edad()  # Llama a la función para obtener los datos de aciertos por edad

    if edad is None or pres is None:
        return jsonify({"error": "No se encontraron datos"}), 404

    trace1 = go.Scatter(x=edad, y=pres, mode='lines+markers', name='Aciertos vs Edad')  # Genera un gráfico de líneas con Plotly

    layout = go.Layout(
        title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}     Promedio de aciertos por Edad',
        xaxis_title='Edad',
        yaxis_title='Aciertos',
        legend=dict(x=0, y=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig = go.Figure(data=[trace1], layout=layout)  # Crea la figura con los datos y el layout

    graph_json = pio.to_json(fig)  # Convierte el gráfico a formato JSON

    return jsonify(graph_json)  # Devuelve el gráfico en formato JSON

# Ruta que renderiza la página que muestra las gráficas
@app.route('/mostrar_grafica')
def mostrar_grafica():
    return render_template('grafica.html')  # Renderiza la página grafica.html

# Ejecución principal de la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # Ejecuta la aplicación en modo depuración
