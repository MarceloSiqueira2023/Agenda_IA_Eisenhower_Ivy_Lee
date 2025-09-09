# pages/1_Matriz_Eisenhower.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import Storage
from datetime import datetime

# --- Configuração e Inicialização ---
st.set_page_config(layout="wide")
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

if 'task_to_edit' not in st.session_state:
    st.session_state.task_to_edit = None

# --- Lógica da Janela de Edição (Pop-up) ---
if st.session_state.task_to_edit:
    task_data = next((t for t in storage.list_tasks() if str(t['id']) == str(st.session_state.task_to_edit)), None)
    
    if task_data:
        with st.expander("✏️ Reconfigurar Tarefa", expanded=True):
            with st.form("edit_form"):
                st.subheader(f"Editando: {task_data['title']}")
                
                # --- CAMPOS DO FORMULÁRIO DE EDIÇÃO (COMPLETOS) ---
                new_title = st.text_input("Título*", value=task_data['title'])
                new_description = st.text_area("Descrição", value=task_data.get('description', ''))
                
                current_due_date = None
                if task_data.get('due_date'):
                    try:
                        current_due_date = datetime.fromisoformat(task_data['due_date'].split('T')[0]).date()
                    except (ValueError, TypeError):
                        current_due_date = None

                new_due_date = st.date_input("Data de Entrega", value=current_due_date)
                
                current_tags = task_data.get('tags', '')
                new_tags = st.text_input("Tags (separadas por vírgula)", value=current_tags)

                col1, col2 = st.columns(2)
                with col1:
                    new_urgency = st.slider("Grau de Urgência", -5, 5, value=task_data.get('urgency', 0))
                with col2:
                    new_importance = st.slider("Grau de Importância", -5, 5, value=task_data.get('importance', 0))

                s_col1, s_col2 = st.columns(2)
                if s_col1.form_submit_button("Salvar Alterações", use_container_width=True):
                    updates = {
                        "title": new_title,
                        "description": new_description,
                        "due_date": new_due_date.isoformat() if new_due_date else "",
                        "tags": new_tags,
                        "urgency": new_urgency,
                        "importance": new_importance
                    }
                    storage.update_task(task_data['id'], updates)
                    st.session_state.task_to_edit = None
                    st.rerun()
                
                if s_col2.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                    st.session_state.task_to_edit = None
                    st.rerun()

# --- INTERFACE PRINCIPAL DA PÁGINA ---
st.header("🗺️ Mapa de Produtividade (Matriz de Eisenhower)")

with st.expander("➕ Adicionar nova tarefa"):
    with st.form(key="add_task_form", clear_on_submit=True):
        title = st.text_input("Título da Tarefa*")
        description = st.text_area("Descrição (opcional)")
        due_date = st.date_input("Data de Entrega (opcional)", value=None)
        tags_raw = st.text_input("Tags (separadas por vírgula)", placeholder="Ex: ensino, pesquisa, projeto_x")

        col1, col2 = st.columns(2)
        with col1:
            urgency = st.slider("Grau de Urgência", -5, 5, 0)
        with col2:
            importance = st.slider("Grau de Importância", -5, 5, 0)
        
        submitted = st.form_submit_button("Adicionar Tarefa")
        if submitted:
            if title:
                due_date_str = due_date.isoformat() if due_date else None
                tags_list = [tag.strip() for tag in tags_raw.split(',') if tag.strip()]
                storage.add_task(title, description, importance, urgency, due_date_str, tags_list)
                st.success("Tarefa adicionada!")
                st.rerun()
            else:
                st.warning("O título é obrigatório.")

# --- Carrega e exibe as tarefas ---
tasks = [t for t in storage.list_tasks() if t.get('status') != 'done']

if not tasks:
    st.info("Nenhuma tarefa ativa. Adicione uma para começar.")
