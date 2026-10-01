import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "centro_capacitacion"
DB = "bd_centro_capacitacion.db"


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = get_db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS cursos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        horas INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS estudiantes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        fecha_nacimiento TEXT);
    CREATE TABLE IF NOT EXISTS inscripciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        curso_id INTEGER NOT NULL,
        estudiante_id INTEGER NOT NULL,
        FOREIGN KEY(curso_id) REFERENCES cursos(id),
        FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id));
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


# ---------- CURSOS ----------
@app.route("/cursos")
def cursos():
    return render_template("cursos.html", cursos=consultar("SELECT * FROM cursos"))


@app.route("/nuevo_curso", methods=["GET", "POST"])
def nuevo_curso():
    if request.method == "POST":
        ejecutar("INSERT INTO cursos(descripcion, horas) VALUES(?,?)",
                 (request.form["descripcion"], request.form["horas"]))
        return redirect(url_for("cursos"))
    return render_template("nuevo_curso.html")


@app.route("/editar_curso/<int:id>", methods=["GET", "POST"])
def editar_curso(id):
    if request.method == "POST":
        ejecutar("UPDATE cursos SET descripcion=?, horas=? WHERE id=?",
                 (request.form["descripcion"], request.form["horas"], id))
        return redirect(url_for("cursos"))
    curso = consultar("SELECT * FROM cursos WHERE id=?", (id,), uno=True)
    return render_template("editar_curso.html", curso=curso)


@app.route("/eliminar_curso/<int:id>")
def eliminar_curso(id):
    if not ejecutar("DELETE FROM cursos WHERE id=?", (id,)):
        flash("No se puede eliminar: el curso tiene inscripciones.")
    return redirect(url_for("cursos"))


# ---------- ESTUDIANTES ----------
@app.route("/estudiantes")
def estudiantes():
    return render_template("estudiantes.html",
                           estudiantes=consultar("SELECT * FROM estudiantes"))


@app.route("/nuevo_estudiante", methods=["GET", "POST"])
def nuevo_estudiante():
    if request.method == "POST":
        ejecutar("INSERT INTO estudiantes(nombre, apellidos, fecha_nacimiento) VALUES(?,?,?)",
                 (request.form["nombre"], request.form["apellidos"],
                  request.form["fecha_nacimiento"]))
        return redirect(url_for("estudiantes"))
    return render_template("nuevo_estudiante.html")


@app.route("/editar_estudiante/<int:id>", methods=["GET", "POST"])
def editar_estudiante(id):
    if request.method == "POST":
        ejecutar("UPDATE estudiantes SET nombre=?, apellidos=?, fecha_nacimiento=? WHERE id=?",
                 (request.form["nombre"], request.form["apellidos"],
                  request.form["fecha_nacimiento"], id))
        return redirect(url_for("estudiantes"))
    est = consultar("SELECT * FROM estudiantes WHERE id=?", (id,), uno=True)
    return render_template("editar_estudiante.html", estudiante=est)


@app.route("/eliminar_estudiante/<int:id>")
def eliminar_estudiante(id):
    if not ejecutar("DELETE FROM estudiantes WHERE id=?", (id,)):
        flash("No se puede eliminar: el estudiante tiene inscripciones.")
    return redirect(url_for("estudiantes"))


# ---------- INSCRIPCIONES ----------
SQL_INSC = """SELECT i.id, i.fecha, e.nombre || ' ' || e.apellidos AS estudiante,
              c.descripcion AS curso
              FROM inscripciones i
              JOIN estudiantes e ON e.id = i.estudiante_id
              JOIN cursos c ON c.id = i.curso_id"""


@app.route("/inscripciones")
def inscripciones():
    return render_template("inscripciones.html", inscripciones=consultar(SQL_INSC))


@app.route("/nueva_inscripcion", methods=["GET", "POST"])
def nueva_inscripcion():
    if request.method == "POST":
        ejecutar("INSERT INTO inscripciones(fecha, estudiante_id, curso_id) VALUES(?,?,?)",
                 (request.form["fecha"], request.form["estudiante_id"],
                  request.form["curso_id"]))
        return redirect(url_for("inscripciones"))
    return render_template("nueva_inscripcion.html",
                           estudiantes=consultar("SELECT * FROM estudiantes"),
                           cursos=consultar("SELECT * FROM cursos"))


@app.route("/editar_inscripcion/<int:id>", methods=["GET", "POST"])
def editar_inscripcion(id):
    if request.method == "POST":
        ejecutar("UPDATE inscripciones SET fecha=?, estudiante_id=?, curso_id=? WHERE id=?",
                 (request.form["fecha"], request.form["estudiante_id"],
                  request.form["curso_id"], id))
        return redirect(url_for("inscripciones"))
    insc = consultar("SELECT * FROM inscripciones WHERE id=?", (id,), uno=True)
    return render_template("editar_inscripcion.html", insc=insc,
                           estudiantes=consultar("SELECT * FROM estudiantes"),
                           cursos=consultar("SELECT * FROM cursos"))


@app.route("/eliminar_inscripcion/<int:id>")
def eliminar_inscripcion(id):
    ejecutar("DELETE FROM inscripciones WHERE id=?", (id,))
    return redirect(url_for("inscripciones"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
