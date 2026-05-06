from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Clave secreta necesaria para las sesiones y mensajes flash
app.secret_key = 'novasalut_secret_key_2026'

# --- CONFIGURACIÓN DE CONEXIÓN A AMAZON AURORA (Datos de Jaume) ---
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
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

# --- INICIALIZACIÓN Y USUARIO DE PRUEBA ---
with app.app_context():
    db.create_all()
    # Creamos un usuario de prueba para que puedas loguearte nada más arrancar
    if not Paciente.query.filter_by(dni='12345678A').first():
        user_test = Paciente(dni='12345678A', nombre='Jose Tejero', password='admin')
        db.session.add(user_test)
        db.session.commit()
        print("👤 Usuario de prueba creado: 12345678A / admin")

# --- RUTAS DE NAVEGACIÓN Y LOGIN ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni_f = request.form.get('dni')
        pass_f = request.form.get('password')

        # Buscamos al paciente en Aurora
        user = Paciente.query.filter_by(dni=dni_f).first()

        if user and user.password == pass_f:
            # Login correcto: Guardamos datos en la sesión
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            flash(f'Bienvenido de nuevo, {user.nombre}', 'success')
            return redirect(url_for('home'))
        else:
            # Login incorrecto
            flash('DNI o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/citas', methods=['GET', 'POST'])
def citas():
    # 1. Comprobar seguridad: ¿Ha hecho login el usuario?
    if 'user_id' not in session:
        flash('Acceso denegado. Por favor, inicie sesión para pedir una cita.', 'warning')
        return redirect(url_for('login'))

    # 2. Si el usuario envía el formulario (POST)
    if request.method == 'POST':
        try:
            # Recoger los datos del formulario HTML
            f_especialidad = request.form.get('especialidad')
            f_medico = request.form.get('medico')
            f_fecha = request.form.get('fecha')
            f_horario = request.form.get('horario')

            # Crear el objeto Cita y enlazarlo con el ID del paciente logueado
            nueva_cita = Cita(
                fecha=f_fecha,
                horario=f_horario,
                especialidad=f_especialidad,
                medico=f_medico,
                paciente_id=session['user_id']
            )

            # Insertar en Amazon Aurora
            db.session.add(nueva_cita)
            db.session.commit()

            flash('✅ ¡Cita médica programada con éxito!', 'success')
            return redirect(url_for('historial')) # Lo mandamos al historial para verla

        except Exception as e:
            db.session.rollback() # Si falla, deshacemos los cambios por seguridad
            flash('❌ Ocurrió un error al guardar la cita en la nube.', 'danger')
            print(f"Error de BD: {e}")

    # 3. Si solo está visitando la página (GET), mostramos el formulario
    return render_template('citas.html')

@app.route('/historial')
def historial():
    return render_template('historial.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)