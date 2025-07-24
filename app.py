from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'projetoepratica'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'aluno',
    'password': 'ifpecjbg',
    'database': 'lembreMed'
}

def conectar_mysql():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        flash('Erro ao conectar ao banco de dados', 'error')
        raise

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, faça login para acessar esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verificar_tabelas():
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        
        # Verificar/criar tabela de responsáveis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responsaveis_login (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                parentesco VARCHAR(50),
                telefone VARCHAR(20),
                email VARCHAR(100) NOT NULL UNIQUE,
                senha VARCHAR(255) NOT NULL
            )
        """)
        
        # Verificar/criar tabela de idosos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS idosos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                idade INT NOT NULL,
                sexo VARCHAR(20),
                telefone VARCHAR(20),
                email VARCHAR(100),
                doencas TEXT,
                id_cuidador INT NOT NULL,
                FOREIGN KEY (id_cuidador) REFERENCES responsaveis_login(id)
            )
        """)
        
        # Verificar/criar tabela de remédios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS remedios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_comercial VARCHAR(100) NOT NULL,
                principio_ativo VARCHAR(100) NOT NULL,
                dosagem VARCHAR(50),
                forma_farmaceutica VARCHAR(50) NOT NULL,
                descricao TEXT,
                horario TIME NOT NULL,
                dias VARCHAR(100) NOT NULL,
                id_id INT NOT NULL,
                FOREIGN KEY (id_id) REFERENCES idosos(id)
            )
        """)
        
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao verificar/criar tabelas: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def obter_idosos_do_usuario(usuario_id):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome FROM idosos WHERE id_cuidador = %s", (usuario_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao obter idosos: {err}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/')
def inicio():
    return render_template('inicio.html', logado='usuario_id' in session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        try:
            conn = conectar_mysql()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM responsaveis_login WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            
            if usuario and check_password_hash(usuario['senha'], senha):
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))  # Redirecionar para dashboard
            else:
                flash('E-mail ou senha incorretos', 'error')
        except mysql.connector.Error as err:
            print(f"Erro ao fazer login: {err}")
            flash('Erro ao conectar com o banco de dados', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado', 'success')
    return redirect(url_for('inicio'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', nome=session.get('usuario_nome'))

@app.route('/criar-conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'parentesco': request.form['parentesco'],
            'telefone': request.form.get('telefone'),
            'email': request.form['email'],
            'senha': request.form['senha']
        }
        
        if request.form['senha'] != request.form['confirmar_senha']:
            flash('As senhas não coincidem', 'error')
        else:
            try:
                conn = conectar_mysql()
                cursor = conn.cursor()
                sql = '''
                    INSERT INTO responsaveis_login (nome, parentesco, telefone, email, senha)
                    VALUES (%s, %s, %s, %s, %s)
                '''
                senha_hash = generate_password_hash(dados['senha'])
                valores = (dados['nome'], dados['parentesco'], dados['telefone'], dados['email'], senha_hash)
                cursor.execute(sql, valores)
                conn.commit()
                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.IntegrityError:
                flash('Este e-mail já está cadastrado', 'error')
            except mysql.connector.Error as err:
                print(f"Erro ao criar conta: {err}")
                flash('Erro ao criar conta. Tente novamente.', 'error')
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
    
    return render_template('criar_conta.html')

@app.route('/cadastro-idoso', methods=['GET', 'POST'])
@login_required
def cadastro_idoso():
    if request.method == 'POST':
        dados = {
            'nome': request.form['nome'],
            'idade': request.form['idade'],
            'sexo': request.form['sexo'],
            'telefone': request.form['telefone'],
            'email': request.form.get('email'),
            'doencas': request.form.get('doencas'),
            'id_cuidador': session['usuario_id']
        }
        
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            sql = '''
                INSERT INTO idosos (nome, idade, sexo, telefone, email, doencas, id_cuidador)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (
                dados['nome'],
                dados['idade'],
                dados['sexo'],
                dados['telefone'],
                dados['email'],
                dados['doencas'],
                dados['id_cuidador']
            )
            cursor.execute(sql, valores)
            conn.commit()
            flash('Idoso cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_idoso'))
        except mysql.connector.Error as err:
            print(f"Erro ao cadastrar idoso: {err}")
            flash('Erro ao cadastrar idoso. Tente novamente.', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('cadastro_idoso.html')

@app.route('/cadastro-remedio', methods=['GET', 'POST'])
@login_required
def cadastro_remedio():
    idosos = obter_idosos_do_usuario(session['usuario_id'])
    
    if request.method == 'POST':
        dados = {
            'nome_comercial': request.form['nome_comercial'],
            'principio_ativo': request.form['principio_ativo'],
            'dosagem': request.form.get('dosagem'),
            'forma_farmaceutica': request.form['forma_farmaceutica'],
            'descricao': request.form.get('descricao'),
            'horario': request.form['horario'],
            'dias': request.form['dias'],
            'id_id': request.form['id_id']
        }
        
        try:
            conn = conectar_mysql()
            cursor = conn.cursor()
            sql = '''
                INSERT INTO remedios (nome_comercial, principio_ativo, dosagem, forma_farmaceutica, descricao, horario, dias, id_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            valores = (
                dados['nome_comercial'],
                dados['principio_ativo'],
                dados['dosagem'],
                dados['forma_farmaceutica'],
                dados['descricao'],
                dados['horario'],
                dados['dias'],
                dados['id_id']
            )
            cursor.execute(sql, valores)
            conn.commit()
            flash('Remédio cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_remedio'))
        except mysql.connector.Error as err:
            print(f"Erro ao cadastrar remédio: {err}")
            flash('Erro ao cadastrar remédio. Tente novamente.', 'error')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('cadastro_remedio.html', idosos=idosos)

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html', logado='usuario_id' in session)

if __name__ == '__main__':
    verificar_tabelas()  # Verifica e cria tabelas se necessário
    app.run(debug=True)