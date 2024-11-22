import pyodbc
import tkinter as tk
from tkinter import messagebox, ttk
import time
from dotenv import load_dotenv
import os

# Carica le credenziali dal file .env
load_dotenv()

# Funzione per connettersi al database tramite ODBC
def connect_to_db():
    try:
        dsn = os.getenv("DB_DSN")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        
        if not all([dsn, username, password]):
            raise ValueError("Credenziali mancanti. Assicurati che il file .env sia configurato correttamente.")
        
        conn_str = f"DSN={dsn};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;"
        return pyodbc.connect(conn_str)
    except Exception as e:
        raise RuntimeError(f"Errore nella connessione al database: {e}")

# Funzione per monitorare le query lente
def monitor_db(conn):
    try:
        cursor = conn.cursor()
        query = """
        SELECT 
            s.login_name AS Utente,
            r.start_time AS OraInizio,
            r.blocking_session_id AS Bloccante,
            r.wait_time / 1000 AS TempoAttesa,
            OBJECT_NAME(st.objectid) AS TabellaInterrogata
        FROM 
            sys.dm_exec_requests r
        JOIN 
            sys.dm_exec_sessions s ON r.session_id = s.session_id
        CROSS APPLY 
            sys.dm_exec_sql_text(r.sql_handle) st
        WHERE 
            r.wait_time > 240000;  -- Tempo in millisecondi (4 minuti)
        """
        cursor.execute(query)
        return cursor.fetchall()
    except pyodbc.Error as e:
        raise RuntimeError(f"Errore durante il monitoraggio: {e}")

# Funzione per avviare il monitoraggio continuo
def start_monitoring(tree):
    try:
        conn = connect_to_db()
        messagebox.showinfo("Successo", "Connessione al database riuscita. Monitoraggio avviato!")

        def update_tree():
            try:
                results = monitor_db(conn)
                for row in tree.get_children():
                    tree.delete(row)
                if results:
                    for record in results:
                        tree.insert("", "end", values=record)
                else:
                    tree.insert("", "end", values=("Nessuna query lenta rilevata", "", "", "", ""))
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il monitoraggio: {e}")
            finally:
                # Aggiorna ogni 10 secondi
                root.after(10000, update_tree)

        update_tree()
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante la connessione: {e}")

# GUI principale
def main():
    global root
    root = tk.Tk()
    root.title("Monitoraggio Query Lente")
    root.configure(bg="black")

    # Stile del testo
    style = {
        "fg": "#00FF00",
        "bg": "black",
        "font": ("Courier", 10)
    }

    # Messaggio di configurazione
    tk.Label(root, text="Le credenziali sono caricate dal file .env", **style).grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    # Tabella per visualizzare i risultati
    tree = ttk.Treeview(root, columns=("Utente", "Ora Inizio", "Bloccante", "Tempo Attesa", "Tabella"), show="headings")
    tree.heading("Utente", text="Utente")
    tree.heading("Ora Inizio", text="Ora Inizio")
    tree.heading("Bloccante", text="Bloccante")
    tree.heading("Tempo Attesa", text="Tempo Attesa (s)")
    tree.heading("Tabella", text="Tabella")
    tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Stile della tabella
    style = ttk.Style()
    style.configure("Treeview", background="black", foreground="#00FF00", fieldbackground="black")
    style.map("Treeview", background=[("selected", "#005500")], foreground=[("selected", "white")])

    # Pulsante per avviare il monitoraggio
    start_button = tk.Button(root, text="Avvia Monitoraggio", command=lambda: start_monitoring(tree), bg="black", fg="#00FF00", font=("Courier", 10))
    start_button.grid(row=3, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
