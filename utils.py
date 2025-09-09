# utils.py
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
import uuid
from datetime import datetime
import json
import base64 # <-- Importamos a nova biblioteca

# --- Imports para a IA ---
import google.generativeai as genai
from sklearn.cluster import AgglomerativeClustering
import numpy as np
from gtts import gTTS
import io

class Storage:
    def __init__(self):
        self.worksheet = self._connect()
        self.columns = ['id', 'title', 'description', 'importance', 'urgency', 'due_date', 'tags', 'quadrant', 'status']

    def _connect(self):
        """Estabelece a conexão com a Planilha Google usando gspread e decodificando o segredo Base64."""
        try:
            # Pega a string codificada em Base64 dos segredos
            creds_b64 = st.secrets.GSHEETS_CREDENTIALS_B64
            # Decodifica a string Base64 de volta para bytes
            creds_bytes = base64.b64decode(creds_b64)
            # Decodifica os bytes para uma string JSON legível
            creds_json_string = creds_bytes.decode('utf-8')
            # Converte a string JSON em um dicionário Python
            creds_dict = json.loads(creds_json_string)

            gc = gspread.service_account_from_dict(creds_dict)
            spreadsheet = gc.open_by_url(st.secrets.GSHEETS_URL)
            worksheet = spreadsheet.worksheet("Página1")
            return worksheet
        except Exception as e:
            st.error(f"Erro fatal ao conectar com o Google Sheets: {e}")
            st.error("Verifique se a URL da planilha e as credenciais Base64 no arquivo secrets.toml estão corretas.")
            st.stop()

    def _read_data(self) -> pd.DataFrame:
        """Lê todos os dados da planilha e retorna como DataFrame."""
        try:
            df = pd.DataFrame(self.worksheet.get_all_records(head=1))
            for col in self.columns:
                if col not in df.columns:
                    df[col] = pd.Series(dtype='object')
            
            df['importance'] = pd.to_numeric(df['importance'], errors='coerce').fillna(0).astype(int)
            df['urgency'] = pd.to_numeric(df['urgency'], errors='coerce').fillna(0).astype(int)
            return df[self.columns]
        except gspread.exceptions.WorksheetNotFound:
            st.error("Aba 'Página1' não encontrada na sua planilha. Verifique o nome.")
            st.stop()

    def _write_data(self, df: pd.DataFrame):
        """Escreve o DataFrame inteiro de volta para a planilha."""
        set_with_dataframe(self.worksheet, df, resize=True)

    # ... O RESTO DO CÓDIGO DA CLASSE STORAGE CONTINUA EXATAMENTE O MESMO ...
    # (add_task, update_task, mark_done, etc. não mudam)
    
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

    def group_tasks_by_similarity_ai(self, api_key: str):
        tasks = [t for t in self.list_tasks() if t.get('status') != 'done']
        if len(tasks) < 2: return []
        try:
            genai.configure(api_key=api_key)
            titles = [task['title'] for task in tasks]
            result = genai.embed_content(model="models/embedding-001", content=titles)
            embeddings = result['embedding']
        except Exception as e:
            st.error(f"Erro ao contatar a API do Google: {e}")
            return []
        embeddings_array = np.array(embeddings)
        clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1.0, linkage='ward')
        labels = clustering.fit_predict(embeddings_array)
        num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        if num_clusters == 0: return []
        cluster_map = {label: [] for label in set(labels) if label != -1}
        for i, label in enumerate(labels):
            if label != -1: cluster_map[label].append(tasks[i])
        return [group for group in cluster_map.values() if len(group) > 1]


def generate_audio_from_text(text: str, lang='pt', tld='com.br', slow=False):
    # O código desta função permanece o mesmo
    try:
        tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        print(f"Erro ao gerar áudio: {e}")
        return None