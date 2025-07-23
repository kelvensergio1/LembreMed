from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Troque por uma chave segura em produção

# Configurações do banco de dados
def conectar_mysql():
    return mysql.connector.connect(
        host='localhost',
        user='aluno',
        password='ifpecjbg',
        database='lembreMed'
    )

# Funções de banco de dados
def salvar_responsavel(dados):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        sql = '''
            INSERT INTO responsaveis_login (nome, parentesco, telefone, email, senha)
            VALUES (%s, %s, %s, %s, %s)
        '''
        # Hash da senha antes de armazenar
        senha_hash = generate_password_hash(dados['senha'])
        valores = (dados['nome'], dados['parentesco'], dados.get('telefone'), dados['email'], senha_hash)
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar responsável: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def salvar_idoso(dados):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        sql = '''
            INSERT INTO idosos (nome, idade, sexo, telefone, email, id_cuidador)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        valores = (
            dados.get('nome'),
            dados['idade'],
            dados.get('sexo'),
            dados.get('telefone'),
            dados['email'],
            dados['id_cuidador']
        )
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar idoso: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def salvar_remedio(dados):
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        sql = '''
            INSERT INTO remedios (nome_comercial, principio_ativo, dosagem, forma_farmaceutica, descricao, horario, dias, id_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        valores = (
            dados.get('nome_comercial'),
            dados['principio_ativo'],
            dados.get('dosagem'),
            dados['forma_farmaceutica'],
            dados.get('descricao'),
            dados['horario'],
            dados['dias'],
            dados['id_id']
        )
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Erro ao salvar remédio: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Rotas
@app.route('/')
def inicio():
    return render_template('inicio.html')

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
                return redirect(url_for('inicio'))
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
    return redirect(url_for('inicio'))

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
        elif salvar_responsavel(dados):
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Erro ao criar conta. Tente novamente.', 'error')
    
    return render_template('criar_conta.html')

@app.route('/cadastro-idoso', methods=['GET', 'POST'])
def cadastro_idoso():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        dados = {
            'nome': request.form.get('nome'),
            'idade': request.form['idade'],
            'sexo': request.form.get('sexo'),
            'telefone': request.form.get('telefone'),
            'email': request.form['email'],
            'id_cuidador': session['usuario_id']
        }
        
        if salvar_idoso(dados):
            flash('Idoso cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_idoso'))
        else:
            flash('Erro ao cadastrar idoso. Tente novamente.', 'error')
    
    return render_template('cadastro_idoso.html')

@app.route('/cadastro-remedio', methods=['GET', 'POST'])
def cadastro_remedio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        dados = {
            'nome_comercial': request.form.get('nome_comercial'),
            'principio_ativo': request.form['principio_ativo'],
            'dosagem': request.form.get('dosagem'),
            'forma_farmaceutica': request.form['forma_farmaceutica'],
            'descricao': request.form.get('descricao'),
            'horario': request.form['horario'],
            'dias': request.form['dias'],
            'id_id': request.form['id_id']
        }
        
        if salvar_remedio(dados):
            flash('Remédio cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastro_remedio'))
        else:
            flash('Erro ao cadastrar remédio. Tente novamente.', 'error')
    
    return render_template('cadastro_remedio.html')

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

if __name__ == '__main__':
    app.run(debug=True)