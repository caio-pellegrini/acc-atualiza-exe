import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path
import threading
import re
import sys

class AutomatedUpdateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Atualização Automatizado")
        self.root.geometry("1100x750")
        self.root.configure(bg='#e0e0e0')

        # Define o caminho para o arquivo de log
        if getattr(sys, 'frozen', False):
            # Se estiver rodando como um executável PyInstaller
            application_path = os.path.dirname(sys.executable)
        else:
            # Se estiver rodando como um script .py
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.log_file_path = os.path.join(application_path, "log.txt")
        
        # Variáveis para os caminhos
        self.pasta_atualizacao = tk.StringVar(value="Atualizacao") 
        self.pasta_progs = tk.StringVar(value="PROGS") 
        
        self.progs_identified_files = []
        self.planned_actions_etapa2 = []
        
        self.setup_styles()
        self.create_widgets()
        self.center_window()
        self.log_message("Interface gráfica iniciada e log de arquivo configurado.", "info") # Log inicial

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        
        style.configure('TFrame', background='#e0e0e0')
        style.configure('TLabel', background='#e0e0e0', font=('Segoe UI', 9))
        style.configure('TLabelframe', background='#e0e0e0', bordercolor="#c0c0c0", font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background='#e0e0e0', foreground='#333', font=('Segoe UI', 10, 'bold'))
        style.configure('TEntry', font=('Segoe UI', 9))
        style.configure('TCheckbutton', background='#e0e0e0', font=('Segoe UI', 9))

        style.configure('Main.TButton', font=('Segoe UI', 10, 'bold'), padding=(10, 6))
        style.configure('Critical.TButton', font=('Segoe UI', 10, 'bold'), padding=(10, 6), background='#ffdddd', foreground='black')
        style.map('Critical.TButton', background=[('active', '#ffcccc')])
        style.configure('Standard.TButton', font=('Segoe UI', 9), padding=(8,4))

        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), background='#e0e0e0', foreground='#333')
        style.configure('Instruction.TLabel', font=('Segoe UI', 8, 'italic'), background='#e0e0e0', foreground='#555')

    def create_widgets(self):
        # Frame principal que se divide em dois
        top_frame = ttk.Frame(self.root, padding=(10,5)) 
        top_frame.pack(fill='x', side='top')
        
        title_label = ttk.Label(top_frame, 
                               text="Sistema de Atualização Automatizado de Arquivos (.exe, .dll)", 
                               style='Title.TLabel')
        title_label.pack(pady=(5, 10))

        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

        left_pane = ttk.Frame(content_frame, width=450, style='TFrame')
        left_pane.pack(side='left', fill='y', padx=(0, 10))
        left_pane.pack_propagate(False) 

        right_pane = ttk.Frame(content_frame, style='TFrame')
        right_pane.pack(side='right', fill='both', expand=True)

        # --- Widgets do Painel da Esquerda ---
        
        paths_frame = ttk.LabelFrame(left_pane, text="Pastas de Entrada", padding="10")
        paths_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(paths_frame, text="Pasta 'Atualizacao':", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=(0,2))
        ttk.Label(paths_frame, text="(Contém os arquivos mais recentes para atualizar)", style='Instruction.TLabel').grid(row=1, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_atualizacao = ttk.Entry(paths_frame, textvariable=self.pasta_atualizacao, width=35)
        self.entry_atualizacao.grid(row=2, column=0, sticky='ew', padx=(0, 5))
        btn_browse_atualizacao = ttk.Button(paths_frame, text="Procurar...", style='Standard.TButton', command=lambda: self.browse_folder(self.pasta_atualizacao, "Atualização"))
        btn_browse_atualizacao.grid(row=2, column=1, sticky='e')
        
        ttk.Label(paths_frame, text="Pasta 'PROGS':", font=('Segoe UI', 9, 'bold')).grid(row=3, column=0, sticky='w', pady=(10,2))
        ttk.Label(paths_frame, text="(Pasta principal dos programas no cliente/servidor)", style='Instruction.TLabel').grid(row=4, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_progs = ttk.Entry(paths_frame, textvariable=self.pasta_progs, width=35)
        self.entry_progs.grid(row=5, column=0, sticky='ew', padx=(0, 5))
        btn_browse_progs = ttk.Button(paths_frame, text="Procurar...", style='Standard.TButton', command=lambda: self.browse_folder(self.pasta_progs, "PROGS"))
        btn_browse_progs.grid(row=5, column=1, sticky='e')
        paths_frame.columnconfigure(0, weight=1)

        options_frame = ttk.LabelFrame(left_pane, text="Opções de Atualização", padding="10")
        options_frame.pack(fill='x', pady=(0, 15))
        
        self.backup_var = tk.BooleanVar(value=True)
        self.create_backup_check = ttk.Checkbutton(options_frame, 
                                                  text="Backup automático antes de sobrescrever arquivos", 
                                                  variable=self.backup_var)
        self.create_backup_check.pack(anchor='w', pady=(0,2))
        ttk.Label(options_frame, text="Se marcado, o arquivo existente na pasta PROGS será\nrenomeado (ex: arquivoDDMMAAAA.exe) antes da cópia.", style='Instruction.TLabel').pack(anchor='w', padx=(20,0), pady=(0,5))

        self.verbose_var = tk.BooleanVar(value=True) 
        self.verbose_check = ttk.Checkbutton(options_frame, 
                                           text="Registrar arquivos com datas idênticas no log", 
                                           variable=self.verbose_var)
        self.verbose_check.pack(anchor='w', pady=(5,2))
        ttk.Label(options_frame, text="Se marcado, informa no log quando os arquivos em 'Atualizacao'\ne 'PROGS' têm a mesma data de modificação.", style='Instruction.TLabel').pack(anchor='w', padx=(20,0), pady=(0,5))

        action_buttons_frame = ttk.LabelFrame(left_pane, text="Fluxo de Execução Controlado", padding="10")
        action_buttons_frame.pack(fill='x', pady=(0, 15))

        self.btn_etapa1 = ttk.Button(action_buttons_frame, text="Executar Etapa 1 – Identificar Arquivos", 
                                     style='Main.TButton', command=self.start_etapa1_identification)
        self.btn_etapa1.pack(fill='x', pady=5)
        ttk.Label(action_buttons_frame, text="Busca arquivos .exe e .dll na pasta PROGS e subpastas.\nRegistra os caminhos completos no log.", style='Instruction.TLabel').pack(anchor='w', pady=(0,10))
        
        self.btn_etapa2 = ttk.Button(action_buttons_frame, text="Executar Etapa 2 – Comparar e Atualizar", 
                                    style='Critical.TButton', command=self.start_etapa2_update, state='disabled')
        self.btn_etapa2.pack(fill='x', pady=5)
        ttk.Label(action_buttons_frame, text="Compara arquivos com a pasta 'Atualizacao'. Se mais recentes,\nremove versões antigas, faz backup (opcional) e copia os novos.\nRequer confirmação antes de modificar arquivos.", style='Instruction.TLabel').pack(anchor='w', pady=(0,10))

        control_buttons_frame = ttk.Frame(left_pane, padding="5")
        control_buttons_frame.pack(fill='x', pady=(15,0), side='bottom') # Push to bottom

        self.btn_clear_log = ttk.Button(control_buttons_frame, text="Limpar Log", style='Standard.TButton', command=self.clear_log)
        self.btn_clear_log.pack(side='left', padx=(0,10))
        
        self.btn_finalize = ttk.Button(control_buttons_frame, text="Finalizar", style='Standard.TButton', command=self.root.destroy)
        self.btn_finalize.pack(side='right')
        
        status_progress_frame = ttk.Frame(left_pane)
        status_progress_frame.pack(fill='x', pady=(10, 5), side='bottom')

        self.status_var = tk.StringVar(value="Pronto.")
        status_label = ttk.Label(status_progress_frame, textvariable=self.status_var, font=('Segoe UI', 9, 'italic'))
        status_label.pack(fill='x', pady=(0,5))
        
        self.progress_bar = ttk.Progressbar(status_progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x')
        
        # --- Widgets do Painel da Direita ---
        log_frame_outer = ttk.LabelFrame(right_pane, text="Log Detalhado de Operações", padding="10")
        log_frame_outer.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame_outer, 
                                                 height=10, 
                                                 font=('Consolas', 10), 
                                                 wrap=tk.WORD,
                                                 bg='#ffffff', 
                                                 fg='#000000') 
        self.log_text.pack(fill='both', expand=True)
        
        self.log_text.tag_configure('success', foreground='#008000', font=('Consolas', 10, 'bold')) 
        self.log_text.tag_configure('warning', foreground='#FF8C00', font=('Consolas', 10, 'bold')) 
        self.log_text.tag_configure('error', foreground='#CC0000', font=('Consolas', 10, 'bold'))   
        self.log_text.tag_configure('info', foreground='#00008B')    
        self.log_text.tag_configure('critical', foreground='#800080', font=('Consolas', 10, 'bold'))
        self.log_text.tag_configure('detail', foreground='#505050') 
        self.log_text.tag_configure('header', foreground='#000000', font=('Consolas', 10, 'bold', 'underline'))

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def browse_folder(self, var, folder_name):
        folder = filedialog.askdirectory(title=f"Selecione a Pasta '{folder_name}'")
        if folder:
            var.set(folder)
            self.log_message(f"Pasta '{folder_name}' definida para: {folder}", 'info')

    def log_message(self, message, tag='info'): 
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        formatted_message_gui = message.replace("\n", "\n" + " " * (len(timestamp) + 3)) # For GUI indentation
        full_message_for_gui = f"[{timestamp}] {formatted_message_gui}\n"
        
        # Log to GUI
        self.log_text.insert(tk.END, full_message_for_gui, tag)
        self.log_text.see(tk.END) 
        
        # Log to file (plain text, timestamp included)
        # For file, use the original message structure with timestamp but without extra spaces for GUI indent
        full_message_for_file = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f_log:
                f_log.write(full_message_for_file)
        except Exception as e:
            # If file logging fails, log this error to the GUI
            # Avoid calling log_message again here to prevent potential infinite loop if file error persists
            gui_error_msg = f"[{timestamp}] !!! CRITICAL: Falha ao escrever no arquivo de log ({self.log_file_path}): {str(e)} !!!\n"
            self.log_text.insert(tk.END, gui_error_msg, 'error')
            self.log_text.see(tk.END)
            
        self.root.update_idletasks()

    def clear_log(self):
        user_confirmation = messagebox.askyesno("Limpar Log", 
                                                "Tem certeza que deseja limpar todo o log de operações na tela?\n"
                                                "Isso também reiniciará as listas de arquivos identificados e ações planejadas.\n"
                                                "O arquivo 'log.txt' não será afetado.",
                                                icon='question')
        if user_confirmation:
            self.log_text.delete(1.0, tk.END)
            self.progs_identified_files = []
            self.planned_actions_etapa2 = []
            self.btn_etapa2.config(state='disabled')
            self.log_message("Log da tela limpo pelo usuário. Listas de arquivos e ações reiniciadas.", "info")
            self.status_var.set("Log da tela limpo. Pronto para Etapa 1.")

    def validate_paths_and_prepare(self):
        pasta_atualizacao_val = self.pasta_atualizacao.get().strip()
        pasta_progs_val = self.pasta_progs.get().strip()
        
        if not pasta_atualizacao_val or not pasta_progs_val:
            messagebox.showerror("Erro de Validação", "Por favor, informe os caminhos para as pastas 'Atualizacao' e 'PROGS'.")
            self.log_message("Erro de Validação: Caminhos para 'Atualizacao' ou 'PROGS' não informados.", "error")
            return False
        
        if not os.path.exists(pasta_atualizacao_val):
            messagebox.showerror("Erro de Validação", f"Pasta 'Atualizacao' não encontrada:\n{pasta_atualizacao_val}")
            self.log_message(f"Erro de Validação: Pasta 'Atualizacao' não encontrada: {pasta_atualizacao_val}", "error")
            return False
        
        if not os.path.exists(pasta_progs_val):
            messagebox.showerror("Erro de Validação", f"Pasta 'PROGS' não encontrada:\n{pasta_progs_val}")
            self.log_message(f"Erro de Validação: Pasta 'PROGS' não encontrada: {pasta_progs_val}", "error")
            return False
        self.log_message("Validação de caminhos concluída com sucesso.", "info")
        return True

    def set_buttons_state_during_operation(self, is_operating):
        state = 'disabled' if is_operating else 'normal'
        self.btn_etapa1.config(state=state)
        
        if not is_operating and self.progs_identified_files:
             self.btn_etapa2.config(state='normal')
        else:
             self.btn_etapa2.config(state='disabled')
        
        self.btn_clear_log.config(state=state)
        self.btn_finalize.config(state=state)

    def start_etapa1_identification(self):
        if not self.validate_paths_and_prepare():
            return
        
        self.set_buttons_state_during_operation(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 1: Identificando arquivos em PROGS...")
        
        self.progs_identified_files = [] 

        thread = threading.Thread(target=self.run_etapa1_identification_logic, daemon=True)
        thread.start()

    def run_etapa1_identification_logic(self):
        try:
            self.log_message("INICIANDO ETAPA 1: IDENTIFICAÇÃO DE ARQUIVOS", 'header')
            self.log_message(f"Buscando arquivos .exe e .dll na pasta PROGS: {self.pasta_progs.get()}", 'info')
            
            path_progs = Path(self.pasta_progs.get())
            file_count = 0
            for item in path_progs.rglob('*'): 
                if item.is_file() and item.suffix.lower() in ['.exe', '.dll']:
                    resolved_path = str(item.resolve())
                    self.progs_identified_files.append(resolved_path)
                    self.log_message(f"Arquivo encontrado: {resolved_path}", 'detail')
                    file_count +=1
            
            self.log_message(f"Total de arquivos (.exe, .dll) encontrados em PROGS: {file_count}", 'info')
            self.log_message("ETAPA 1 CONCLUÍDA", 'success')
            
            if not self.progs_identified_files:
                self.log_message("Nenhum arquivo .exe ou .dll encontrado na pasta PROGS.", 'warning')
                self.status_var.set("Etapa 1: Concluída. Nenhum arquivo encontrado.")
            else:
                self.status_var.set(f"Etapa 1: Concluída. {file_count} arquivo(s) identificado(s). Pronto para Etapa 2.")

        except Exception as e:
            error_msg = f"Erro na Etapa 1: {str(e)}"
            self.log_message(error_msg, 'error')
            messagebox.showerror("Erro - Etapa 1", error_msg)
            self.status_var.set("Erro na Etapa 1.")
        finally:
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)

    def start_etapa2_update(self):
        if not self.progs_identified_files:
            msg = "Nenhum arquivo foi identificado na Etapa 1. Execute a Etapa 1 primeiro."
            messagebox.showwarning("Aviso - Etapa 2", msg)
            self.log_message(f"Aviso Etapa 2: {msg}", "warning")
            return
        if not self.validate_paths_and_prepare(): 
            return

        self.set_buttons_state_during_operation(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 2: Analisando arquivos para atualização...")
        self.planned_actions_etapa2 = [] 

        thread = threading.Thread(target=self.run_etapa2_analysis_phase, daemon=True)
        thread.start()
    
    def run_etapa2_analysis_phase(self):
        try:
            self.log_message("INICIANDO ETAPA 2 (FASE DE ANÁLISE): COMPARAÇÃO DE ARQUIVOS", 'header')
            self.log_message(f"Pasta PROGS (origem): {self.pasta_progs.get()}", 'info')
            self.log_message(f"Pasta Atualizacao (comparação): {self.pasta_atualizacao.get()}", 'info')
            self.log_message(f"Verificando {len(self.progs_identified_files)} arquivo(s) identificados na Etapa 1.", 'info')
            
            base_progs_path = Path(self.pasta_progs.get())
            base_atualizacao_path = Path(self.pasta_atualizacao.get())
            
            for progs_file_full_path_str in self.progs_identified_files:
                progs_file_path = Path(progs_file_full_path_str)
                try:
                    relative_path = progs_file_path.relative_to(base_progs_path)
                except ValueError:
                    self.log_message(f"ERRO INTERNO: Arquivo {progs_file_path} não parece estar dentro da pasta PROGS base {base_progs_path}. Ignorando.", "error")
                    continue

                atualizacao_file_path = base_atualizacao_path / relative_path
                
                self.log_message(f"Analisando: {progs_file_path.name} (em {relative_path.parent})", 'detail')

                if not atualizacao_file_path.exists(): 
                    self.log_message(f"  -> Ignorado: Arquivo correspondente NÃO ENCONTRADO em 'Atualizacao': {atualizacao_file_path}.", 'detail')
                    continue

                mtime_progs = progs_file_path.stat().st_mtime
                mtime_atualizacao = atualizacao_file_path.stat().st_mtime
                
                date_progs_str = datetime.fromtimestamp(mtime_progs).strftime('%d/%m/%Y %H:%M:%S')
                date_atualizacao_str = datetime.fromtimestamp(mtime_atualizacao).strftime('%d/%m/%Y %H:%M:%S')

                if mtime_atualizacao == mtime_progs: 
                    if self.verbose_var.get():
                        self.log_message(f"  -> Datas de modificação IGUAIS para '{progs_file_path.name}'. Nenhuma ação.", 'info')
                        self.log_message(f"     PROGS: {date_progs_str}, Atualizacao: {date_atualizacao_str}", 'detail')
                    continue
                elif mtime_atualizacao < mtime_progs: 
                    self.log_message(f"  -> ALERTA: Versão em 'Atualizacao' de '{progs_file_path.name}' é MAIS ANTIGA. Nenhuma substituição será feita.", 'error')
                    self.log_message(f"     PROGS: {date_progs_str} (mais recente)", 'error')
                    self.log_message(f"     Atualizacao: {date_atualizacao_str} (mais antiga)", 'error')
                    continue
                
                self.log_message(f"  -> ATUALIZAÇÃO NECESSÁRIA para '{progs_file_path.name}'. Versão em 'Atualizacao' é MAIS RECENTE.", 'warning')
                self.log_message(f"     PROGS: {date_progs_str} (será atualizado)", 'warning')
                self.log_message(f"     Atualizacao: {date_atualizacao_str} (mais recente)", 'warning')

                action_details = {
                    'progs_file_path_str': str(progs_file_path.resolve()),
                    'atualizacao_file_path_str': str(atualizacao_file_path.resolve()),
                    'target_dir_str': str(progs_file_path.parent.resolve()),
                    'original_filename': progs_file_path.name,
                    'base_name': progs_file_path.stem, 
                    'extension': progs_file_path.suffix,
                }
                self.planned_actions_etapa2.append(action_details)

            self.log_message("FASE DE ANÁLISE DA ETAPA 2 CONCLUÍDA", 'success')
            
            if not self.planned_actions_etapa2:
                self.status_var.set("Etapa 2: Análise concluída. Nenhum arquivo para atualizar.")
                self.log_message("Nenhum arquivo precisa ser atualizado com base na data de modificação.", "info")
                self.progress_bar.stop()
                self.set_buttons_state_during_operation(False)
                return

            self.log_message(f"Total de arquivos que precisam de atualização: {len(self.planned_actions_etapa2)}", 'critical')
            self.status_var.set("Etapa 2: Análise concluída. Aguardando confirmação para atualizar...")
            self.root.after(0, self._request_update_confirmation_dialog)

        except Exception as e:
            error_msg = f"Erro durante a análise da Etapa 2: {str(e)}"
            self.log_message(error_msg, 'error')
            messagebox.showerror("Erro - Etapa 2 (Análise)", error_msg)
            self.status_var.set("Erro na Etapa 2 (Análise).")
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)

    def _request_update_confirmation_dialog(self):
        num_updates = len(self.planned_actions_etapa2)
        confirm_msg = f"CONFIRMAÇÃO NECESSÁRIA\n\n"
        confirm_msg += f"{num_updates} arquivo(s) são mais recentes na pasta 'Atualizacao' e estão planejados para atualização.\n\n"
        confirm_msg += "O processo de atualização irá:\n"
        confirm_msg += "1. Remover arquivos antigos (com sufixos de data ou prefixo 'old_') nas pastas de destino em 'PROGS' para cada arquivo a ser atualizado.\n"
        if self.backup_var.get():
            confirm_msg += "2. Renomear os arquivos atuais em 'PROGS' (adicionando data atual, ex: arquivoDDMMAAAA.exe) como backup.\n"
            confirm_msg += "3. Copiar os arquivos novos da 'Atualizacao' para 'PROGS', mantendo o nome original.\n"
        else:
            confirm_msg += "2. Copiar os arquivos novos da 'Atualizacao' para 'PROGS' (SOBRESCREVENDO SEM BACKUP dos arquivos atuais).\n"

        confirm_msg += "\nEsta operação modifica arquivos no sistema de destino e é crítica.\n"
        confirm_msg += "Verifique o log para detalhes dos arquivos afetados.\n\n"
        confirm_msg += "Deseja continuar e aplicar estas atualizações?"
        
        user_confirmed = messagebox.askyesno("Confirmação Crítica de Atualização", confirm_msg, icon='warning')
        
        if user_confirmed:
            self.status_var.set("Etapa 2: Confirmação recebida. Iniciando execução das atualizações...")
            self.log_message("CONFIRMAÇÃO DO USUÁRIO: Atualização autorizada.", 'critical')
            execution_thread = threading.Thread(target=self.run_etapa2_execution_phase, daemon=True)
            execution_thread.start()
        else:
            self.log_message("ATUALIZAÇÃO CANCELADA PELO USUÁRIO.", 'warning')
            self.status_var.set("Etapa 2: Atualização cancelada pelo usuário.")
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)

    def run_etapa2_execution_phase(self):
        try:
            self.log_message("INICIANDO ETAPA 2 (FASE DE EXECUÇÃO): APLICANDO ATUALIZAÇÕES", 'header')
            arquivos_atualizados_count = 0
            erros_count = 0

            for action in self.planned_actions_etapa2:
                progs_file_path = Path(action['progs_file_path_str'])
                atualizacao_file_path = Path(action['atualizacao_file_path_str'])
                target_dir = Path(action['target_dir_str'])
                original_filename = action['original_filename']
                base_name = action['base_name']
                extension = action['extension']

                self.log_message(f"Processando atualização para: '{original_filename}' em '{target_dir}'", 'info')

                try:
                    self.log_message(f"  Passo 6.1: Verificando e removendo arquivos antigos para '{original_filename}'...", 'detail')
                    self._remove_legacy_files_step_6_1(target_dir, base_name, extension)

                    if self.backup_var.get():
                        if progs_file_path.exists(): 
                            self.log_message(f"  Passo 6.2: Criando backup de '{original_filename}'...", 'detail')
                            self._backup_file_with_date_step_6_2(progs_file_path)
                        else:
                            self.log_message(f"  Passo 6.2 (Backup): Arquivo '{original_filename}' não encontrado em PROGS para backup (pode já ter sido processado ou removido).", 'warning')
                    else:
                        self.log_message(f"  Passo 6.2: Backup automático desabilitado. O arquivo '{original_filename}' será sobrescrito diretamente se existir.", 'detail')

                    self.log_message(f"  Passo 6.3: Copiando nova versão de '{original_filename}' de 'Atualizacao' para 'PROGS'...", 'detail')
                    target_dir.mkdir(parents=True, exist_ok=True) 
                    shutil.copy2(str(atualizacao_file_path), str(target_dir / original_filename)) 
                    
                    self.log_message(f"  -> SUCESSO: '{original_filename}' atualizado com sucesso.", 'success')
                    arquivos_atualizados_count += 1

                except Exception as file_op_error:
                    erros_count += 1
                    self.log_message(f"  -> ERRO AO ATUALIZAR '{original_filename}': {str(file_op_error)}", 'error')
            
            self.log_message("FASE DE EXECUÇÃO DA ETAPA 2 CONCLUÍDA", 'success')
            self.log_message(f"Total de arquivos atualizados com sucesso: {arquivos_atualizados_count}", 'success')
            if erros_count > 0:
                self.log_message(f"Total de erros durante a atualização: {erros_count}", 'error')
            
            summary_title = "Atualização Concluída"
            summary_msg = f"Processo de atualização finalizado!\n\n" \
                          f"✅ Arquivos atualizados com sucesso: {arquivos_atualizados_count}\n" \
                          f"❌ Erros encontrados durante a operação: {erros_count}"
            
            self.root.after(0, lambda: messagebox.showinfo(summary_title, summary_msg) if erros_count == 0 else messagebox.showwarning(summary_title, summary_msg))

        except Exception as e:
            error_msg = f"Erro crítico durante a execução da Etapa 2: {str(e)}"
            self.log_message(error_msg, 'error')
            self.root.after(0, lambda: messagebox.showerror("Erro - Etapa 2 (Execução)", error_msg))
        finally:
            self.status_var.set(f"Etapa 2: Concluída. {arquivos_atualizados_count} atualizado(s), {erros_count} erro(s).")
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)
            self.planned_actions_etapa2 = [] 

    def _remove_legacy_files_step_6_1(self, target_dir: Path, base_name_to_update: str, extension_to_update: str):
        files_removed_count = 0
        date_suffix_pattern = re.compile(rf"^{re.escape(base_name_to_update)}(\d{{6,8}})$", re.IGNORECASE)
        old_prefix_pattern = re.compile(rf"^old_{re.escape(base_name_to_update)}.*$", re.IGNORECASE)

        for item in target_dir.iterdir():
            if item.is_file() and item.suffix.lower() == extension_to_update.lower():
                if item.name.lower() == (base_name_to_update + extension_to_update).lower():
                    continue

                should_remove = False
                reason = ""
                if date_suffix_pattern.match(item.stem):
                    should_remove = True
                    reason = "sufixo de data"
                elif old_prefix_pattern.match(item.stem):
                    should_remove = True
                    reason = "prefixo 'old_'"
                
                if should_remove:
                    try:
                        item.unlink()
                        self.log_message(f"     Removido arquivo legado ('{reason}'): {item.name}", 'detail')
                        files_removed_count +=1
                    except Exception as e:
                        self.log_message(f"     ERRO ao remover arquivo legado '{item.name}': {e}", 'error')
        
        if files_removed_count == 0:
            self.log_message(f"     Nenhum arquivo legado (com data/old) correspondente a '{base_name_to_update+extension_to_update}' encontrado para remoção.", 'detail')

    def _backup_file_with_date_step_6_2(self, progs_file_path: Path):
        directory = progs_file_path.parent
        base_name = progs_file_path.stem
        extension = progs_file_path.suffix
        current_date_str = datetime.now().strftime('%d%m%Y')
        backup_base_name_with_date = f"{base_name}{current_date_str}"
        new_backup_name = f"{backup_base_name_with_date}{extension}"
        new_backup_path = directory / new_backup_name
        
        counter = 1
        while new_backup_path.exists(): 
            new_backup_name = f"{backup_base_name_with_date}_{counter}{extension}"
            new_backup_path = directory / new_backup_name
            counter += 1
        
        try:
            progs_file_path.rename(new_backup_path)
            self.log_message(f"     Backup criado: '{progs_file_path.name}' renomeado para '{new_backup_path.name}'", 'success')
        except Exception as e:
            self.log_message(f"     ERRO ao criar backup para '{progs_file_path.name}' como '{new_backup_path.name}': {e}", 'error')
            raise 

def resource_path(relative_path):
    """Retorna o caminho para o recurso, mesmo se estiver embutido no .exe"""
    try:
        base_path = sys._MEIPASS  # Criado automaticamente pelo PyInstaller
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__)) # Use absolute path for script context
    return os.path.join(base_path, relative_path)

def main():
    root = tk.Tk()
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
             # Use default=icon_path on Windows to set icon for app and child windows (like dialogs)
            root.iconbitmap(default=icon_path)
        # else: # Icon not found, will use default Tk icon. No explicit error message needed unless debugging.
        #     print(f"Debug: Icon not found at {icon_path}") # Optional: for debugging
    except tk.TclError:
        # This can happen if the icon file is corrupted or not a valid .ico format for Tk
        # print("Debug: TclError setting icon - possibly invalid icon format or missing.") # Optional
        pass 
    except Exception as e:
        # Catch any other unexpected error during icon setting
        # print(f"Debug: An unexpected error occurred while setting icon: {e}") # Optional
        pass

    if os.name == 'nt':
        try:
            s = ttk.Style()
            s.theme_use('vista') 
        except ImportError:
            pass 
    app = AutomatedUpdateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()