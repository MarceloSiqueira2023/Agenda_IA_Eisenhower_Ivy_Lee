# pages/1_Matriz_Eisenhower.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import Storage

st.set_page_config(layout="wide")
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

if 'task_to_edit' not in st.session_state:
    st.session_state.task_to_edit = None

if st.session_state.task_to_edit:
    task_data = next((t for t in storage.list_tasks() if str(t['id']) == str(st.session_state.task_to_edit)), None)
    if task_data:
        with st.expander("✏️ Reconfigurar Tarefa", expanded=True):
            with st.form("edit_form"):
                st.subheader(f"Editando: {task_data['title']}")
                new_title = st.text_input("Título", value=task_data['title'])
                new_urgency = st.slider("Grau de Urgência", -5, 5, value=task_data.get('urgency', 0))
                new_importance = st.slider("Grau de Importância", -5, 5, value=task_data.get('importance', 0))
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Salvar Alterações", use_container_width=True):
                    updates = {"title": new_title, "urgency": new_urgency, "importance": new_importance}
                    storage.update_task(task_data['id'], updates)
                    st.session_state.task_to_edit = None
                    st.rerun()
                if col2.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                    st.session_state.task_to_edit = None
                    st.rerun()

st.header("🗺️ Mapa de Produtividade (Matriz de Eisenhower)")
with st.expander("➕ Adicionar nova tarefa"):
    with st.form(key="add_task_form", clear_on_submit=True):
        title = st.text_input("Título da Tarefa")
        urgency = st.slider("Grau de Urgência", -5, 5, 0)
        importance = st.slider("Grau de Importância", -5, 5, 0)
        submitted = st.form_submit_button("Adicionar Tarefa")
        if submitted:
            if title:
                storage.add_task(title, "", importance, urgency, None, [])
                st.success("Tarefa adicionada!")
                st.rerun()
            else:
                st.warning("O título é obrigatório.")

tasks = [t for t in storage.list_tasks() if t.get('status') != 'done']
if not tasks:
    st.info("Nenhuma tarefa ativa. Adicione uma para começar.")
else:
    df = pd.DataFrame(tasks)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['urgency'], y=df['importance'], mode='markers', marker=dict(size=15, color='#1f77b4', opacity=0.8), text=df['title'], hoverinfo='text'))
    fig.update_layout(title="Seu Mapa de Produtividade", xaxis_title="Grau de Urgência", yaxis_title="Grau de Importância", xaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=2, zerolinecolor='black'), yaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=2, zerolinecolor='black'), width=800, height=600, plot_bgcolor='rgba(0,0,0,0)', shapes=[dict(type="rect", xref="x", yref="y", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor="#d4edda", opacity=0.2, layer="below", line_width=0), dict(type="rect", xref="x", yref="y", x0=-5.5, y0=0, x1=0, y1=5.5, fillcolor="#fff3cd", opacity=0.2, layer="below", line_width=0), dict(type="rect", xref="x", yref="y", x0=0, y0=-5.5, x1=5.5, y1=0, fillcolor="#f8d7da", opacity=0.2, layer="below", line_width=0), dict(type="rect", xref="x", yref="y", x0=-5.5, y0=-5.5, x1=0, y1=0, fillcolor="#e2e3e5", opacity=0.2, layer="below", line_width=0)], annotations=[dict(x=2.75, y=2.75, text="Faça Primeiro", showarrow=False, font=dict(size=16, color="green")), dict(x=-2.75, y=2.75, text="Agende", showarrow=False, font=dict(size=16, color="#856404")), dict(x=2.75, y=-2.75, text="Delegue", showarrow=False, font=dict(size=16, color="#721c24")), dict(x=-2.75, y=-2.75, text="Elimine", showarrow=False, font=dict(size=16, color="grey"))])
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📋 Lista de Tarefas Ativas")
    for task in tasks:
        st.markdown("---")
        col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
        with col1:
            st.markdown(f"**{task['title']}**")
            st.caption(f"Quadrante: {task['quadrant']} | Urgência: {task.get('urgency', 0)} | Importância: {task.get('importance', 0)}")
        with col2:
            if st.button("✏️", key=f"edit_{task['id']}", help="Editar esta tarefa"):
                st.session_state.task_to_edit = task['id']
                st.rerun()
        with col3:
            if st.button("✔️", key=f"done_{task['id']}", help="Concluir esta tarefa"):
                storage.mark_done(task['id'])
                st.rerun()