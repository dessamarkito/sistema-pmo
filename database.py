import sqlite3
import hashlib
import os

# Garante que o banco persiste mesmo no Streamlit Cloud
DB_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "pmo.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em TEXT DEFAULT (date('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT DEFAULT 'Operacionais',
            area_demandante TEXT,
            pmo_responsavel TEXT,
            envolvidos TEXT,
            descricao TEXT,
            status TEXT DEFAULT '🔵 Não Iniciado',
            prioridade TEXT DEFAULT 'Média',
            fase TEXT DEFAULT 'Iniciação',
            inicio_previsto TEXT,
            fim_previsto TEXT,
            forecast_prazo TEXT,
            orcamento_aprovado REAL DEFAULT 0,
            orcamento_consumido REAL DEFAULT 0,
            forecast_custo REAL DEFAULT 0,
            qtd_replanejamentos INTEGER DEFAULT 0,
            motivo_replanejamento TEXT,
            observacoes TEXT,
            criado_por TEXT,
            criado_em TEXT DEFAULT (datetime('now')),
            atualizado_em TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            nome_arquivo TEXT NOT NULL,
            tipo_arquivo TEXT,
            conteudo BLOB NOT NULL,
            enviado_por TEXT,
            enviado_em TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (projeto_id) REFERENCES projetos(id)
        )
    """)

    # Usuários iniciais
    usuarios_iniciais = [
        ("Andressa Marquito", "andressa@pmo.com", "pmo@2025"),
        ("Ana Paula",         "ana@pmo.com",      "pmo@2025"),
        ("Bruno Silva",       "bruno@pmo.com",    "pmo@2025"),
        ("Carla Matos",       "carla@pmo.com",    "pmo@2025"),
        ("Daniel Costa",      "daniel@pmo.com",   "pmo@2025"),
    ]
    for nome, email, senha in usuarios_iniciais:
        c.execute("INSERT OR IGNORE INTO usuarios (nome, email, senha_hash) VALUES (?,?,?)",
                  (nome, email, hash_senha(senha)))

    c.execute("""
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT,
            responsavel TEXT,
            status TEXT DEFAULT 'Pendente',
            prioridade TEXT DEFAULT 'Média',
            data_prevista TEXT,
            data_conclusao TEXT,
            criado_por TEXT,
            criado_em TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (projeto_id) REFERENCES projetos(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS historico_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            status_anterior TEXT,
            status_novo TEXT NOT NULL,
            observacao TEXT,
            alterado_por TEXT,
            alterado_em TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (projeto_id) REFERENCES projetos(id)
        )
    """)

    # Migrações para bancos existentes
    for sql in [
        "ALTER TABLE projetos ADD COLUMN categoria TEXT DEFAULT 'Operacionais'",
    ]:
        try:
            c.execute(sql)
        except Exception:
            pass

    conn.commit()
    conn.close()

def autenticar(email, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE email=? AND senha_hash=?",
              (email, hash_senha(senha)))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def listar_projetos(filtro_status=None, filtro_area=None, filtro_pmo=None):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT * FROM projetos WHERE 1=1"
    params = []
    if filtro_status and filtro_status != "Todos":
        query += " AND status=?"
        params.append(filtro_status)
    if filtro_area and filtro_area != "Todos":
        query += " AND area_demandante=?"
        params.append(filtro_area)
    if filtro_pmo and filtro_pmo != "Todos":
        query += " AND pmo_responsavel=?"
        params.append(filtro_pmo)
    query += " ORDER BY id DESC"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def buscar_projeto(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM projetos WHERE id=?", (projeto_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def proximo_codigo():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM projetos")
    total = c.fetchone()["total"]
    conn.close()
    return f"PRJ-{total+1:03d}"

def salvar_projeto(dados, usuario):
    conn = get_conn()
    c = conn.cursor()
    if dados.get("id"):
        # Verifica se o status mudou antes de atualizar
        c.execute("SELECT status FROM projetos WHERE id=?", (dados["id"],))
        row = c.fetchone()
        status_anterior = row["status"] if row else None

        c.execute("""
            UPDATE projetos SET
                nome=?, categoria=?, area_demandante=?, pmo_responsavel=?, envolvidos=?,
                descricao=?, status=?, prioridade=?, fase=?,
                inicio_previsto=?, fim_previsto=?, forecast_prazo=?,
                orcamento_aprovado=?, orcamento_consumido=?, forecast_custo=?,
                qtd_replanejamentos=?, motivo_replanejamento=?, observacoes=?,
                atualizado_em=datetime('now')
            WHERE id=?
        """, (
            dados["nome"], dados["categoria"], dados["area_demandante"], dados["pmo_responsavel"],
            dados["envolvidos"], dados["descricao"], dados["status"],
            dados["prioridade"], dados["fase"], dados["inicio_previsto"],
            dados["fim_previsto"], dados["forecast_prazo"],
            dados["orcamento_aprovado"], dados["orcamento_consumido"],
            dados["forecast_custo"], dados["qtd_replanejamentos"],
            dados["motivo_replanejamento"], dados["observacoes"], dados["id"]
        ))

        if status_anterior != dados["status"]:
            c.execute("""
                INSERT INTO historico_status
                    (projeto_id, status_anterior, status_novo, observacao, alterado_por)
                VALUES (?,?,?,?,?)
            """, (dados["id"], status_anterior, dados["status"],
                  dados.get("obs_status", ""), usuario))

        new_id = None
    else:
        codigo = proximo_codigo()
        c.execute("""
            INSERT INTO projetos (
                codigo, nome, categoria, area_demandante, pmo_responsavel, envolvidos,
                descricao, status, prioridade, fase,
                inicio_previsto, fim_previsto, forecast_prazo,
                orcamento_aprovado, orcamento_consumido, forecast_custo,
                qtd_replanejamentos, motivo_replanejamento, observacoes, criado_por
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            codigo, dados["nome"], dados["categoria"], dados["area_demandante"], dados["pmo_responsavel"],
            dados["envolvidos"], dados["descricao"], dados["status"],
            dados["prioridade"], dados["fase"], dados["inicio_previsto"],
            dados["fim_previsto"], dados["forecast_prazo"],
            dados["orcamento_aprovado"], dados["orcamento_consumido"],
            dados["forecast_custo"], dados["qtd_replanejamentos"],
            dados["motivo_replanejamento"], dados["observacoes"], usuario
        ))
        new_id = c.lastrowid
        # Grava o status inicial no histórico
        c.execute("""
            INSERT INTO historico_status
                (projeto_id, status_anterior, status_novo, observacao, alterado_por)
            VALUES (?,?,?,?,?)
        """, (new_id, None, dados["status"], "Projeto criado", usuario))

    conn.commit()
    conn.close()
    return new_id

