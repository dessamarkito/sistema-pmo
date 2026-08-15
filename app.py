import streamlit as st
from database import (init_db, autenticar, listar_projetos, buscar_projeto,
                      salvar_projeto, excluir_projeto, areas_distintas,
                      pmos_distintos, trocar_senha,
                      salvar_documento, listar_documentos,
                      baixar_documento, excluir_documento)

st.set_page_config(
    page_title="Sistema PMO | Cateno",
    page_icon="📋",
    layout="wide",
)

init_db()

# ── Estilos ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background:#0E1117; }
  .block-container { padding-top:1rem; }
  .titulo-sistema {
    font-size:1.6rem; font-weight:700; color:#FFFFFF;
    border-left:5px solid #009A44; padding-left:12px; margin-bottom:4px;
  }
  .subtitulo { font-size:0.9rem; color:#AAAAAA; padding-left:17px; }
  .card-projeto {
    background:#1C2333; border-radius:10px;
    padding:16px 20px; margin-bottom:12px;
    border-left:5px solid #555;
  }
  .card-verde   { border-left-color:#009A44; }
  .card-amarelo { border-left-color:#FFC200; }
  .card-vermelho{ border-left-color:#C0392B; }
  .card-azul    { border-left-color:#0056A2; }
  .badge {
    display:inline-block; padding:3px 10px; border-radius:12px;
    font-size:0.78rem; font-weight:600; margin-right:6px;
  }
  .kpi { background:#1C2333; border-radius:8px; padding:14px; text-align:center; }
  .kpi-val { font-size:1.8rem; font-weight:700; }
  .kpi-lbl { font-size:0.78rem; color:#AAAAAA; }
  .divider { border-top:1px solid #333; margin:16px 0; }
  .logo-cateno {
    background: linear-gradient(135deg, #002B5C 0%, #0056A2 100%);
    border-radius:10px; padding:10px 20px;
    display:flex; align-items:center; gap:12px; margin-bottom:16px;
  }
  .logo-texto {
    font-size:1.6rem; font-weight:800; color:#FFFFFF; letter-spacing:2px;
  }
  .logo-sub {
    font-size:0.75rem; color:#AAD4FF; letter-spacing:1px;
  }
</style>
""", unsafe_allow_html=True)

STATUS_OPTS    = ["🔵 Não Iniciado","🟢 No Prazo","🟡 Atenção","🔴 Crítico","⚫ Encerrado"]
PRIORIDADE_OPTS = ["Alta","Média","Baixa"]
FASE_OPTS      = ["Iniciação","Planejamento","Execução","Monitoramento","Encerramento"]
CATEGORIA_OPTS = ["Estratégicos","Regulatórios","Operacionais","Melhorias"]

CARD_CLASS = {
    "🟢 No Prazo":    "card-verde",
    "🟡 Atenção":     "card-amarelo",
    "🔴 Crítico":     "card-vermelho",
    "🔵 Não Iniciado":"card-azul",
    "⚫ Encerrado":   "",
}

# ════════════════════════════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════════════════════════════
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_center = st.columns([1,1.2,1])[1]
    with col_center:
        st.markdown("""
        <div style='text-align:center; padding:40px 30px; background:#1C2333;
                    border-radius:16px; border:1px solid #333;'>
          <div style='background:linear-gradient(135deg,#002B5C,#0056A2);
                      border-radius:8px; padding:12px 24px; display:inline-block; margin-bottom:16px;'>
            <span style='font-size:1.8rem; font-weight:800; color:#FFF; letter-spacing:3px;'>CATENO</span>
          </div>
          <div style='font-size:1.3rem; font-weight:700; color:#FFF; margin:8px 0'>Sistema PMO</div>
          <div style='color:#AAA; font-size:0.9rem'>Controle de Projetos e Documentações</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        email = st.text_input("E-mail", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        if st.button("Entrar", use_container_width=True, type="primary"):
            user = autenticar(email, senha)
            if user:
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos.")
        st.markdown("""
        <div style='text-align:center; color:#666; font-size:0.78rem; margin-top:16px'>
        Acesso restrito à equipe PMO
        </div>""", unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#002B5C,#0056A2);
                border-radius:10px; padding:12px 16px; margin-bottom:16px; text-align:center;'>
      <span style='font-size:1.4rem; font-weight:800; color:#FFF; letter-spacing:3px;'>CATENO</span><br>
      <span style='font-size:0.7rem; color:#AAD4FF; letter-spacing:1px;'>SISTEMA PMO</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:#1C2333; border-radius:10px; padding:14px; margin-bottom:16px;'>
      <div style='font-size:0.78rem; color:#AAA'>Logado como</div>
      <div style='font-weight:700; color:#FFF'>{st.session_state.usuario['nome']}</div>
      <div style='font-size:0.78rem; color:#009A44'>{st.session_state.usuario['email']}</div>
    </div>
    """, unsafe_allow_html=True)

    pagina = st.radio("Menu", ["🏠 Painel", "📋 Projetos", "➕ Novo Projeto", "🔑 Trocar Senha"],
                      label_visibility="collapsed")

    st.markdown("<hr style='border-color:#333'>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.session_state.pop("editar_id", None)
        st.rerun()

# ════════════════════════════════════════════════════════════════════
# PAINEL
# ════════════════════════════════════════════════════════════════════
if pagina == "🏠 Painel":
    st.markdown('<div class="titulo-sistema">Painel Executivo</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Visão consolidada do portfólio de projetos</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    projetos = listar_projetos()
    total    = len(projetos)

    if total == 0:
        st.info("Nenhum projeto cadastrado ainda. Acesse **Novo Projeto** para começar.")
    else:
        no_prazo  = sum(1 for p in projetos if p["status"] == "🟢 No Prazo")
        atencao   = sum(1 for p in projetos if p["status"] == "🟡 Atenção")
        critico   = sum(1 for p in projetos if p["status"] == "🔴 Crítico")
        nao_inic  = sum(1 for p in projetos if p["status"] == "🔵 Não Iniciado")
        orc_tot   = sum(p["orcamento_aprovado"] or 0 for p in projetos)
        cons_tot  = sum(p["orcamento_consumido"] or 0 for p in projetos)
        fc_tot    = sum(p["forecast_custo"] or 0 for p in projetos)

        k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
        def kpi(col, label, val, color="#FFFFFF"):
            col.markdown(f"""
            <div class='kpi'>
              <div class='kpi-val' style='color:{color}'>{val}</div>
              <div class='kpi-lbl'>{label}</div>
            </div>""", unsafe_allow_html=True)

        kpi(k1, "Total",        total)
        kpi(k2, "🟢 No Prazo",  no_prazo,  "#009A44")
        kpi(k3, "🟡 Atenção",   atencao,   "#FFC200")
        kpi(k4, "🔴 Crítico",   critico,   "#C0392B")
        kpi(k5, "🔵 Não Inic.", nao_inic,  "#0056A2")
        kpi(k6, "Consumido",    f"R${cons_tot/1e6:.1f}M", "#7EB8F7")
        kpi(k7, "Forecast",
            f"R${fc_tot/1e6:.1f}M",
            "#C0392B" if fc_tot > orc_tot else "#009A44")

        st.markdown("<br>", unsafe_allow_html=True)

        # Críticos em destaque
        criticos = [p for p in projetos if p["status"] == "🔴 Crítico"]
        if criticos:
            st.markdown("#### 🚨 Projetos Críticos")
            for p in criticos:
                st.error(f"**{p['codigo']} — {p['nome']}** | PMO: {p['pmo_responsavel']} "
                         f"| Forecast: {p['forecast_prazo'] or '—'} "
                         f"| Replanej.: {p['qtd_replanejamentos']}")

        st.markdown("#### Todos os Projetos")
        for p in projetos:
            css = CARD_CLASS.get(p["status"], "")
            pct = (p["orcamento_consumido"] or 0) / (p["orcamento_aprovado"] or 1) * 100
            st.markdown(f"""
            <div class='card-projeto {css}'>
              <b>{p['codigo']} — {p['nome']}</b>
              &nbsp;&nbsp;<span style='color:#AAA;font-size:0.85rem'>{p['area_demandante'] or '—'}</span>
              <br>
              <span style='color:#CCC;font-size:0.85rem'>
                PMO: <b>{p['pmo_responsavel'] or '—'}</b> &nbsp;|&nbsp;
                {p['status']} &nbsp;|&nbsp;
                Fase: {p['fase'] or '—'} &nbsp;|&nbsp;
                Categoria: <b>{p.get('categoria') or '—'}</b> &nbsp;|&nbsp;
                Orç. Consumido: <b>{pct:.0f}%</b> &nbsp;|&nbsp;
                Forecast: {p['forecast_prazo'] or '—'}
              </span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# LISTA DE PROJETOS
# ════════════════════════════════════════════════════════════════════
elif pagina == "📋 Projetos":
    st.markdown('<div class="titulo-sistema">Projetos</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Gerencie, edite e exclua projetos</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Filtros
    c1, c2, c3 = st.columns(3)
    with c1:
        f_status = st.selectbox("Status", ["Todos"] + STATUS_OPTS)
    with c2:
        f_area = st.selectbox("Área", ["Todos"] + areas_distintas())
    with c3:
        f_pmo = st.selectbox("PMO", ["Todos"] + pmos_distintos())

    projetos = listar_projetos(
        filtro_status=f_status if f_status != "Todos" else None,
        filtro_area=f_area if f_area != "Todos" else None,
        filtro_pmo=f_pmo if f_pmo != "Todos" else None,
    )

    if not projetos:
        st.info("Nenhum projeto encontrado com os filtros selecionados.")
    else:
        st.markdown(f"**{len(projetos)} projeto(s) encontrado(s)**")
        for p in projetos:
            css = CARD_CLASS.get(p["status"], "")
            with st.container():
                st.markdown(f"""
                <div class='card-projeto {css}'>
                  <b>{p['codigo']} — {p['nome']}</b>
                  <span style='color:#AAA; font-size:0.85rem; margin-left:10px'>
                    {p['area_demandante'] or '—'}
                  </span><br>
                  <span style='color:#CCC; font-size:0.85rem'>
                    {p['status']} &nbsp;|&nbsp; PMO: {p['pmo_responsavel'] or '—'} &nbsp;|&nbsp;
                    Fase: {p['fase'] or '—'} &nbsp;|&nbsp;
                    Categoria: <b>{p.get('categoria') or '—'}</b> &nbsp;|&nbsp;
                    Prazo: {p['fim_previsto'] or '—'} → {p['forecast_prazo'] or '—'} &nbsp;|&nbsp;
                    Replanej.: {p['qtd_replanejamentos']}
                  </span>
                </div>
                """, unsafe_allow_html=True)

                col_e, col_x, _ = st.columns([1, 1, 8])
                with col_e:
                    if st.button("✏️ Editar", key=f"ed_{p['id']}"):
                        st.session_state["editar_id"] = p["id"]
                        st.rerun()
                with col_x:
                    if st.button("🗑️ Excluir", key=f"ex_{p['id']}"):
                        st.session_state[f"confirmar_{p['id']}"] = True
                        st.rerun()

                if st.session_state.get(f"confirmar_{p['id']}"):
                    st.warning(f"Confirma exclusão de **{p['nome']}**?")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Sim, excluir", key=f"sim_{p['id']}", type="primary"):
                            excluir_projeto(p["id"])
                            st.session_state.pop(f"confirmar_{p['id']}", None)
                            st.success("Projeto excluído.")
                            st.rerun()
                    with cc2:
                        if st.button("❌ Cancelar", key=f"nao_{p['id']}"):
                            st.session_state.pop(f"confirmar_{p['id']}", None)
                            st.rerun()

# ════════════════════════════════════════════════════════════════════
# FORMULÁRIO NOVO / EDITAR
# ════════════════════════════════════════════════════════════════════
elif pagina == "➕ Novo Projeto" or st.session_state.get("editar_id"):
    editar_id = st.session_state.get("editar_id")
    p = buscar_projeto(editar_id) if editar_id else {}

    titulo = f"Editar Projeto — {p.get('codigo','')}" if editar_id else "Novo Projeto"
    st.markdown(f'<div class="titulo-sistema">{titulo}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("form_projeto", clear_on_submit=False):
        st.markdown("#### Identificação")
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do Projeto *", value=p.get("nome",""))
        with c2:
            area = st.text_input("Área Demandante *", value=p.get("area_demandante",""))

        c3, c4 = st.columns(2)
        with c3:
            pmo  = st.text_input("PMO Responsável *", value=p.get("pmo_responsavel",""))
        with c4:
            envolvidos = st.text_input("Envolvidos", value=p.get("envolvidos",""))

        descricao = st.text_area("Descrição do Projeto", value=p.get("descricao",""), height=100)

        st.markdown("#### Status e Classificação")
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            status = st.selectbox("Status *", STATUS_OPTS,
                                  index=STATUS_OPTS.index(p["status"]) if p.get("status") in STATUS_OPTS else 0)
        with c6:
            prioridade = st.selectbox("Prioridade", PRIORIDADE_OPTS,
                                      index=PRIORIDADE_OPTS.index(p["prioridade"]) if p.get("prioridade") in PRIORIDADE_OPTS else 1)
        with c7:
            fase = st.selectbox("Fase Atual", FASE_OPTS,
                                index=FASE_OPTS.index(p["fase"]) if p.get("fase") in FASE_OPTS else 0)
        with c8:
            _cat_default = p.get("categoria","Operacionais") or "Operacionais"
            categoria = st.selectbox("Categoria", CATEGORIA_OPTS,
                                     index=CATEGORIA_OPTS.index(_cat_default) if _cat_default in CATEGORIA_OPTS else 2)

        st.markdown("#### Cronograma")
        d1, d2, d3 = st.columns(3)
        with d1:
            inicio  = st.text_input("Início Previsto (dd/mm/aaaa)", value=p.get("inicio_previsto",""))
        with d2:
            fim     = st.text_input("Fim Previsto (dd/mm/aaaa)", value=p.get("fim_previsto",""))
        with d3:
            fc_prazo = st.text_input("Forecast de Conclusão (dd/mm/aaaa)", value=p.get("forecast_prazo",""))

        st.markdown("#### Orçamento")
        o1, o2, o3 = st.columns(3)
        with o1:
            orc_ap  = st.number_input("Orçamento Aprovado (R$)", min_value=0.0,
                                      value=float(p.get("orcamento_aprovado") or 0), step=1000.0)
        with o2:
            orc_cons = st.number_input("Consumido (R$)", min_value=0.0,
                                       value=float(p.get("orcamento_consumido") or 0), step=1000.0)
        with o3:
            fc_custo = st.number_input("Forecast Custo (R$)", min_value=0.0,
                                       value=float(p.get("forecast_custo") or 0), step=1000.0)

        st.markdown("#### Replanejamentos")
        r1, r2 = st.columns([1, 3])
        with r1:
            qtd_rep = st.number_input("Qtd. Replanejamentos", min_value=0,
                                      value=int(p.get("qtd_replanejamentos") or 0))
        with r2:
            motivo  = st.text_input("Motivo do Último Replanejamento", value=p.get("motivo_replanejamento",""))

        observacoes = st.text_area("Observações", value=p.get("observacoes",""), height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        c_salvar, c_cancelar = st.columns([1,1])
        with c_salvar:
            salvar = st.form_submit_button("💾 Salvar Projeto", type="primary", use_container_width=True)
        with c_cancelar:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            if not nome or not area or not pmo:
                st.error("Preencha os campos obrigatórios: Nome, Área Demandante e PMO Responsável.")
            else:
                dados = {
                    "id": editar_id,
                    "nome": nome, "categoria": categoria,
                    "area_demandante": area,
                    "pmo_responsavel": pmo, "envolvidos": envolvidos,
                    "descricao": descricao, "status": status,
                    "prioridade": prioridade, "fase": fase,
                    "inicio_previsto": inicio, "fim_previsto": fim,
                    "forecast_prazo": fc_prazo,
                    "orcamento_aprovado": orc_ap,
                    "orcamento_consumido": orc_cons,
                    "forecast_custo": fc_custo,
                    "qtd_replanejamentos": qtd_rep,
                    "motivo_replanejamento": motivo,
                    "observacoes": observacoes,
                }
                novo_id = salvar_projeto(dados, st.session_state.usuario["nome"])
                if not editar_id and novo_id:
                    st.session_state["editar_id"] = novo_id
                else:
                    st.session_state.pop("editar_id", None)
                st.success("✅ Projeto salvo com sucesso!")
                st.rerun()

        if cancelar:
            st.session_state.pop("editar_id", None)
            st.rerun()

    # ── Seção de Documentos (somente ao editar projeto existente) ─────
    if editar_id:
        st.markdown("<hr style='border-color:#333; margin:24px 0'>", unsafe_allow_html=True)
        st.markdown("#### 📎 Documentos do Projeto")

        docs = listar_documentos(editar_id)

        if docs:
            for doc in docs:
                col_nome, col_env, col_dl, col_del = st.columns([4, 3, 1, 1])
                with col_nome:
                    st.markdown(f"📄 **{doc['nome_arquivo']}**")
                with col_env:
                    st.markdown(f"<span style='color:#AAA;font-size:0.82rem'>"
                                f"Enviado por {doc['enviado_por']} em {doc['enviado_em'][:10]}"
                                f"</span>", unsafe_allow_html=True)
                with col_dl:
                    raw = baixar_documento(doc["id"])
                    if raw:
                        st.download_button(
                            "⬇️",
                            data=raw["conteudo"],
                            file_name=raw["nome_arquivo"],
                            mime=raw["tipo_arquivo"] or "application/octet-stream",
                            key=f"dl_{doc['id']}",
                        )
                with col_del:
                    if st.button("🗑️", key=f"deldoc_{doc['id']}"):
                        excluir_documento(doc["id"])
                        st.rerun()
        else:
            st.markdown("<span style='color:#777;font-size:0.88rem'>Nenhum documento anexado ainda.</span>",
                        unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        arquivo = st.file_uploader(
            "Anexar novo documento",
            accept_multiple_files=False,
            key="uploader_doc",
        )
        if arquivo is not None:
            if st.button("📤 Enviar arquivo", type="primary"):
                salvar_documento(
                    projeto_id=editar_id,
                    nome_arquivo=arquivo.name,
                    tipo_arquivo=arquivo.type,
                    conteudo=arquivo.read(),
                    enviado_por=st.session_state.usuario["nome"],
                )
                st.success(f"✅ **{arquivo.name}** enviado com sucesso!")
                st.rerun()

# ════════════════════════════════════════════════════════════════════
# TROCAR SENHA
# ════════════════════════════════════════════════════════════════════
elif pagina == "🔑 Trocar Senha":
    st.markdown('<div class="titulo-sistema">Trocar Senha</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Altere sua senha de acesso ao sistema</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        with st.form("form_senha"):
            st.markdown(f"""
            <div style='background:#1C2333; border-radius:10px; padding:16px;
                        margin-bottom:16px; text-align:center;'>
              <div style='color:#AAA; font-size:0.85rem;'>Alterando senha para</div>
              <div style='color:#FFF; font-weight:700;'>{st.session_state.usuario['nome']}</div>
            </div>
            """, unsafe_allow_html=True)

            senha_atual  = st.text_input("Senha atual", type="password")
            nova_senha   = st.text_input("Nova senha", type="password",
                                         help="Mínimo 6 caracteres")
            conf_senha   = st.text_input("Confirmar nova senha", type="password")

            salvar_senha = st.form_submit_button("🔑 Alterar Senha",
                                                  type="primary",
                                                  use_container_width=True)
            if salvar_senha:
                if not senha_atual or not nova_senha or not conf_senha:
                    st.error("Preencha todos os campos.")
                elif nova_senha != conf_senha:
                    st.error("A nova senha e a confirmação não coincidem.")
                else:
                    ok, msg = trocar_senha(
                        st.session_state.usuario["id"], senha_atual, nova_senha
                    )
                    if ok:
                        st.success(f"✅ {msg} Faça login novamente.")
                        st.session_state.usuario = None
                        st.rerun()
                    else:
                        st.error(msg)
