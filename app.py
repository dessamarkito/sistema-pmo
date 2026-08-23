import streamlit as st
import base64, os
from database import (init_db, autenticar, listar_projetos, buscar_projeto,
                      salvar_projeto, excluir_projeto, areas_distintas,
                      pmos_distintos, trocar_senha,
                      salvar_documento, listar_documentos,
                      baixar_documento, excluir_documento,
                      listar_tarefas, salvar_tarefa, buscar_tarefa,
                      excluir_tarefa, metricas_tarefas,
                      listar_historico_status)

def _logo_b64():
    _path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cateno.png")
    with open(_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

LOGO_SRC = _logo_b64()

st.set_page_config(
    page_title="Sistema PMO | Cateno",
    page_icon="📋",
    layout="wide",
)

init_db()

# ── Estilos ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fundo geral */
  .stApp, .main, [data-testid="stAppViewContainer"] {
    background: #F0F2F6 !important;
  }
  [data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
  }
  .block-container { padding-top:1.5rem; }

  /* Títulos */
  .titulo-sistema {
    font-size:1.5rem; font-weight:700; color:#111827;
    border-left:4px solid #0056A2; padding-left:12px; margin-bottom:2px;
  }
  .subtitulo { font-size:0.88rem; color:#6B7280; padding-left:16px; }

  /* Cards de projeto */
  .card-projeto {
    background:#FFFFFF;
    border-radius:10px;
    padding:16px 20px;
    margin-bottom:10px;
    border-left:4px solid #D1D5DB;
    box-shadow:0 1px 4px rgba(0,0,0,0.07);
  }
  .card-verde    { border-left-color:#009A44; }
  .card-amarelo  { border-left-color:#F59E0B; }
  .card-vermelho { border-left-color:#DC2626; }
  .card-azul     { border-left-color:#0056A2; }

  /* KPI */
  .kpi {
    background:#FFFFFF; border-radius:10px;
    padding:16px 12px; text-align:center;
    box-shadow:0 1px 4px rgba(0,0,0,0.07);
  }
  .kpi-val { font-size:1.9rem; font-weight:700; color:#111827; }
  .kpi-lbl { font-size:0.75rem; color:#6B7280; margin-top:2px; }

  /* Divider */
  .divider { border-top:1px solid #E5E7EB; margin:16px 0; }

  /* Texto geral dos cards */
  .card-projeto b { color:#111827; }
  .card-projeto span { color:#374151; }
</style>
""", unsafe_allow_html=True)

STATUS_OPTS    = ["🔵 Não Iniciado","🟢 No Prazo","🟡 Atenção","🔴 Crítico","⚫ Encerrado"]
PRIORIDADE_OPTS = ["Alta","Média","Baixa"]
CATEGORIA_OPTS = ["Estratégicos","Regulatórios","Operacionais","Melhorias"]
ETAPA_OPTS     = ["Ideação","Prototipação","Aprovação do Business Case"]
TAREFA_STATUS  = ["Pendente","Em Andamento","Concluída","Cancelada"]
TAREFA_CORES   = {"Pendente":"#6B7280","Em Andamento":"#0056A2",
                  "Concluída":"#009A44","Cancelada":"#9CA3AF"}
TAREFA_PRIOR_CORES = {"Alta":"#DC2626","Média":"#D97706","Baixa":"#6B7280"}

STATUS_CORES = {
    "🟢 No Prazo":    "#009A44",
    "🟡 Atenção":     "#D97706",
    "🔴 Crítico":     "#DC2626",
    "🔵 Não Iniciado":"#0056A2",
    "⚫ Encerrado":   "#6B7280",
}

def _render_historico(historico):
    for i, h in enumerate(historico):
        cor = STATUS_CORES.get(h["status_novo"], "#6B7280")
        is_last = (i == len(historico) - 1)
        ant = h["status_anterior"] or "—"
        data = h["alterado_em"][:16].replace("T", " ") if h["alterado_em"] else "—"
        obs  = f"<br><span style='color:#6B7280;font-size:0.78rem;font-style:italic'>\"{h['observacao']}\"</span>" if h.get("observacao") else ""
        st.markdown(f"""
        <div style='display:flex; gap:14px; margin-bottom:4px;'>
          <div style='display:flex; flex-direction:column; align-items:center;'>
            <div style='width:12px;height:12px;border-radius:50%;background:{cor};
                        border:2px solid {cor};margin-top:3px;flex-shrink:0;'></div>
            {'<div style="width:2px;flex:1;background:#E5E7EB;margin:3px auto 0;"></div>' if not is_last else ''}
          </div>
          <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;
                      padding:10px 14px;margin-bottom:8px;flex:1;'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:4px;'>
              <div>
                <span style='font-size:0.78rem;color:#9CA3AF'>{ant}</span>
                <span style='color:#9CA3AF;margin:0 6px'>→</span>
                <span style='background:{cor}22;color:{cor};font-size:0.8rem;font-weight:700;
                             padding:2px 10px;border-radius:99px;'>{h['status_novo']}</span>
              </div>
              <span style='font-size:0.75rem;color:#9CA3AF'>{data} · {h.get('alterado_por','—')}</span>
            </div>
            {obs}
          </div>
        </div>
        """, unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style='text-align:center; padding:40px 30px; background:#FFFFFF;
                    border-radius:16px; box-shadow:0 4px 20px rgba(0,0,0,0.10);'>
          <div style='background:#111827; border-radius:10px; padding:16px 28px;
                      display:inline-block; margin-bottom:16px;'>
            <img src='{LOGO_SRC}' style='height:52px; display:block;'>
          </div>
          <div style='font-size:1.3rem; font-weight:700; color:#111827; margin:8px 0'>Sistema PMO</div>
          <div style='color:#6B7280; font-size:0.9rem'>Controle de Projetos e Documentações</div>
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
        <div style='text-align:center; color:#9CA3AF; font-size:0.78rem; margin-top:16px'>
        Acesso restrito à equipe PMO
        </div>""", unsafe_allow_html=True)
    st.stop()

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style='background:#111827; border-radius:10px; padding:12px 16px;
                margin-bottom:4px; text-align:center;'>
      <img src='{LOGO_SRC}' style='height:44px; display:inline-block;'>
    </div>
    <div style='text-align:center; font-size:0.7rem; color:#6B7280;
                letter-spacing:1px; margin-bottom:14px;'>SISTEMA PMO</div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:12px 14px; margin-bottom:16px;'>
      <div style='font-size:0.75rem; color:#9CA3AF'>Logado como</div>
      <div style='font-weight:700; color:#111827'>{st.session_state.usuario['nome']}</div>
      <div style='font-size:0.75rem; color:#0056A2'>{st.session_state.usuario['email']}</div>
    </div>
    """, unsafe_allow_html=True)

    pagina = st.radio("Menu", ["🏠 Painel", "📋 Projetos", "➕ Novo Projeto", "🔑 Trocar Senha"],
                      label_visibility="collapsed")

    st.markdown("<hr style='border-color:#E5E7EB'>", unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.session_state.pop("editar_id", None)
        st.session_state.pop("consultar_id", None)
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

        kpi(k1, "Total",        total,     "#111827")
        kpi(k2, "🟢 No Prazo",  no_prazo,  "#009A44")
        kpi(k3, "🟡 Atenção",   atencao,   "#D97706")
        kpi(k4, "🔴 Crítico",   critico,   "#DC2626")
        kpi(k5, "🔵 Não Inic.", nao_inic,  "#0056A2")
        kpi(k6, "Consumido",    f"R${cons_tot/1e6:.1f}M", "#374151")
        kpi(k7, "Forecast",
            f"R${fc_tot/1e6:.1f}M",
            "#DC2626" if fc_tot > orc_tot else "#009A44")

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
            col_card, col_btn = st.columns([9, 1])
            with col_card:
                st.markdown(f"""
                <div class='card-projeto {css}'>
                  <b style='color:#111827;font-size:1rem'>{p['codigo']} — {p['nome']}</b>
                  &nbsp;&nbsp;<span style='color:#6B7280;font-size:0.85rem'>{p['area_demandante'] or '—'}</span>
                  <br>
                  <span style='color:#374151;font-size:0.84rem'>
                    PMO: <b>{p['pmo_responsavel'] or '—'}</b> &nbsp;|&nbsp;
                    {p['status']} &nbsp;|&nbsp;
                    Etapa: {p.get('etapa') or '—'} &nbsp;|&nbsp;
                    Categoria: <b>{p.get('categoria') or '—'}</b> &nbsp;|&nbsp;
                    Orç. Previsto: <b>R$ {(p.get('orcamento_previsto') or 0):,.0f}</b>
                  </span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.markdown("<div style='padding-top:6px'>", unsafe_allow_html=True)
                if st.button("👁️", key=f"vp_{p['id']}", help="Consultar projeto"):
                    st.session_state["consultar_id"] = p["id"]
                    st.session_state.pop("editar_id", None)
                    st.rerun()
                if st.button("✏️", key=f"ep_{p['id']}", help="Editar projeto"):
                    st.session_state["editar_id"] = p["id"]
                    st.session_state.pop("consultar_id", None)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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
                  <b style='color:#111827;font-size:1rem'>{p['codigo']} — {p['nome']}</b>
                  <span style='color:#6B7280; font-size:0.85rem; margin-left:10px'>
                    {p['area_demandante'] or '—'}
                  </span><br>
                  <span style='color:#374151; font-size:0.84rem'>
                    {p['status']} &nbsp;|&nbsp; PMO: <b>{p['pmo_responsavel'] or '—'}</b> &nbsp;|&nbsp;
                    Etapa: {p.get('etapa') or '—'} &nbsp;|&nbsp;
                    Categoria: <b>{p.get('categoria') or '—'}</b> &nbsp;|&nbsp;
                    Orç. Previsto: <b>R$ {(p.get('orcamento_previsto') or 0):,.0f}</b>
                  </span>
                </div>
                """, unsafe_allow_html=True)

                col_c, col_e, col_x, _ = st.columns([1.2, 1.2, 1.2, 6])
                with col_c:
                    if st.button("👁️ Consultar", key=f"vl_{p['id']}"):
                        st.session_state["consultar_id"] = p["id"]
                        st.session_state.pop("editar_id", None)
                        st.rerun()
                with col_e:
                    if st.button("✏️ Editar", key=f"ed_{p['id']}"):
                        st.session_state["editar_id"] = p["id"]
                        st.session_state.pop("consultar_id", None)
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
# CONSULTAR PROJETO (somente leitura)
# ════════════════════════════════════════════════════════════════════
elif st.session_state.get("consultar_id"):
    pid = st.session_state["consultar_id"]
    p   = buscar_projeto(pid)

    if not p:
        st.error("Projeto não encontrado.")
        st.session_state.pop("consultar_id", None)
        st.rerun()

    css   = CARD_CLASS.get(p["status"], "")
    cor_s = {"🟢 No Prazo":"#009A44","🟡 Atenção":"#D97706",
              "🔴 Crítico":"#DC2626","🔵 Não Iniciado":"#0056A2",
              "⚫ Encerrado":"#6B7280"}.get(p["status"], "#6B7280")

    # Cabeçalho
    cb1, cb2 = st.columns([8, 2])
    with cb1:
        st.markdown(f'<div class="titulo-sistema">{p["codigo"]} — {p["nome"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="subtitulo">{p["area_demandante"] or ""} · {p["categoria"] or ""}</div>',
                    unsafe_allow_html=True)
    with cb2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✏️ Editar este projeto", use_container_width=True, type="primary"):
            st.session_state["editar_id"] = pid
            st.session_state.pop("consultar_id", None)
            st.rerun()
        if st.button("← Voltar", use_container_width=True):
            st.session_state.pop("consultar_id", None)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Status / badges
    _etapa_c = p.get("etapa") or "—"
    st.markdown(f"""
    <div style='display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px;'>
      <span style='background:{cor_s}22; color:{cor_s}; padding:5px 14px;
                   border-radius:99px; font-weight:700; font-size:0.88rem;'>{p['status']}</span>
      <span style='background:#E5E7EB; color:#374151; padding:5px 14px;
                   border-radius:99px; font-size:0.88rem;'>Etapa: {_etapa_c}</span>
      <span style='background:#E5E7EB; color:#374151; padding:5px 14px;
                   border-radius:99px; font-size:0.88rem;'>Prioridade: {p['prioridade'] or '—'}</span>
      <span style='background:#E5E7EB; color:#374151; padding:5px 14px;
                   border-radius:99px; font-size:0.88rem;'>Categoria: {p.get('categoria') or '—'}</span>
    </div>
    """, unsafe_allow_html=True)

    # Detalhes em duas colunas
    d1, d2 = st.columns(2)
    def campo(label, valor):
        return f"<div style='margin-bottom:10px;'><span style='font-size:0.75rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.5px'>{label}</span><br><span style='font-size:0.95rem;color:#111827;font-weight:600'>{valor or '—'}</span></div>"

    with d1:
        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:20px;'>
          <div style='font-size:0.8rem;font-weight:700;color:#6B7280;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.5px'>Equipe</div>
          {campo("PMO Responsável", p['pmo_responsavel'])}
          {campo("Gerente Executivo", p.get('gerente_executivo'))}
          {campo("Área Demandante", p['area_demandante'])}
          {campo("Envolvidos", p['envolvidos'])}
        </div>
        """, unsafe_allow_html=True)

    with d2:
        orc_prev = p.get("orcamento_previsto") or 0
        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:20px;'>
          <div style='font-size:0.8rem;font-weight:700;color:#6B7280;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.5px'>Orçamento e Estratégia</div>
          {campo("Orçamento Previsto", f"R$ {orc_prev:,.2f}".replace(",","X").replace(".",",").replace("X","."))}
          {campo("Direcionador Estratégico", p.get('direcionador_estrategico'))}
          {campo("Etapa Atual", p.get('etapa'))}
        </div>
        """, unsafe_allow_html=True)

    if p.get("descricao"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:20px;'>
          <div style='font-size:0.8rem;font-weight:700;color:#6B7280;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px'>Descrição</div>
          <p style='color:#374151;margin:0'>{p['descricao']}</p>
        </div>""", unsafe_allow_html=True)

    if p.get("observacoes"):
        st.markdown(f"""
        <div style='background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:16px 20px;margin-top:10px;'>
          <div style='font-size:0.8rem;font-weight:700;color:#D97706;margin-bottom:6px;'>Observações</div>
          <p style='color:#374151;margin:0'>{p['observacoes']}</p>
        </div>""", unsafe_allow_html=True)

    # Tarefas (leitura)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#E5E7EB'>", unsafe_allow_html=True)
    st.markdown("#### ✅ Tarefas")
    met = metricas_tarefas(pid)
    if met["total"] > 0:
        pct_t = met["pct"]
        cor_t = "#009A44" if pct_t == 100 else ("#0056A2" if pct_t >= 50 else "#D97706")
        st.markdown(f"""
        <div style='background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:14px 20px;margin-bottom:14px;'>
          <div style='display:flex;justify-content:space-between;margin-bottom:6px;'>
            <span style='font-size:0.85rem;color:#374151'><b>{met['concluidas']}</b> de <b>{met['total']}</b> concluídas</span>
            <span style='font-weight:700;color:{cor_t}'>{pct_t}%</span>
          </div>
          <div style='background:#E5E7EB;border-radius:99px;height:8px;'>
            <div style='background:{cor_t};width:{pct_t}%;height:8px;border-radius:99px;'></div>
          </div>
        </div>""", unsafe_allow_html=True)
        for t in listar_tarefas(pid):
            cor_s2 = TAREFA_CORES.get(t["status"], "#6B7280")
            cor_p2 = TAREFA_PRIOR_CORES.get(t["prioridade"], "#6B7280")
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;
                        padding:10px 16px;margin-bottom:6px;border-left:3px solid {cor_p2};'>
              <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;'>
                <span style='font-weight:600;color:#111827'>{t['titulo']}</span>
                <span style='background:{cor_s2}22;color:{cor_s2};font-size:0.72rem;font-weight:600;padding:2px 8px;border-radius:99px;'>{t['status']}</span>
                <span style='background:{cor_p2}22;color:{cor_p2};font-size:0.72rem;font-weight:600;padding:2px 8px;border-radius:99px;'>{t['prioridade']}</span>
              </div>
              <div style='font-size:0.78rem;color:#6B7280;margin-top:4px;'>
                {'👤 ' + t['responsavel'] if t['responsavel'] else ''}&nbsp;&nbsp;
                {'📅 ' + t['data_prevista'] if t['data_prevista'] else ''}
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#9CA3AF;font-size:0.88rem'>Nenhuma tarefa cadastrada.</span>",
                    unsafe_allow_html=True)

    # Documentos (leitura + download)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#E5E7EB'>", unsafe_allow_html=True)
    st.markdown("#### 📎 Documentos")
    docs = listar_documentos(pid)
    if docs:
        for doc in docs:
            dc1, dc2 = st.columns([6, 1])
            with dc1:
                st.markdown(f"📄 **{doc['nome_arquivo']}** <span style='color:#9CA3AF;font-size:0.8rem'>&nbsp;·&nbsp; {doc['enviado_por']} · {doc['enviado_em'][:10]}</span>",
                            unsafe_allow_html=True)
            with dc2:
                raw = baixar_documento(doc["id"])
                if raw:
                    st.download_button("⬇️", data=raw["conteudo"],
                                       file_name=raw["nome_arquivo"],
                                       mime=raw["tipo_arquivo"] or "application/octet-stream",
                                       key=f"dlc_{doc['id']}")
    else:
        st.markdown("<span style='color:#9CA3AF;font-size:0.88rem'>Nenhum documento anexado.</span>",
                    unsafe_allow_html=True)

    # Histórico de status na tela de Consulta
    historico = listar_historico_status(pid)
    if historico:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#E5E7EB'>", unsafe_allow_html=True)
        st.markdown("#### 🕐 Histórico de Status")
        _render_historico(historico)

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
        f1, f2 = st.columns(2)
        with f1:
            nome = st.text_input("Nome do Projeto *", value=p.get("nome",""))
        with f2:
            area = st.text_input("Área Demandante *", value=p.get("area_demandante",""))

        f3, f4 = st.columns(2)
        with f3:
            pmo = st.text_input("PMO Responsável *", value=p.get("pmo_responsavel",""))
        with f4:
            gerente = st.text_input("Gerente Executivo Responsável", value=p.get("gerente_executivo",""))

        envolvidos = st.text_input("Envolvidos", value=p.get("envolvidos",""),
                                   placeholder="Nomes separados por vírgula")
        descricao  = st.text_area("Descrição do Projeto", value=p.get("descricao",""), height=100)

        st.markdown("#### Classificação")
        g1, g2, g3 = st.columns(3)
        with g1:
            _prior = p.get("prioridade","Média") or "Média"
            prioridade = st.selectbox("Prioridade", PRIORIDADE_OPTS,
                                      index=PRIORIDADE_OPTS.index(_prior) if _prior in PRIORIDADE_OPTS else 1)
        with g2:
            _cat = p.get("categoria","Operacionais") or "Operacionais"
            categoria = st.selectbox("Categoria", CATEGORIA_OPTS,
                                     index=CATEGORIA_OPTS.index(_cat) if _cat in CATEGORIA_OPTS else 2)
        with g3:
            _etapa = p.get("etapa","Ideação") or "Ideação"
            etapa = st.selectbox("Etapa", ETAPA_OPTS,
                                 index=ETAPA_OPTS.index(_etapa) if _etapa in ETAPA_OPTS else 0)

        direcionador = st.text_input("Direcionador Estratégico",
                                     value=p.get("direcionador_estrategico",""),
                                     placeholder="Ex: Transformação Digital, Eficiência Operacional...")

        st.markdown("#### Orçamento")
        orc_prev = st.number_input("Orçamento Previsto (R$)", min_value=0.0,
                                   value=float(p.get("orcamento_previsto") or 0), step=1000.0,
                                   format="%.2f")

        if editar_id:
            st.markdown("#### Status Atual")
            h1, h2 = st.columns([1, 2])
            with h1:
                _st = p.get("status","🔵 Não Iniciado") or "🔵 Não Iniciado"
                status = st.selectbox("Status", STATUS_OPTS,
                                      index=STATUS_OPTS.index(_st) if _st in STATUS_OPTS else 0)
            with h2:
                obs_status = st.text_input("Motivo da mudança (opcional)",
                                           placeholder="Registrado no histórico ao mudar o status")
        else:
            status     = "🔵 Não Iniciado"
            obs_status = ""

        st.markdown("<br>", unsafe_allow_html=True)
        c_salvar, c_cancelar = st.columns([1, 1])
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
                    "area_demandante": area, "pmo_responsavel": pmo,
                    "gerente_executivo": gerente, "envolvidos": envolvidos,
                    "descricao": descricao, "status": status,
                    "prioridade": prioridade, "etapa": etapa,
                    "direcionador_estrategico": direcionador,
                    "orcamento_previsto": orc_prev,
                    "obs_status": obs_status,
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

    # ── Histórico de Status ───────────────────────────────────────────
    if editar_id:
        historico = listar_historico_status(editar_id)
        if historico:
            st.markdown("<hr style='border-color:#E5E7EB; margin:24px 0'>", unsafe_allow_html=True)
            st.markdown("#### 🕐 Histórico de Status")
            _render_historico(historico)

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
            st.markdown("<span style='color:#9CA3AF;font-size:0.88rem'>Nenhum documento anexado ainda.</span>",
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

    # ── Seção de Tarefas ──────────────────────────────────────────────
    if editar_id:
        st.markdown("<hr style='border-color:#E5E7EB; margin:28px 0'>", unsafe_allow_html=True)
        st.markdown("#### ✅ Tarefas Planejadas")

        met = metricas_tarefas(editar_id)
        tarefas = listar_tarefas(editar_id)

        # Mini painel de progresso
        if met["total"] > 0:
            pct = met["pct"]
            bar_color = "#009A44" if pct == 100 else ("#0056A2" if pct >= 50 else "#D97706")
            st.markdown(f"""
            <div style='background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px;
                        padding:14px 20px; margin-bottom:16px;'>
              <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                <span style='font-size:0.85rem; color:#374151'>
                  <b>{met['concluidas']}</b> de <b>{met['total']}</b> tarefas concluídas
                </span>
                <span style='font-size:0.85rem; font-weight:700; color:{bar_color}'>{pct}%</span>
              </div>
              <div style='background:#E5E7EB; border-radius:99px; height:8px;'>
                <div style='background:{bar_color}; width:{pct}%; height:8px; border-radius:99px;
                            transition:width 0.3s;'></div>
              </div>
              <div style='display:flex; gap:16px; margin-top:10px; font-size:0.78rem; color:#6B7280;'>
                <span>🔵 Em andamento: <b>{met['em_andamento']}</b></span>
                <span>⏳ Pendentes: <b>{met['pendentes']}</b></span>
                <span>✅ Concluídas: <b>{met['concluidas']}</b></span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Lista de tarefas
        if tarefas:
            for t in tarefas:
                cor_status = TAREFA_CORES.get(t["status"], "#6B7280")
                cor_prior  = TAREFA_PRIOR_CORES.get(t["prioridade"], "#6B7280")
                is_edit = st.session_state.get(f"edit_tarefa_{t['id']}", False)

                with st.container():
                    if is_edit:
                        # Formulário inline de edição
                        with st.form(f"form_edit_t_{t['id']}"):
                            st.markdown(f"**Editando:** {t['titulo']}")
                            ea, eb = st.columns(2)
                            with ea:
                                et = st.text_input("Título *", value=t["titulo"])
                                er = st.text_input("Responsável", value=t["responsavel"] or "")
                                ep = st.selectbox("Prioridade", PRIORIDADE_OPTS,
                                                  index=PRIORIDADE_OPTS.index(t["prioridade"]) if t["prioridade"] in PRIORIDADE_OPTS else 1)
                            with eb:
                                es = st.selectbox("Status", TAREFA_STATUS,
                                                  index=TAREFA_STATUS.index(t["status"]) if t["status"] in TAREFA_STATUS else 0)
                                edp = st.text_input("Data Prevista (dd/mm/aaaa)", value=t["data_prevista"] or "")
                                edc = st.text_input("Data Conclusão (dd/mm/aaaa)", value=t["data_conclusao"] or "")
                            ed = st.text_area("Descrição", value=t["descricao"] or "", height=60)
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                                    salvar_tarefa({
                                        "id": t["id"], "titulo": et, "descricao": ed,
                                        "responsavel": er, "status": es, "prioridade": ep,
                                        "data_prevista": edp, "data_conclusao": edc,
                                    }, st.session_state.usuario["nome"])
                                    st.session_state.pop(f"edit_tarefa_{t['id']}", None)
                                    st.rerun()
                            with ec2:
                                if st.form_submit_button("Cancelar", use_container_width=True):
                                    st.session_state.pop(f"edit_tarefa_{t['id']}", None)
                                    st.rerun()
                    else:
                        col_info, col_ac = st.columns([9, 1])
                        with col_info:
                            st.markdown(f"""
                            <div style='background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px;
                                        padding:10px 16px; margin-bottom:6px;
                                        border-left:3px solid {cor_prior};'>
                              <div style='display:flex; align-items:center; gap:10px; flex-wrap:wrap;'>
                                <span style='font-weight:600; color:#111827'>{t['titulo']}</span>
                                <span style='background:{cor_status}22; color:{cor_status};
                                             font-size:0.72rem; font-weight:600; padding:2px 8px;
                                             border-radius:99px;'>{t['status']}</span>
                                <span style='background:{cor_prior}22; color:{cor_prior};
                                             font-size:0.72rem; font-weight:600; padding:2px 8px;
                                             border-radius:99px;'>{t['prioridade']}</span>
                              </div>
                              <div style='font-size:0.78rem; color:#6B7280; margin-top:4px;'>
                                {'👤 ' + t['responsavel'] if t['responsavel'] else ''}&nbsp;&nbsp;
                                {'📅 ' + t['data_prevista'] if t['data_prevista'] else ''}
                                {' → ✅ ' + t['data_conclusao'] if t['data_conclusao'] else ''}
                              </div>
                              {f"<div style='font-size:0.78rem; color:#9CA3AF; margin-top:2px;'>{t['descricao']}</div>" if t['descricao'] else ''}
                            </div>
                            """, unsafe_allow_html=True)
                        with col_ac:
                            st.markdown("<div style='padding-top:4px'>", unsafe_allow_html=True)
                            if st.button("✏️", key=f"edtk_{t['id']}", help="Editar tarefa"):
                                st.session_state[f"edit_tarefa_{t['id']}"] = True
                                st.rerun()
                            if st.button("🗑️", key=f"deltk_{t['id']}", help="Excluir tarefa"):
                                excluir_tarefa(t["id"])
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#9CA3AF;font-size:0.88rem'>Nenhuma tarefa cadastrada ainda.</span>",
                        unsafe_allow_html=True)

        # Formulário de nova tarefa
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nova Tarefa", type="primary"):
            st.session_state["nova_tarefa_aberta"] = True

        if st.session_state.get("nova_tarefa_aberta"):
            with st.form("form_nova_tarefa", clear_on_submit=True):
                st.markdown("**Nova Tarefa**")
                na, nb = st.columns(2)
                with na:
                    nt = st.text_input("Título *")
                    nr = st.text_input("Responsável")
                    np = st.selectbox("Prioridade", PRIORIDADE_OPTS, index=1)
                with nb:
                    ns = st.selectbox("Status", TAREFA_STATUS)
                    nd = st.text_input("Data Prevista (dd/mm/aaaa)")
                    _ = st.text_input("Data Conclusão (dd/mm/aaaa)", value="",
                                      disabled=True, help="Preenchida ao concluir")
                ndesc = st.text_area("Descrição", height=60)
                nc1, nc2 = st.columns(2)
                with nc1:
                    if st.form_submit_button("✅ Adicionar Tarefa", type="primary", use_container_width=True):
                        if not nt:
                            st.error("Informe o título da tarefa.")
                        else:
                            salvar_tarefa({
                                "projeto_id": editar_id,
                                "titulo": nt, "descricao": ndesc,
                                "responsavel": nr, "status": ns,
                                "prioridade": np, "data_prevista": nd,
                            }, st.session_state.usuario["nome"])
                            st.session_state.pop("nova_tarefa_aberta", None)
                            st.rerun()
                with nc2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state.pop("nova_tarefa_aberta", None)
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
            <div style='background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:16px;
                        margin-bottom:16px; text-align:center;'>
              <div style='color:#6B7280; font-size:0.85rem;'>Alterando senha para</div>
              <div style='color:#111827; font-weight:700;'>{st.session_state.usuario['nome']}</div>
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