def listar_historico_status(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM historico_status
        WHERE projeto_id=? ORDER BY alterado_em DESC
    """, (projeto_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def salvar_documento(projeto_id, nome_arquivo, tipo_arquivo, conteudo, enviado_por):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO documentos (projeto_id, nome_arquivo, tipo_arquivo, conteudo, enviado_por)
        VALUES (?,?,?,?,?)
    """, (projeto_id, nome_arquivo, tipo_arquivo, conteudo, enviado_por))
    conn.commit()
    conn.close()

def listar_documentos(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, nome_arquivo, tipo_arquivo, enviado_por, enviado_em
        FROM documentos WHERE projeto_id=? ORDER BY enviado_em DESC
    """, (projeto_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def baixar_documento(doc_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT nome_arquivo, tipo_arquivo, conteudo FROM documentos WHERE id=?", (doc_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def excluir_documento(doc_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM documentos WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()

def excluir_projeto(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM projetos WHERE id=?", (projeto_id,))
    conn.commit()
    conn.close()

def trocar_senha(usuario_id, senha_atual, nova_senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT senha_hash FROM usuarios WHERE id=?", (usuario_id,))
    row = c.fetchone()
    if not row or row["senha_hash"] != hash_senha(senha_atual):
        conn.close()
        return False, "Senha atual incorreta."
    if len(nova_senha) < 6:
        conn.close()
        return False, "A nova senha deve ter pelo menos 6 caracteres."
    c.execute("UPDATE usuarios SET senha_hash=? WHERE id=?",
              (hash_senha(nova_senha), usuario_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"

def areas_distintas():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT area_demandante FROM projetos WHERE area_demandante IS NOT NULL")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def pmos_distintos():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT pmo_responsavel FROM projetos WHERE pmo_responsavel IS NOT NULL")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

# ── Tarefas ───────────────────────────────────────────────────────────

def listar_tarefas(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM tarefas WHERE projeto_id=?
        ORDER BY
            CASE prioridade WHEN 'Alta' THEN 1 WHEN 'Média' THEN 2 ELSE 3 END,
            data_prevista ASC
    """, (projeto_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def salvar_tarefa(dados, usuario):
    conn = get_conn()
    c = conn.cursor()
    if dados.get("id"):
        c.execute("""
            UPDATE tarefas SET
                titulo=?, descricao=?, responsavel=?, status=?,
                prioridade=?, data_prevista=?, data_conclusao=?
            WHERE id=?
        """, (
            dados["titulo"], dados["descricao"], dados["responsavel"],
            dados["status"], dados["prioridade"],
            dados["data_prevista"], dados["data_conclusao"], dados["id"]
        ))
    else:
        c.execute("""
            INSERT INTO tarefas
                (projeto_id, titulo, descricao, responsavel, status,
                 prioridade, data_prevista, criado_por)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            dados["projeto_id"], dados["titulo"], dados["descricao"],
            dados["responsavel"], dados["status"], dados["prioridade"],
            dados["data_prevista"], usuario
        ))
    conn.commit()
    conn.close()

def buscar_tarefa(tarefa_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tarefas WHERE id=?", (tarefa_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def excluir_tarefa(tarefa_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
    conn.commit()
    conn.close()

def metricas_tarefas(projeto_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT status FROM tarefas WHERE projeto_id=?", (projeto_id,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    total      = len(rows)
    concluidas = rows.count("Concluída")
    em_andamento = rows.count("Em Andamento")
    pendentes  = rows.count("Pendente")
    pct        = round(concluidas / total * 100) if total else 0
    return {"total": total, "concluidas": concluidas,
            "em_andamento": em_andamento, "pendentes": pendentes, "pct": pct}
