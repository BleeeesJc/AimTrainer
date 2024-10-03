import csv
from datetime import datetime
from flask import Flask, jsonify, request,render_template,redirect, send_file, url_for,session,Response
import mysql.connector
import plotly.graph_objects as go
import plotly.io as pio
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


def exportar_resultados_a_csv(nombre_archivo):
    try:
        # Conexión a la base de datos
        conn = conn = connect_to_database()
        cursor = conn.cursor()

        # Consulta SQL para obtener los resultados de los jugadores
        query = """
            SELECT u.usuario AS nombre_usuario, tj.nombre AS tipo_juego, r.aciertos, r.pre AS `precision`, r.tiempo, r.fecha
            FROM resultados r
            JOIN usuarios u ON r.idUsuario = u.idUsuario
            JOIN tipo_juego tj ON r.idTipo = tj.idTipo
            ORDER BY u.usuario, r.fecha;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()

        if not resultados:
            print("No se encontraron resultados.")
            return

        # Escribir los resultados en un archivo CSV
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)

            # Escribir la fila de encabezados
            escritor_csv.writerow(['nombre_usuario', 'tipo_juego', 'aciertos', 'precision', 'tiempo', 'fecha'])

            # Escribir los resultados obtenidos
            for fila in resultados:
                escritor_csv.writerow(fila)

        print(f"Los resultados se han guardado correctamente en el archivo {nombre_archivo}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error al exportar los resultados a CSV: {e}")

# Ruta que genera y descarga el archivo CSV
@app.route('/descargar_csv')
def descargar_csv():
    # Nombre del archivo CSV
    nombre_archivo = 'resultados_jugadores.csv'

    # Generar el archivo CSV
    exportar_resultados_a_csv(nombre_archivo)

    # Enviar el archivo CSV para su descarga
    return send_file(nombre_archivo, as_attachment=True, download_name=nombre_archivo)        

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

@app.route('/usuarios', methods=['GET'])
def list_users():
    conn = connect_to_database()
    cursor = conn.cursor()

    query = "SELECT * FROM usuarios"
    cursor.execute(query)
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('crud.html', usuarios=usuarios)

@app.route('/usuarios/update/<int:id>', methods=['POST'])
def update_user(id):
    conn = connect_to_database()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener los nuevos datos enviados en el cuerpo de la solicitud
        data = request.get_json()
        nuevo_usuario = data['usuario']
        nuevo_email = data['email']
        nueva_edad = data['edad']

        try:
            query = "UPDATE usuarios SET usuario = %s, correo = %s, edad = %s WHERE idUsuario = %s"
            values = (nuevo_usuario, nuevo_email, nueva_edad, id)
            cursor.execute(query, values)
            conn.commit()
            return jsonify({"message": "Actualizado exitosamente"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()
            conn.close()

@app.route('/usuarios/delete/<int:id>', methods=['POST'])
def delete_user(id):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        query = "DELETE FROM usuarios WHERE idUsuario = %s"
        cursor.execute(query, (id,))
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
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

@app.route('/grafica')
def grafica():
    return render_template('grafica.html')


#Funcion para obtener el promedio de precision por edad
@app.route('/grafica_precision_edad', methods=['GET'])
def datos_precision_edad():
    conn = connect_to_database()
    cursor = conn.cursor()

    query = """SELECT u.edad, AVG(r.pre) AS media_precision
        FROM usuarios u
        JOIN resultados r ON u.idUsuario = r.idUsuario
        GROUP BY u.edad;"""
    cursor.execute(query)
    resultados = cursor.fetchall()
        
    if not resultados:
        print("No se encontraron datos")
        return None, None
    
    edad = []
    pres = []

    for fila in resultados:
        edad.append(fila[0])
        pres.append(fila[1])

    cursor.close()
    conn.close()

    return edad, pres

# Funcion para obtener el promedio de aciertos por edad
@app.route('/datos_aciertos_edad', methods=['GET'])
def datos_aciertos_edad():
    conn = connect_to_database()
    cursor = conn.cursor()

    query = """SELECT u.edad, AVG(r.aciertos) AS promedio_aciertos
                FROM usuarios u
                JOIN resultados r ON u.idUsuario = r.idUsuario
                GROUP BY u.edad;"""
    cursor.execute(query)
    resultados = cursor.fetchall()
        
    if not resultados:
        print("No se encontraron datos")
        return None, None
    
    edad = []
    aciertos = []

    for fila in resultados:
        edad.append(fila[0])
        aciertos.append(fila[1])

    cursor.close()
    conn.close()

    return edad, aciertos

# Funcion para obtener la precision por usuarios y por fechas
@app.route('/datos_pres_fecha_usuario', methods=['GET'])
def datos_pres_fecha_usuario(nombre):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        query = """SELECT r.fecha, r.pre
                   FROM resultados r
                   JOIN usuarios u ON r.idUsuario = u.idUsuario
                   WHERE u.usuario = %s
                   ORDER BY r.fecha ASC;"""
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        fecha = []
        pres = []

        for fila in resultados:
            fecha.append(fila[0]) 
            pres.append(fila[1]) 

        cursor.close()
        conn.close()

        return fecha, pres 
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None

# Funcion para obtener los aciertos por usuarios y por fechas
@app.route('/datos_aciertos_fecha_usuario', methods=['GET'])
def datos_aciertos_fecha_usuario(nombre):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        query = """SELECT r.fecha, r.aciertos
                   FROM resultados r
                   JOIN usuarios u ON r.idUsuario = u.idUsuario
                   WHERE u.usuario = %s
                   ORDER BY r.fecha ASC;"""
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        fecha = []
        aciertos = []

        for fila in resultados:
            fecha.append(fila[0]) 
            aciertos.append(fila[1])  

        cursor.close()
        conn.close()

        return fecha, aciertos 
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None
    
# Funcion para obtener los aciertos por usuarios y por tipo de juego
@app.route('/datos_aciertos_juego_usuario', methods=['GET'])
def datos_aciertos_juego_usuario(nombre):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        query = """SELECT tj.nombre AS tipo_juego, SUM(r.aciertos) AS total_aciertos
                    FROM resultados r
                    JOIN tipo_juego tj ON r.idTipo = tj.idTipo
                    JOIN usuarios u ON r.idUsuario = u.idUsuario
                    WHERE u.usuario = %s
                    GROUP BY tj.nombre;
                    """
        cursor.execute(query, (nombre,))
        resultados = cursor.fetchall()

        if not resultados:
            print(f"No se encontraron resultados para el usuario: {nombre}")
            return None, None 

        juego = []
        aciertos = []

        for fila in resultados:
            juego.append(fila[0]) 
            aciertos.append(fila[1])  

        cursor.close()
        conn.close()

        return juego, aciertos 
    except Exception as e:
        print(f"Error en la función datos_aciertos_edad_usuario: {e}")
        return None, None

@app.route('/grafico_aciertos_juego_usuario', methods=['GET'])
def grafico_aciertos_juego_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)

        # Obtener solo 'fecha' y 'pres' de la función
        juego, aciertos = datos_aciertos_juego_usuario(nombre)

        if juego is None or aciertos is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Pie(labels=juego, values=aciertos)

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   Aciertos por Juego de: {nombre}',
        )

        fig = go.Figure(data=[trace1], layout=layout)

        graph_json = pio.to_json(fig)

        return jsonify(graph_json)
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500

@app.route('/grafico_aciertos_vs_fecha_usuario', methods=['GET'])
def grafico_aciertos_vs_fecha_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)

        # Obtener solo 'fecha' y 'pres' de la función
        fecha, aciertos = datos_aciertos_fecha_usuario(nombre)

        if fecha is None or aciertos is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Scatter(x=fecha, y=aciertos, mode='lines+markers', name='Precisión vs Edad')

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   Aciertos por Fecha de: {nombre}',
            xaxis_title='Fecha',
            yaxis_title='Aciertos',
            legend=dict(x=0, y=1),
            margin=dict(l=40, r=40, t=40, b=40)
        )

        fig = go.Figure(data=[trace1], layout=layout)

        graph_json = pio.to_json(fig)

        return jsonify(graph_json)
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500

@app.route('/grafico_pres_vs_fecha_usuario', methods=['GET'])
def grafico_pres_vs_fecha_usuario():
    try:
        nombre = request.args.get('nombre', default="Sara", type=str)

        # Obtener solo 'fecha' y 'pres' de la función
        fecha, pres = datos_pres_fecha_usuario(nombre)

        if fecha is None or pres is None:
            return jsonify({"error": f"No se encontraron datos para el usuario: {nombre}"}), 404

        trace1 = go.Scatter(x=fecha, y=pres, mode='lines+markers', name='Precisión vs Edad')

        layout = go.Layout(
            title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                  Precisión por Fecha de: {nombre}',
            xaxis_title='Fecha',
            yaxis_title='Precisión',
            legend=dict(x=0, y=1),
            margin=dict(l=40, r=40, t=40, b=40)
        )

        fig = go.Figure(data=[trace1], layout=layout)

        graph_json = pio.to_json(fig)

        return jsonify(graph_json)
    except Exception as e:
        print(f"Error en la ruta grafico_pres_vs_edad_usuario: {e}")
        return jsonify({"error": "Ocurrió un error en el servidor"}), 500


@app.route('/grafico_pres_vs_edad', methods=['GET'])
def grafico_pres_vs_edad():

    edad, pres = datos_precision_edad()

    if edad is None or pres is None:
        return jsonify({"error": "No se encontraron datos"}), 404

    trace1 = go.Scatter(x=edad, y=pres, mode='lines+markers', name='Precisión vs Edad')

    layout = go.Layout(
        title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}     Promedio de precision por Edad',
        xaxis_title='Edad',
        yaxis_title='Precisión',
        legend=dict(x=0, y=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig = go.Figure(data=[trace1], layout=layout)

    graph_json = pio.to_json(fig)

    return jsonify(graph_json)

@app.route('/grafico_aciertos_vs_edad', methods=['GET'])
def grafico_aciertos_vs_edad():

    edad, pres = datos_aciertos_edad()

    if edad is None or pres is None:
        return jsonify({"error": "No se encontraron datos"}), 404

    trace1 = go.Scatter(x=edad, y=pres, mode='lines+markers', name='Aciertos vs Edad')

    layout = go.Layout(
        title=f'Gráfico en tiempo real - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}     Promedio de aciertos por Edad',
        xaxis_title='Edad',
        yaxis_title='Aciertos',
        legend=dict(x=0, y=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig = go.Figure(data=[trace1], layout=layout)

    graph_json = pio.to_json(fig)

    return jsonify(graph_json)

@app.route('/mostrar_grafica')
def mostrar_grafica():
    return render_template('grafica.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)