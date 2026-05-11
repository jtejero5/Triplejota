from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'novasalut_secret_key_2026'

# --- CONEXIÓN A AMAZON AURORA (Datos de Jaume) ---
DB_USER = 'admin'
DB_PASS = 'Passw0rd!:.'
DB_HOST = 'aurora-cluster.cluster-cy85ltnhoq9c.us-east-1.rds.amazonaws.com'
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
    return render_template('index.html')

# NUEVA RUTA: REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        dni_f = request.form.get('dni')
        nombre_f = request.form.get('nombre')
        pass_f = request.form.get('password')

        existe = Paciente.query.filter_by(dni=dni_f).first()
        if existe:
            flash('El DNI ya está registrado.', 'danger')
            return redirect(url_for('register'))

        nuevo_paciente = Paciente(dni=dni_f, nombre=nombre_f, password=pass_f)
        try:
            db.session.add(nuevo_paciente)
            db.session.commit()
            flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni_f = request.form.get('dni')
        pass_f = request.form.get('password')
        user = Paciente.query.filter_by(dni=dni_f).first()
        if user and user.password == pass_f:
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            flash(f'Bienvenido, {user.nombre}', 'success')
            return redirect(url_for('home'))
        else:
            flash('DNI o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/citas', methods=['GET', 'POST'])
def citas():
    if 'user_id' not in session:
        flash('Inicie sesión primero.', 'warning')
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
            flash('✅ Cita guardada.', 'success')
            return redirect(url_for('historial'))
        except Exception as e:
            db.session.rollback()
            flash('❌ Error al guardar.', 'danger')
    return render_template('citas.html')

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mis_citas = Cita.query.filter_by(paciente_id=session['user_id']).all()
    return render_template('historial.html', citas=mis_citas)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
