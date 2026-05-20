from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'novasalut_secret_key_2026'

# --- CONEXIÓN A AMAZON AURORA (Datos de Jaume) ---
DB_USER = 'admin'
DB_PASS = 'Passw0rd!:.'
DB_HOST = 'auroracluster.cluster-ccvsi5zk9s0d.us-east-1.rds.amazonaws.com'
DB_NAME = 'triplejota_db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---
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

# --- INICIALIZACIÓN ---
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error inicializando DB: {e}")

# --- RUTAS ---

@app.route('/')
def home():
    # Si el usuario está logueado, le pasamos sus citas para que el Dashboard sea dinámico
    citas_count = 0
    if 'user_id' in session:
        citas_count = Cita.query.filter_by(paciente_id=session['user_id']).count()
    return render_template('index.html', citas_count=citas_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        dni_f = request.form.get('dni')
        nombre_f = request.form.get('nombre')
        pass_f = request.form.get('password')
        existe = Paciente.query.filter_by(dni=dni_f).first()
        if existe:
            flash('Este DNI ya está registrado.', 'warning')
            return redirect(url_for('register'))
        nuevo = Paciente(dni=dni_f, nombre=nombre_f, password=pass_f)
        db.session.add(nuevo)
        db.session.commit()
        flash('Registro completado. Ya puede entrar.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Paciente.query.filter_by(dni=request.form.get('dni')).first()
        if user and user.password == request.form.get('password'):
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            return redirect(url_for('home'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/citas', methods=['GET', 'POST'])
def citas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        nueva = Cita(
            fecha=request.form.get('fecha'),
            horario=request.form.get('horario'),
            especialidad=request.form.get('especialidad'),
            medico=request.form.get('medico'),
            observaciones=request.form.get('observaciones'),
            paciente_id=session['user_id']
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Cita programada correctamente.', 'success')
        return redirect(url_for('historial'))
    return render_template('citas.html')

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mis_citas = Cita.query.filter_by(paciente_id=session['user_id']).all()
    return render_template('historial.html', citas=mis_citas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
