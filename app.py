from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'novasalut_secret_key_2026' # Seguridad para sesiones

# --- CONFIGURACIÓN DE CONEXIÓN A AMAZON AURORA (Clúster de Jaume) ---
DB_USER = 'admin'
DB_PASS = 'Passw0rd!:.'
DB_HOST = 'aurora-cluster.cluster-cy85ltnhoq9c.us-east-1.rds.amazonaws.com'
DB_NAME = 'triplejota_db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS (Tablas en AWS) ---
class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    citas = db.relationship('Cita', backref='paciente', lazy=True)

class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(20), nullable=False)
    horario = db.Column(db.String(20), nullable=False)
    especialidad = db.Column(db.String(50), nullable=False)
    medico = db.Column(db.String(100), nullable=False)
    observaciones = db.Column(db.String(250))
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
with app.app_context():
    db.create_all()
    # Usuario de prueba: 12345678A / admin
    if not Paciente.query.filter_by(dni='12345678A').first():
        user_test = Paciente(dni='12345678A', nombre='Jose Tejero', password='admin')
        db.session.add(user_test)
        db.session.commit()

# --- RUTAS ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni_f = request.form.get('dni')
        pass_f = request.form.get('password')
        user = Paciente.query.filter_by(dni=dni_f).first()

        if user and user.password == pass_f:
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            flash(f'Bienvenido al portal, {user.nombre}', 'success')
            return redirect(url_for('home'))
        else:
            flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/citas', methods=['GET', 'POST'])
def citas():
    if 'user_id' not in session:
        flash('Inicie sesión para solicitar una cita.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            nueva_cita = Cita(
                fecha=request.form.get('fecha'),
                horario=request.form.get('horario'),
                especialidad=request.form.get('especialidad'),
                medico=request.form.get('medico'),
                observaciones=request.form.get('observaciones'),
                paciente_id=session['user_id']
            )
            db.session.add(nueva_cita)
            db.session.commit()
            flash('✅ Cita guardada correctamente en Amazon Aurora.', 'success')
            return redirect(url_for('historial'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al guardar en la nube.', 'danger')
    return render_template('citas.html')

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mis_citas = Cita.query.filter_by(paciente_id=session['user_id']).all()
    return render_template('historial.html', citas=mis_citas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
