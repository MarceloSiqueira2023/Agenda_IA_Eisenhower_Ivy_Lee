# utils.py
# Versão final com gerenciamento de tags e agrupamento de tarefas por tags

import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
import uuid
from datetime import datetime
import json
import base64

# --- Imports para a IA (agora apenas para a função de voz) ---
from gtts import gTTS
import io

class Storage:
    def __init__(self):
        self.spreadsheet = self._connect_spreadsheet()
        self.tasks_worksheet = self.spreadsheet.worksheet("Página1")
        self.tags_worksheet = self._get_or_create_worksheet("Tags")
        self.columns = ['id', 'title', 'description', 'importance', 'urgency', 'due_date', 'tags', 'quadrant', 'status']

    def _connect_spreadsheet(self):
        try:
            creds_b64 = st.secrets.GSHEETS_CREDENTIALS_B64
            creds_bytes = base64.b64decode(creds_b64)
            creds_json_string = creds_bytes.decode('utf-8')
            creds_dict = json.loads(creds_json_string)
            gc = gspread.service_account_from_dict(creds_dict)
            return gc.open_by_url(st.secrets.GSHEETS_URL)
        except Exception as e:
            st.error(f"Erro fatal ao conectar com o Google Sheets: {e}")
            st.stop()

    def _get_or_create_worksheet(self, name: str):
        try:
            return self.spreadsheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=name, rows="100", cols="1")
            worksheet.update('A1', 'tag_name')
            return worksheet

    def _read_data(self) -> pd.DataFrame:
        try:
            df = pd.DataFrame(self.tasks_worksheet.get_all_records(head=1))
            for col in self.columns:
                if col not in df.columns: df[col] = pd.Series(dtype='object')
            df['importance'] = pd.to_numeric(df['importance'], errors='coerce').fillna(0).astype(int)
            df['urgency'] = pd.to_numeric(df['urgency'], errors='coerce').fillna(0).astype(int)
            return df[self.columns]
        except gspread.exceptions.WorksheetNotFound:
            st.error("Aba 'Página1' não encontrada na sua planilha. Verifique o nome.")
            st.stop()

    def _write_data(self, df: pd.DataFrame):
        set_with_dataframe(self.tasks_worksheet, df, resize=True)

    def list_tags(self) -> list[str]:
        try:
            tags = self.tags_worksheet.col_values(1)[1:]
            return sorted([tag for tag in tags if tag])
        except Exception as e:
            st.error(f"Não foi possível ler as tags: {e}")
            return []

    def add_tag(self, tag_name: str):
        if not tag_name or tag_name.isspace():
            st.warning("O nome da tag не pode estar vazio.")
            return
        current_tags = self.list_tags()
        if tag_name in current_tags:
            st.warning(f"A tag '{tag_name}' já existe.")
            return
        self.tags_worksheet.append_row([tag_name])
        st.success(f"Tag '{tag_name}' adicionada com sucesso!")

    def delete_tag(self, tag_name: str):
        try:
            cell = self.tags_worksheet.find(tag_name)
            if cell:
                self.tags_worksheet.delete_rows(cell.row)
                st.success(f"Tag '{tag_name}' removida.")
        except gspread.exceptions.CellNotFound:
            st.error(f"Tag '{tag_name}' não encontrada para remoção.")
        except Exception as e:
            st.error(f"Erro ao remover a tag: {e}")

    def list_tasks(self) -> list[dict]:
        df = self._read_data()
        return df.to_dict('records')

    def add_task(self, title: str, description: str, importance: int, urgency: int, due_date: str | None, tags: list[str]):
        quadrant = self._get_quadrant(importance, urgency)
        new_task_df = pd.DataFrame([{"id": str(uuid.uuid4()), "title": title, "description": description, "importance": importance, "urgency": urgency, "due_date": due_date if due_date else "", "tags": ", ".join(tags), "quadrant": quadrant, "status": "pending"}])
        existing_df = self._read_data()
        updated_df = pd.concat([existing_df, new_task_df], ignore_index=True)
        self._write_data(updated_df)
    
    def update_task(self, task_id: str, updates: dict):
        df = self._read_data()
        df['id'] = df['id'].astype(str)
        task_id = str(task_id)
        if task_id not in df['id'].values: return False
        idx = df[df['id'] == task_id].index[0]
        for key, value in updates.items():
            df.loc[idx, key] = value
        if 'importance' in updates or 'urgency' in updates:
            importance = int(df.loc[idx, 'importance'])
            urgency = int(df.loc[idx, 'urgency'])
            df.loc[idx, 'quadrant'] = self._get_quadrant(importance, urgency)
        self._write_data(df)
        return True

    def mark_done(self, task_id: str):
        df = self._read_data()
        df['id'] = df['id'].astype(str)
        task_id = str(task_id)
        if task_id in df['id'].values:
            df.loc[df['id'] == task_id, 'status'] = 'done'
            self._write_data(df)

    def get_urgent_tasks(self) -> list[dict]:
        df = self._read_data()
        urgent_df = df[(df['urgency'] > 0) & (df['status'] != 'done')]
        return urgent_df.to_dict('records')
    
    def get_top_n_pending_tasks(self, n: int = 6) -> list[dict]:
        df = self._read_data()
        pending_df = df[df['status'] != 'done']
        sorted_df = pending_df.sort_values(by=['importance', 'urgency'], ascending=[False, False])
        return sorted_df.head(n).to_dict('records')

    def reset(self):
        header = pd.DataFrame(columns=self.columns)
        self._write_data(header)

    def _get_quadrant(self, importance: int, urgency: int) -> str:
        if importance > 0 and urgency > 0: return "Faça Primeiro"
        if importance > 0 and not urgency > 0: return "Agende"
        if not importance > 0 and urgency > 0: return "Delegue"
        return "Elimine"

    # --- NOVA FUNÇÃO DE AGRUPAMENTO (MAIS SIMPLES E EFICIENTE) ---
    def group_tasks_by_tag(self) -> dict:
        """Agrupa tarefas pendentes pelas suas tags."""
        tasks = [t for t in self.list_tasks() if t.get('status') != 'done']
        all_defined_tags = self.list_tags()
        
        grouped_tasks = {tag: [] for tag in all_defined_tags}
        
        for task in tasks:
            task_tags_str = task.get('tags', '')
            if task_tags_str:
                task_tags_list = [tag.strip() for tag in task_tags_str.split(',')]
                for tag in task_tags_list:
                    if tag in grouped_tasks:
                        grouped_tasks[tag].append(task)
                        
        final_groups = {tag: tasks for tag, tasks in grouped_tasks.items() if tasks}
        
        return final_groups

def generate_audio_from_text(text: str, lang='pt', tld='com.br', slow=False):
    try:
        tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        print(f"Erro ao gerar áudio: {e}")
        return None

