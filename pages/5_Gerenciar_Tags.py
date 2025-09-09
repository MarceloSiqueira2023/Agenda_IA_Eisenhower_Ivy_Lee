import streamlit as st
from utils import Storage

st.set_page_config(layout="wide")
st.header("⚙️ Gerenciar Tags (Categorias de Trabalho)")
st.markdown("Adicione, visualize e remova as categorias que você usa para organizar suas tarefas.")

# Inicializa a conexão com o storage
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

# Formulário para adicionar uma nova tag
st.subheader("Adicionar Nova Tag")
with st.form("add_tag_form", clear_on_submit=True):
    new_tag_name = st.text_input("Nome da nova tag:")
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        storage.add_tag(new_tag_name)
        st.rerun() # Recarrega a página para mostrar a nova tag na lista

# Exibe as tags existentes
st.markdown("---")
st.subheader("Tags Atuais")

current_tags = storage.list_tags()

if not current_tags:
    st.info("Nenhuma tag cadastrada. Adicione sua primeira categoria acima.")
else:
    # Exibe as tags em colunas para um layout mais limpo
    cols = st.columns(3)
    col_index = 0
    for tag in current_tags:
        with cols[col_index]:
            # Container para cada tag com o botão de remoção
            with st.container(border=True):
                col_tag, col_button = st.columns([0.8, 0.2])
                col_tag.write(tag)
                if col_button.button("🗑️", key=f"delete_{tag}", help=f"Remover a tag '{tag}'"):
                    storage.delete_tag(tag)
                    st.rerun() # Recarrega a página para atualizar a lista
        
        col_index = (col_index + 1) % 3
