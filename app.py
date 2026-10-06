import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "centro_capacitacion"
DB = "bd_capacitacion.db"
TABLAS = ("instructores", "cursos", "estudiantes", "inscripciones")


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = get_db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS instructores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        especialidad TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS cursos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        horas INTEGER NOT NULL,
        costo REAL NOT NULL DEFAULT 0,
        instructor_id INTEGER,
        FOREIGN KEY(instructor_id) REFERENCES instructores(id) ON DELETE SET NULL);
    CREATE TABLE IF NOT EXISTS estudiantes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ci TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        correo TEXT,
        fecha_nacimiento TEXT);
    CREATE TABLE IF NOT EXISTS inscripciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'Activa',
        estudiante_id INTEGER NOT NULL,
        curso_id INTEGER NOT NULL,
        FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
        FOREIGN KEY(curso_id) REFERENCES cursos(id) ON DELETE CASCADE);
    """)
    con.commit()
    con.close()


def ejecutar(sql, params=()):
    con = get_db()
    try:
        con.execute(sql, params)
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()


def consultar(sql, params=(), uno=False):
    con = get_db()
    cur = con.execute(sql, params)
    datos = cur.fetchone() if uno else cur.fetchall()
    con.close()
    return datos


@app.route("/")
def inicio():
    return redirect(url_for("cursos"))


# ---------- ELIMINAR (siempre vuelve a Inscripciones) ----------
@app.route("/eliminar/<tabla>/<int:id>")
def eliminar(tabla, id):
    if tabla in TABLAS:
        ejecutar(f"DELETE FROM {tabla} WHERE id=?", (id,))
        flash("Registro eliminado correctamente.")
    return redirect(url_for("inscripciones"))


# ---------- INSTRUCTORES ----------
@app.route("/instructores")
def instructores():
    return render_template("instructores.html",
                           datos=consultar("SELECT * FROM instructores"))


@app.route("/instructor/nuevo", methods=["GET", "POST"])
def nuevo_instructor():
    if request.method == "POST":
        ejecutar("INSERT INTO instructores(nombre, especialidad) VALUES(?,?)",
                 (request.form["nombre"], request.form["especialidad"]))
        return redirect(url_for("instructores"))
    return render_template("instructor_form.html", titulo="Nuevo Instructor", i=None)


@app.route("/instructor/editar/<int:id>", methods=["GET", "POST"])
def editar_instructor(id):
    if request.method == "POST":
        ejecutar("UPDATE instructores SET nombre=?, especialidad=? WHERE id=?",
                 (request.form["nombre"], request.form["especialidad"], id))
        return redirect(url_for("instructores"))
    i = consultar("SELECT * FROM instructores WHERE id=?", (id,), uno=True)
    return render_template("instructor_form.html", titulo="Editar Instructor", i=i)


# ---------- CURSOS ----------
@app.route("/cursos")
def cursos():
    datos = consultar("""SELECT c.*, i.nombre AS instructor FROM cursos c
                         LEFT JOIN instructores i ON i.id = c.instructor_id""")
    return render_template("cursos.html", datos=datos)


@app.route("/curso/nuevo", methods=["GET", "POST"])
def nuevo_curso():
    if request.method == "POST":
        ejecutar("INSERT INTO cursos(descripcion, horas, costo, instructor_id) VALUES(?,?,?,?)",
                 (request.form["descripcion"], request.form["horas"],
                  request.form["costo"], request.form.get("instructor_id") or None))
        return redirect(url_for("cursos"))
    return render_template("curso_form.html", titulo="Nuevo Curso", c=None,
                           instructores=consultar("SELECT * FROM instructores"))


@app.route("/curso/editar/<int:id>", methods=["GET", "POST"])
def editar_curso(id):
    if request.method == "POST":
        ejecutar("UPDATE cursos SET descripcion=?, horas=?, costo=?, instructor_id=? WHERE id=?",
                 (request.form["descripcion"], request.form["horas"],
                  request.form["costo"], request.form.get("instructor_id") or None, id))
        return redirect(url_for("cursos"))
    c = consultar("SELECT * FROM cursos WHERE id=?", (id,), uno=True)
    return render_template("curso_form.html", titulo="Editar Curso", c=c,
                           instructores=consultar("SELECT * FROM instructores"))


# ---------- ESTUDIANTES ----------
@app.route("/estudiantes")
def estudiantes():
    return render_template("estudiantes.html",
                           datos=consultar("SELECT * FROM estudiantes"))


@app.route("/estudiante/nuevo", methods=["GET", "POST"])
def nuevo_estudiante():
    if request.method == "POST":
        ok = ejecutar("""INSERT INTO estudiantes(ci, nombre, apellidos, correo, fecha_nacimiento)
                         VALUES(?,?,?,?,?)""",
                      (request.form["ci"], request.form["nombre"], request.form["apellidos"],
                       request.form["correo"], request.form["fecha_nacimiento"]))
        if not ok:
            flash("Ya existe un estudiante con ese CI.")
            return redirect(url_for("nuevo_estudiante"))
        return redirect(url_for("estudiantes"))
    return render_template("estudiante_form.html", titulo="Nuevo Estudiante", e=None)


@app.route("/estudiante/editar/<int:id>", methods=["GET", "POST"])
def editar_estudiante(id):
    if request.method == "POST":
        ok = ejecutar("""UPDATE estudiantes SET ci=?, nombre=?, apellidos=?, correo=?,
                         fecha_nacimiento=? WHERE id=?""",
                      (request.form["ci"], request.form["nombre"], request.form["apellidos"],
                       request.form["correo"], request.form["fecha_nacimiento"], id))
        if not ok:
            flash("Ya existe un estudiante con ese CI.")
            return redirect(url_for("editar_estudiante", id=id))
        return redirect(url_for("estudiantes"))
    e = consultar("SELECT * FROM estudiantes WHERE id=?", (id,), uno=True)
    return render_template("estudiante_form.html", titulo="Editar Estudiante", e=e)


# ---------- INSCRIPCIONES ----------
@app.route("/inscripciones")
def inscripciones():
    datos = consultar("""SELECT i.id, i.fecha, i.estado,
                         e.nombre || ' ' || e.apellidos AS estudiante,
                         c.descripcion AS curso
                         FROM inscripciones i
                         JOIN estudiantes e ON e.id = i.estudiante_id
                         JOIN cursos c ON c.id = i.curso_id""")
    return render_template("inscripciones.html", datos=datos)


@app.route("/inscripcion/nueva", methods=["GET", "POST"])
def nueva_inscripcion():
    estudiantes = consultar("SELECT * FROM estudiantes")
    cursos = consultar("SELECT * FROM cursos")
    if request.method == "POST":
        if not request.form.get("estudiante_id") or not request.form.get("curso_id"):
            flash("Primero registra al menos un estudiante y un curso.")
            return redirect(url_for("nueva_inscripcion"))
        ejecutar("""INSERT INTO inscripciones(fecha, estado, estudiante_id, curso_id)
                    VALUES(?,?,?,?)""",
                 (request.form["fecha"], request.form["estado"],
                  request.form["estudiante_id"], request.form["curso_id"]))
        return redirect(url_for("inscripciones"))
    return render_template("inscripcion_form.html", estudiantes=estudiantes, cursos=cursos)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
