from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import db

app = Flask(__name__)
app.secret_key = "brut-barbershop-secret-2026"

@app.route("/")
def index():
    stats = db.get_stats()
    appointments = db.get_all_appointments()
    return render_template("index.html", stats=stats, appointments=appointments)

@app.route("/services")
def services():
    svcs = db.conn.execute("SELECT * FROM services ORDER BY id").fetchall()
    return render_template("services.html", services=svcs)

@app.route("/services/add", methods=["POST"])
def add_service():
    db.add_service(request.form["name"], int(request.form["price"]), int(request.form["duration"]), request.form["description"])
    return redirect(url_for("services"))

@app.route("/services/edit/<int:sid>", methods=["POST"])
def edit_service(sid):
    db.update_service(sid, request.form["name"], int(request.form["price"]), int(request.form["duration"]), request.form["description"])
    return redirect(url_for("services"))

@app.route("/services/toggle/<int:sid>")
def toggle_service(sid):
    db.toggle_service(sid)
    return redirect(url_for("services"))

@app.route("/masters")
def masters():
    ms = db.conn.execute("SELECT * FROM masters ORDER BY id").fetchall()
    return render_template("masters.html", masters=ms)

@app.route("/masters/add", methods=["POST"])
def add_master():
    db.add_master(request.form["name"], request.form["role"], request.form["description"], int(request.form["experience"]))
    return redirect(url_for("masters"))

@app.route("/masters/edit/<int:mid>", methods=["POST"])
def edit_master(mid):
    db.update_master(mid, request.form["name"], request.form["role"], request.form["description"], int(request.form["experience"]))
    return redirect(url_for("masters"))

@app.route("/masters/toggle/<int:mid>")
def toggle_master(mid):
    db.toggle_master(mid)
    return redirect(url_for("masters"))

@app.route("/appointments")
def appointments():
    apts = db.conn.execute("""
        SELECT a.*, s.name as service_name, s.price, m.name as master_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN masters m ON a.master_id = m.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """).fetchall()
    return render_template("appointments.html", appointments=apts)

@app.route("/appointments/cancel/<int:apt_id>")
def cancel_appointment(apt_id):
    db.cancel_appointment(apt_id)
    return redirect(url_for("appointments"))

@app.route("/appointments/done/<int:apt_id>")
def done_appointment(apt_id):
    db.done_appointment(apt_id)
    return redirect(url_for("appointments"))

@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())

def run_web():
    from config import WEB_HOST, WEB_PORT
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)

if __name__ == "__main__":
    run_web()