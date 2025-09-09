import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import Storage

st.set_page_config(layout="wide")

# Inicializa a conexão com o storage
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

# Inicializa o estado de edição se não existir
if 'task_to_edit' not in st.session_state:
    st.session_state.task_to_edit = None

# Carrega a lista de tags disponíveis uma vez no início da página
available_tags = storage.list_tags()

# --- LÓGICA DA JANELA DE EDIÇÃO (POP-UP) ---
if st.session_state.task_to_edit:
    task_data = next((t for t in storage.list_tasks() if str(t['id']) == str(st.session_state.task_to_edit)), None)
    
    if task_data:
        with st.expander("✏️ Reconfigurar Tarefa", expanded=True):
            with st.form("edit_form"):
                st.subheader(f"Editando: {task_data['title']}")
                
                new_title = st.text_input("Título", value=task_data['title'])
                new_description = st.text_area("Descrição", value=task_data.get('description', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    new_urgency = st.slider("Grau de Urgência", -5, 5, value=task_data.get('urgency', 0))
                with col2:
                    new_importance = st.slider("Grau de Importância", -5, 5, value=task_data.get('importance', 0))
                
                new_due_date_str = task_data.get('due_date')
                new_due_date = pd.to_datetime(new_due_date_str).date() if new_due_date_str else None
                new_due_date = st.date_input("Data de Entrega", value=new_due_date)

                # Converte a string de tags da planilha em uma lista para o multiselect
                default_tags = [tag.strip() for tag in task_data.get('tags', '').split(',') if tag.strip()]
                
                # --- CAMPO DE TAGS ATUALIZADO ---
                selected_tags = st.multiselect(
                    "Selecione as Tags",
                    options=available_tags,
                    default=default_tags
                )
                
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.form_submit_button("Salvar Alterações", use_container_width=True):
                    updates = {
                        "title": new_title,
                        "description": new_description,
                        "urgency": new_urgency,
                        "importance": new_importance,
                        "due_date": new_due_date.isoformat() if new_due_date else "",
                        "tags": ", ".join(selected_tags) # Converte a lista de volta para string
                    }
                    storage.update_task(task_data['id'], updates)
                    st.session_state.task_to_edit = None
                    st.rerun()
                
                if btn_col2.form_submit_button("Cancelar", type="secondary", use_container_width=True):
                    st.session_state.task_to_edit = None
                    st.rerun()

# --- INTERFACE PRINCIPAL DA PÁGINA ---
st.header("🗺️ Mapa de Produtividade (Matriz de Eisenhower)")
with st.expander("➕ Adicionar nova tarefa"):
    with st.form(key="add_task_form", clear_on_submit=True):
        title = st.text_input("Título da Tarefa*")
        description = st.text_area("Descrição (opcional)")
        
        col1, col2 = st.columns(2)
        with col1:
            urgency = st.slider("Grau de Urgência", -5, 5, 0)
        with col2:
            importance = st.slider("Grau de Importância", -5, 5, 0)

        due_date = st.date_input("Data de Entrega (opcional)")
        
        # --- CAMPO DE TAGS ATUALIZADO ---
        tags = st.multiselect(
            "Selecione as Tags",
            options=available_tags
        )
        
        submitted = st.form_submit_button("Adicionar Tarefa")
        if submitted:
            if title:
                due_date_str = due_date.isoformat() if due_date else None
                storage.add_task(title, description, importance, urgency, due_date_str, tags)
                st.success("Tarefa adicionada!")
                st.rerun()
            else:
                st.warning("O título é obrigatório.")

# --- Exibe o gráfico e a lista de tarefas ---
tasks = [t for t in storage.list_tasks() if t.get('status') != 'done']

if not tasks:
    st.info("Nenhuma tarefa ativa. Adicione uma para começar.")
else:
    df = pd.DataFrame(tasks)
    
    # Adiciona a coluna de cores para o gráfico
    color_map = {
        "Faça Primeiro": "#1f77b4", # Azul
        "Agende": "#ff7f0e",       # Laranja
        "Delegue": "#d62728",      # Vermelho
        "Elimine": "#7f7f7f",       # Cinza
    }
    df['color'] = df['quadrant'].map(color_map).fillna('#7f7f7f')

    # Cria o hover text mais detalhado
    df['hover_text'] = df.apply(
        lambda row: f"<b>{row['title']}</b><br><br>" +
                    f"Descrição: {row.get('description', 'N/A')}<br>" +
                    f"Entrega: {row.get('due_date', 'N/A')}<br>" +
                    f"Tags: {row.get('tags', 'N/A')}",
        axis=1
    )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['urgency'], 
        y=df['importance'],
        mode='markers',
        marker=dict(size=15, color=df['color'], opacity=0.8, line=dict(width=1, color='DarkSlateGrey')),
        text=df['hover_text'],
        hoverinfo='text'
    ))

    # Layout do gráfico
    fig.update_layout(
        xaxis_title="Urgência", yaxis_title="Importância",
        xaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='rgba(200, 200, 200, 0.2)'),
        yaxis=dict(range=[-5.5, 5.5], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='rgba(200, 200, 200, 0.2)'),
        height=600, plot_bgcolor='rgba(240, 242, 246, 1)',
        shapes=[
            dict(type="rect", xref="paper", yref="paper", x0=0.5, y0=0.5, x1=1, y1=1, fillcolor="#d4edda", opacity=0.3, layer="below", line_width=0),
            dict(type="rect", xref="paper", yref="paper", x0=0, y0=0.5, x1=0.5, y1=1, fillcolor="#fff3cd", opacity=0.3, layer="below", line_width=0),
            dict(type="rect", xref="paper", yref="paper", x0=0.5, y0=0, x1=1, y1=0.5, fillcolor="#f8d7da", opacity=0.3, layer="below", line_width=0),
            dict(type="rect", xref="paper", yref="paper", x0=0, y0=0, x1=0.5, y1=0.5, fillcolor="#e2e3e5", opacity=0.3, layer="below", line_width=0),
        ],
        annotations=[
            dict(x=2.75, y=2.75, text="Faça Primeiro", showarrow=False, font=dict(size=16, color="#155724")),
            dict(x=-2.75, y=2.75, text="Agende", showarrow=False, font=dict(size=16, color="#856404")),
            dict(x=2.75, y=-2.75, text="Delegue", showarrow=False, font=dict(size=16, color="#721c24")),
            dict(x=-2.75, y=-2.75, text="Elimine", showarrow=False, font=dict(size=16, color="#383d41")),
        ]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Lista de Tarefas Ativas")
    for task in tasks:
        st.markdown("---")
        col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
        
        with col1:
            st.markdown(f"**{task['title']}**")
            st.caption(f"Entrega: {task.get('due_date', 'N/A')} | Tags: {task.get('tags', 'N/A')}")
        with col2:
            if st.button("✏️", key=f"edit_{task['id']}", help="Editar esta tarefa"):
                st.session_state.task_to_edit = task['id']
                st.rerun()
        with col3:
            if st.button("✔️", key=f"done_{task['id']}", help="Concluir esta tarefa"):
                storage.mark_done(task['id'])
                st.rerun()