else:
    # --- GRÁFICO VISUALMENTE APRIMORADO ---
    df = pd.DataFrame(tasks)

    # 1. Preparar dados para o gráfico (cores e texto de hover)
    quadrant_colors = {
        "Faça Primeiro": "#1f77b4", # Azul
        "Agende": "#ff7f0e",         # Laranja
        "Delegue": "#2ca02c",        # Verde
        "Elimine": "#d62728"         # Vermelho
    }
    df["color"] = df["quadrant"].apply(lambda q: quadrant_colors.get(q, "#8c564b")) # Usa a cor do quadrante ou um padrão

    df['hover_text'] = df.apply(
        lambda row: (
            f"<b>{row['title']}</b><br><br>"
            f"<b>Descrição:</b> {row.get('description') or 'Nenhuma'}<br>"
            f"<b>Entrega:</b> {row.get('due_date') or 'Não definida'}<br>"
            f"<b>Tags:</b> {row.get('tags') or 'Nenhuma'}<br>"
            f"<i>({row['quadrant']})</i>"
        ),
        axis=1
    )

    # 2. Criar a figura base
    fig = go.Figure()

    # 3. Adicionar as tarefas como scatter plot
    fig.add_trace(go.Scatter(
        x=df['urgency'],
        y=df['importance'],
        mode='markers',
        marker=dict(
            size=16,
            color=df['color'], # Usa a coluna de cores
            opacity=0.7,
            line=dict(width=1, color='DarkSlateGrey') # Borda sutil nos pontos
        ),
        text=df['hover_text'],
        hoverinfo='text'
    ))

    # 4. Configurar layout, eixos e quadrantes
    background_colors = {
        "Faça Primeiro": "rgba(204, 235, 255, 0.3)",
        "Agende": "rgba(255, 240, 204, 0.3)",
        "Delegue": "rgba(204, 255, 229, 0.3)",
        "Elimine": "rgba(242, 242, 242, 0.3)"
    }

    fig.update_layout(
        title=dict(text="<b>Seu Mapa de Produtividade</b>", font=dict(size=24), x=0.5),
        xaxis_title="← Menos Urgente | Mais Urgente →",
        yaxis_title="← Menos Importante | Mais Importante →",
        xaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=1, zerolinecolor='rgba(0,0,0,0.4)', gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=1, zerolinecolor='rgba(0,0,0,0.4)', gridcolor='rgba(0,0,0,0.05)'),
        height=600,
        plot_bgcolor='white',
        showlegend=False,
        shapes=[
            dict(type="rect", xref="x", yref="y", x0=0, y0=0, x1=5.5, y1=5.5, fillcolor=background_colors["Faça Primeiro"], layer="below", line_width=0),
            dict(type="rect", xref="x", yref="y", x0=-5.5, y0=0, x1=0, y1=5.5, fillcolor=background_colors["Agende"], layer="below", line_width=0),
            dict(type="rect", xref="x", yref="y", x0=0, y0=-5.5, x1=5.5, y1=0, fillcolor=background_colors["Delegue"], layer="below", line_width=0),
            dict(type="rect", xref="x", yref="y", x0=-5.5, y0=-5.5, x1=0, y1=0, fillcolor=background_colors["Elimine"], layer="below", line_width=0),
        ],
        annotations=[
            dict(x=2.75, y=2.75, text="<b>Faça Primeiro</b>", showarrow=False, font=dict(size=18, color=quadrant_colors["Faça Primeiro"])),
            dict(x=-2.75, y=2.75, text="<b>Agende</b>", showarrow=False, font=dict(size=18, color=quadrant_colors["Agende"])),
            dict(x=2.75, y=-2.75, text="<b>Delegue</b>", showarrow=False, font=dict(size=18, color=quadrant_colors["Delegue"])),
            dict(x=-2.75, y=-2.75, text="<b>Elimine</b>", showarrow=False, font=dict(size=18, color=quadrant_colors["Elimine"])),
        ]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # A lista de tarefas continua a mesma
    st.subheader("📋 Lista de Tarefas Ativas")
    for task in tasks:
        st.markdown("---")
        col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
        with col1:
            st.markdown(f"**{task['title']}**")
            details = [f"Urg: {task.get('urgency', 0)}", f"Imp: {task.get('importance', 0)}"]
            if task.get('due_date'):
                details.append(f"Entrega: {task['due_date']}")
            if task.get('tags'):
                details.append(f"Tags: {task['tags']}")
            st.caption(" | ".join(details))

        with col2:
            if st.button("✏️", key=f"edit_{task['id']}", help="Editar esta tarefa"):
                st.session_state.task_to_edit = task['id']
                st.rerun()
        with col3:
            if st.button("✔️", key=f"done_{task['id']}", help="Concluir esta tarefa"):
                storage.mark_done(task['id'])
                st.rerun()

