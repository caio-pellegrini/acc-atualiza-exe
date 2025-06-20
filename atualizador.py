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

        # Lista para armazenar pastas a ignorar
        self.ignore_list = []

        # Define o caminho para o arquivo de log
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.log_file_path = os.path.join(application_path, "log.txt")
        
        # Variáveis para os caminhos
        self.pasta_atualizacao = tk.StringVar(value="Atualizacao")
        self.pasta_progs = tk.StringVar(value="C:\\PROGS")
        
        self.progs_identified_files = []
        self.planned_actions_etapa2 = []
        
        self.setup_styles()
        self.create_widgets()
        self.center_window()
        
        self.log_message("Interface gráfica iniciada e arquivo de log configurado.", "info")
        self.log_message("Pasta 'PROGS' definida inicialmente como 'C:\\PROGS'. Altere se necessário.", "info")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#e0e0e0')
        style.configure('TLabel', background='#e0e0e0', font=('Segoe UI', 9))
        style.configure('TLabelframe', background='#e0e0e0', bordercolor="#c0c0c0", font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background='#e0e0e0', foreground='#333', font=('Segoe UI', 10, 'bold'))
        style.configure('TEntry', font=('Segoe UI', 9))
        style.configure('TCheckbutton', background='#e0e0e0', font=('Segoe UI', 9))
        style.configure('TListbox', font=('Segoe UI', 9))

        style.configure('Main.TButton', font=('Segoe UI', 10, 'bold'), padding=(10, 6))
        style.configure('Critical.TButton', font=('Segoe UI', 10, 'bold'), padding=(10, 6), background='#ffdddd', foreground='black')
        style.map('Critical.TButton', background=[('active', '#ffcccc')])
        style.configure('Standard.TButton', font=('Segoe UI', 9), padding=(8,4))
        style.configure('Small.TButton', font=('Segoe UI', 8), padding=(5,3))

        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), background='#e0e0e0', foreground='#333')
        style.configure('Instruction.TLabel', font=('Segoe UI', 8, 'italic'), background='#e0e0e0', foreground='#555')

    def create_widgets(self):
        # Frame principal
        top_frame = ttk.Frame(self.root, padding=(10,5))
        top_frame.pack(fill='x', side='top')
        
        title_label = ttk.Label(top_frame, text="Sistema de Atualização Automatizado de Arquivos (.exe, .dll)", style='Title.TLabel')
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
        paths_frame.pack(fill='x', pady=(0, 10), anchor='n')

        ttk.Label(paths_frame, text="Pasta 'PROGS':", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=(5,2))
        ttk.Label(paths_frame, text="(Pasta principal dos programas no cliente/servidor)", style='Instruction.TLabel').grid(row=1, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_progs = ttk.Entry(paths_frame, textvariable=self.pasta_progs, width=35)
        self.entry_progs.grid(row=2, column=0, sticky='ew', padx=(0, 5))
        btn_browse_progs = ttk.Button(paths_frame, text="Procurar...", style='Standard.TButton', command=lambda: self.browse_folder(self.pasta_progs, "PROGS"))
        btn_browse_progs.grid(row=2, column=1, sticky='e')
        
        ttk.Label(paths_frame, text="Pasta 'Atualizacao':", font=('Segoe UI', 9, 'bold')).grid(row=3, column=0, sticky='w', pady=(5,2))
        ttk.Label(paths_frame, text="(Contém os arquivos mais recentes para atualizar)", style='Instruction.TLabel').grid(row=4, column=0, columnspan=2, sticky='w', pady=(0,5))
        self.entry_atualizacao = ttk.Entry(paths_frame, textvariable=self.pasta_atualizacao, width=35)
        self.entry_atualizacao.grid(row=5, column=0, sticky='ew', padx=(0, 5))
        btn_browse_atualizacao = ttk.Button(paths_frame, text="Procurar...", style='Standard.TButton', command=lambda: self.browse_folder(self.pasta_atualizacao, "Atualização"))
        btn_browse_atualizacao.grid(row=5, column=1, sticky='e')
        paths_frame.columnconfigure(0, weight=1)

        # Seção de Pastas a Ignorar
        ignore_frame = ttk.LabelFrame(left_pane, text="Pastas a Ignorar", padding="10")
        ignore_frame.pack(fill='x', pady=(0, 10), anchor='n')
        
        ttk.Label(ignore_frame, text="Pastas listadas aqui não serão analisadas nem atualizadas.", style='Instruction.TLabel').pack(anchor='w', pady=(0,5))
        
        listbox_frame = ttk.Frame(ignore_frame)
        listbox_frame.pack(fill='x', expand=True)

        self.ignore_listbox = tk.Listbox(listbox_frame, height=4, font=('Segoe UI', 9), selectmode=tk.EXTENDED)
        self.ignore_listbox.pack(side='left', fill='x', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.ignore_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.ignore_listbox.config(yscrollcommand=scrollbar.set)
        
        ignore_buttons_frame = ttk.Frame(ignore_frame)
        ignore_buttons_frame.pack(fill='x', pady=(5,0))
        
        btn_add_ignore = ttk.Button(ignore_buttons_frame, text="Adicionar", style='Small.TButton', command=self.add_ignore_folder)
        btn_add_ignore.pack(side='left', expand=True, fill='x', padx=(0,2))
        
        btn_remove_ignore = ttk.Button(ignore_buttons_frame, text="Remover Selecionada", style='Small.TButton', command=self.remove_ignore_folder)
        btn_remove_ignore.pack(side='left', expand=True, fill='x', padx=(2,0))
        
        options_frame = ttk.LabelFrame(left_pane, text="Opções de Atualização", padding="10")
        options_frame.pack(fill='x', pady=(0, 10), anchor='n')
        
        self.backup_var = tk.BooleanVar(value=True)
        self.create_backup_check = ttk.Checkbutton(options_frame, text="Backup automático antes de sobrescrever arquivos", variable=self.backup_var)
        self.create_backup_check.pack(anchor='w', pady=(0,2))
        ttk.Label(options_frame, text="Se marcado, o arquivo existente será renomeado (ex: arquivoDDMMAAAA.exe).", style='Instruction.TLabel').pack(anchor='w', padx=(20,0), pady=(0,5))

        action_buttons_frame = ttk.LabelFrame(left_pane, text="Fluxo de Execução Controlado", padding="10")
        action_buttons_frame.pack(fill='both', expand=True, pady=(0, 10), anchor='n')

        self.btn_etapa1 = ttk.Button(action_buttons_frame, text="Etapa 1 – Identificar Arquivos", style='Main.TButton', command=self.start_etapa1_identification)
        self.btn_etapa1.pack(fill='x', pady=5)
        
        self.btn_etapa2 = ttk.Button(action_buttons_frame, text="Etapa 2 – Comparar e Atualizar", style='Critical.TButton', command=self.start_etapa2_update, state='disabled')
        self.btn_etapa2.pack(fill='x', pady=5)

        # Bottom controls
        bottom_frame = ttk.Frame(left_pane)
        bottom_frame.pack(fill='x', side='bottom', pady=(10,0))
        
        status_progress_frame = ttk.Frame(bottom_frame)
        status_progress_frame.pack(fill='x', pady=(0, 5))

        self.status_var = tk.StringVar(value="Pronto.")
        status_label = ttk.Label(status_progress_frame, textvariable=self.status_var, font=('Segoe UI', 9, 'italic'))
        status_label.pack(fill='x', pady=(0,5))
        
        self.progress_bar = ttk.Progressbar(status_progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x')
        
        control_buttons_frame = ttk.Frame(bottom_frame, padding=(0, 5, 0, 0))
        control_buttons_frame.pack(fill='x')

        self.btn_clear_log = ttk.Button(control_buttons_frame, text="Limpar Log", style='Standard.TButton', command=self.clear_log)
        self.btn_clear_log.pack(side='left')
        
        self.btn_finalize = ttk.Button(control_buttons_frame, text="Finalizar", style='Standard.TButton', command=self.root.destroy)
        self.btn_finalize.pack(side='right')
        
        # --- Painel da Direita (Log) ---
        log_frame_outer = ttk.LabelFrame(right_pane, text="Log Detalhado de Operações", padding="10")
        log_frame_outer.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame_outer, height=10, font=('Consolas', 10), wrap=tk.WORD, bg='#ffffff', fg='#000000')
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
        if not folder:
            return

        normalized_folder = os.path.normpath(folder)
        var.set(normalized_folder)
        self.log_message(f"Pasta '{folder_name}' definida para: {normalized_folder}", 'info')
        
        if folder_name == "Atualização":
            progs_path = os.path.normpath(self.pasta_progs.get())
            if os.path.commonpath([progs_path, normalized_folder]) == progs_path:
                if normalized_folder not in self.ignore_list:
                    self.ignore_list.append(normalized_folder)
                    self.update_ignore_listbox()
                    self.log_message(f"Pasta 'Atualizacao' está dentro de 'PROGS' e foi adicionada à lista de ignorados.", 'warning')

    def add_ignore_folder(self):
        folder = filedialog.askdirectory(title="Selecione uma pasta para ignorar")
        if folder:
            normalized_folder = os.path.normpath(folder)
            if normalized_folder not in self.ignore_list:
                self.ignore_list.append(normalized_folder)
                self.update_ignore_listbox()
                self.log_message(f"Pasta adicionada à lista de ignorados: {normalized_folder}", 'info')
            else:
                self.log_message(f"A pasta '{normalized_folder}' já está na lista de ignorados.", 'detail')

    def remove_ignore_folder(self):
        selected_indices = self.ignore_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Nenhuma Seleção", "Por favor, selecione uma ou mais pastas para remover.")
            return

        for index in sorted(selected_indices, reverse=True):
            removed_folder = self.ignore_list.pop(index)
            self.log_message(f"Pasta removida da lista de ignorados: {removed_folder}", 'info')
        
        self.update_ignore_listbox()

    def update_ignore_listbox(self):
        self.ignore_listbox.delete(0, tk.END)
        for folder in sorted(self.ignore_list):
            self.ignore_listbox.insert(tk.END, folder)

    def log_message(self, message, tag='info'):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        formatted_message_gui = message.replace("\n", "\n" + " " * (len(timestamp) + 3))
        full_message_for_gui = f"[{timestamp}] {formatted_message_gui}\n"
        
        self.log_text.insert(tk.END, full_message_for_gui, tag)
        self.log_text.see(tk.END)
        
        full_message_for_file = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f_log:
                f_log.write(full_message_for_file)
        except Exception as e:
            gui_error_msg = f"[{timestamp}] !!! CRITICAL: Falha ao escrever no arquivo de log ({self.log_file_path}): {e} !!!\n"
            self.log_text.insert(tk.END, gui_error_msg, 'error')
            self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        if messagebox.askyesno("Limpar Log", "Tem certeza que deseja limpar o log na tela?"):
            self.log_text.delete(1.0, tk.END)
            self.log_message("Log da tela limpo pelo usuário.", "info")

    def validate_paths_and_prepare(self):
        pasta_atualizacao_val = os.path.normpath(self.pasta_atualizacao.get().strip())
        pasta_progs_val = os.path.normpath(self.pasta_progs.get().strip())
        
        if not pasta_atualizacao_val or not pasta_progs_val:
            messagebox.showerror("Erro de Validação", "Informe os caminhos para 'Atualizacao' e 'PROGS'.")
            return False
        if not os.path.exists(pasta_atualizacao_val):
            messagebox.showerror("Erro de Validação", f"Pasta 'Atualizacao' não encontrada:\n{pasta_atualizacao_val}")
            return False
        if not os.path.exists(pasta_progs_val):
            messagebox.showerror("Erro de Validação", f"Pasta 'PROGS' não encontrada:\n{pasta_progs_val}")
            return False
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
        self.ignore_listbox.config(state=state)

    def start_etapa1_identification(self):
        if not self.validate_paths_and_prepare():
            return
        
        self.progs_identified_files = []
        self.planned_actions_etapa2 = []
        self.set_buttons_state_during_operation(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 1: Identificando arquivos em PROGS...")
        
        thread = threading.Thread(target=self.run_etapa1_identification_logic, daemon=True)
        thread.start()

    def run_etapa1_identification_logic(self):
        try:
            self.log_message("INICIANDO ETAPA 1: IDENTIFICAÇÃO DE ARQUIVOS", 'header')
            path_progs_str = os.path.normpath(self.pasta_progs.get())
            self.log_message(f"Buscando em: {path_progs_str}", 'info')
            
            normalized_ignore_list = [os.path.normpath(p) for p in self.ignore_list]
            if normalized_ignore_list:
                self.log_message("Pastas a ignorar na verificação:", 'info')
                for p in normalized_ignore_list:
                    self.log_message(f" - {p}", 'detail')

            file_count = 0
            for root, dirs, files in os.walk(path_progs_str, topdown=True):
                normalized_root = os.path.normpath(root)
                is_ignored = any(normalized_root.startswith(ignore_path) for ignore_path in normalized_ignore_list)
                if is_ignored:
                    dirs[:] = []
                    continue

                for filename in files:
                    if filename.lower().endswith(('.exe', '.dll')):
                        full_path = os.path.join(root, filename)
                        self.progs_identified_files.append(os.path.abspath(full_path))
                        file_count += 1
            
            self.log_message(f"Total de arquivos (.exe, .dll) encontrados: {file_count}", 'info')
            self.log_message("ETAPA 1 CONCLUÍDA", 'success')
            
            if not self.progs_identified_files:
                self.status_var.set("Etapa 1: Nenhum arquivo encontrado.")
            else:
                self.status_var.set(f"Etapa 1: {file_count} arquivo(s) identificado(s).")

        except Exception as e:
            self.log_message(f"Erro na Etapa 1: {e}", 'error')
            self.status_var.set("Erro na Etapa 1.")
        finally:
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)
            
    def start_etapa2_update(self):
        if not self.progs_identified_files:
            messagebox.showwarning("Aviso", "Execute a Etapa 1 primeiro.")
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
            self.log_message("INICIANDO ETAPA 2 (ANÁLISE)", 'header')
            base_progs_path = Path(self.pasta_progs.get())
            base_atualizacao_path = Path(self.pasta_atualizacao.get())
            
            for progs_file_str in self.progs_identified_files:
                progs_file_path = Path(progs_file_str)
                try:
                    relative_path = progs_file_path.relative_to(base_progs_path)
                except ValueError:
                    self.log_message(f"ERRO INTERNO: {progs_file_path} não está em {base_progs_path}.", "error")
                    continue

                atualizacao_file_path = base_atualizacao_path / relative_path
                
                if not atualizacao_file_path.exists():
                    continue

                mtime_progs = progs_file_path.stat().st_mtime
                mtime_atualizacao = atualizacao_file_path.stat().st_mtime
                
                if mtime_atualizacao > mtime_progs:
                    action_details = {
                        'progs_file_path_str': str(progs_file_path),
                        'atualizacao_file_path_str': str(atualizacao_file_path),
                        'target_dir_str': str(progs_file_path.parent),
                        'original_filename': progs_file_path.name,
                        'base_name': progs_file_path.stem,
                        'extension': progs_file_path.suffix,
                    }
                    self.planned_actions_etapa2.append(action_details)
                    self.log_message(f"-> ATUALIZAÇÃO NECESSÁRIA para '{progs_file_path.name}'.", 'warning')

            if not self.planned_actions_etapa2:
                self.log_message("Nenhum arquivo precisa ser atualizado.", "info")
                self.status_var.set("Etapa 2: Nenhum arquivo para atualizar.")
            else:
                self.log_message(f"Total de arquivos para atualizar: {len(self.planned_actions_etapa2)}", 'critical')
                self.status_var.set("Etapa 2: Análise concluída. Aguardando confirmação.")
                self.root.after(0, self._request_update_confirmation_dialog)

        except Exception as e:
            self.log_message(f"Erro na análise da Etapa 2: {e}", 'error')
            self.status_var.set("Erro na análise da Etapa 2.")
        finally:
            if not self.planned_actions_etapa2:
                self.progress_bar.stop()
                self.set_buttons_state_during_operation(False)

    def _request_update_confirmation_dialog(self):
        num_updates = len(self.planned_actions_etapa2)
        confirm_msg = f"CONFIRMAÇÃO NECESSÁRIA\n\n{num_updates} arquivo(s) serão atualizados.\n\nO processo irá:\n"
        confirm_msg += "1. Remover arquivos antigos (com sufixos de data ou prefixo 'old_').\n"
        if self.backup_var.get():
            confirm_msg += "2. Renomear os arquivos atuais como backup.\n"
            confirm_msg += "3. Copiar os arquivos novos da 'Atualizacao' para 'PROGS'.\n"
        else:
            confirm_msg += "2. Copiar os arquivos novos (SOBRESCREVENDO SEM BACKUP).\n"
        confirm_msg += "\nEsta operação é crítica. Verifique o log. Deseja continuar?"
        
        if messagebox.askyesno("Confirmação Crítica", confirm_msg, icon='warning'):
            self.log_message("CONFIRMAÇÃO DO USUÁRIO: Atualização autorizada.", 'critical')
            execution_thread = threading.Thread(target=self.run_etapa2_execution_phase, daemon=True)
            execution_thread.start()
        else:
            self.log_message("ATUALIZAÇÃO CANCELADA PELO USUÁRIO.", 'warning')
            self.status_var.set("Etapa 2: Atualização cancelada.")
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)

    def run_etapa2_execution_phase(self):
        try:
            self.log_message("INICIANDO ETAPA 2 (EXECUÇÃO)", 'header')
            updated_count = 0
            error_count = 0

            for action in self.planned_actions_etapa2:
                original_filename = action['original_filename']
                target_dir = Path(action['target_dir_str'])
                self.log_message(f"Processando: '{original_filename}' em '{target_dir}'", 'info')
                
                try:
                    # Passo 1: Remover arquivos legados
                    self._remove_legacy_files_step_6_1(target_dir, action['base_name'], action['extension'])

                    # Passo 2: Backup (se habilitado)
                    progs_file_path = Path(action['progs_file_path_str'])
                    if self.backup_var.get() and progs_file_path.exists():
                        self._backup_file_with_date_step_6_2(progs_file_path)

                    # Passo 3: Copiar o novo arquivo
                    atualizacao_file_path = Path(action['atualizacao_file_path_str'])
                    shutil.copy2(str(atualizacao_file_path), str(progs_file_path))
                    self.log_message(f" -> SUCESSO: '{original_filename}' atualizado.", 'success')
                    updated_count += 1

                except Exception as file_op_error:
                    error_count += 1
                    self.log_message(f" -> ERRO AO ATUALIZAR '{original_filename}': {file_op_error}", 'error')
            
            summary_msg = f"Finalizado!\n\n✅ Sucessos: {updated_count}\n❌ Erros: {error_count}"
            self.root.after(0, lambda: messagebox.showinfo("Resumo da Atualização", summary_msg))

        except Exception as e:
            self.log_message(f"Erro crítico na execução da Etapa 2: {e}", 'error')
        finally:
            self.status_var.set(f"Etapa 2: Concluída. {updated_count} atualizado(s), {error_count} erro(s).")
            self.progress_bar.stop()
            self.set_buttons_state_during_operation(False)
            self.planned_actions_etapa2 = []

    def _remove_legacy_files_step_6_1(self, target_dir: Path, base_name: str, extension: str):
        """
        Remove de forma abrangente arquivos legados baseados no nome do arquivo original.
        """
        # Padrão para arquivos com prefixo 'old_', comum em backups manuais.
        prefix_pattern = re.compile(rf"^old_{re.escape(base_name)}.*", re.IGNORECASE)
        
        original_filename_lower = (base_name + extension).lower()
        base_name_lower = base_name.lower()

        for item in target_dir.iterdir():
            # Processa apenas arquivos com a mesma extensão.
            if item.is_file() and item.suffix.lower() == extension.lower():
                item_name_lower = item.name.lower()
                item_stem_lower = item.stem.lower()

                # Pula o arquivo original exato que será atualizado.
                if item_name_lower == original_filename_lower:
                    continue

                should_remove = False
                
                # Condição 1: Verifica o padrão de prefixo "old_".
                if prefix_pattern.match(item.stem):
                    should_remove = True
                
                # Condição 2: Verifica se o nome do arquivo começa com o nome base, mas é mais longo.
                elif item_stem_lower.startswith(base_name_lower) and len(item_stem_lower) > len(base_name_lower):
                    # Pega o caractere logo após o nome base.
                    char_after_basename = item_stem_lower[len(base_name_lower)]
                    # Se não for uma letra, consideramos um arquivo legado (ex: "Nome_123", "Nome - Copia").
                    # Isso evita remover arquivos como "NomeHelper.exe".
                    if not char_after_basename.isalpha():
                        should_remove = True

                if should_remove:
                    try:
                        item.unlink()
                        self.log_message(f"   Removido arquivo legado: {item.name}", 'detail')
                    except Exception as e:
                        self.log_message(f"   ERRO ao remover legado '{item.name}': {e}", 'error')

    def _backup_file_with_date_step_6_2(self, progs_file_path: Path):
        dir, base, ext = progs_file_path.parent, progs_file_path.stem, progs_file_path.suffix
        date_str = datetime.now().strftime('%d%m%Y')
        backup_name = f"{base}{date_str}{ext}"
        backup_path = dir / backup_name
        
        counter = 1
        while backup_path.exists():
            backup_name = f"{base}{date_str}_{counter}{ext}"
            backup_path = dir / backup_name
            counter += 1
        
        try:
            progs_file_path.rename(backup_path)
            self.log_message(f"   Backup criado: '{progs_file_path.name}' -> '{backup_path.name}'", 'detail')
        except Exception as e:
            self.log_message(f"   ERRO ao criar backup para '{progs_file_path.name}': {e}", 'error')
            raise

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    root = tk.Tk()
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception:
        pass
    if os.name == 'nt':
        try:
            ttk.Style().theme_use('vista')
        except tk.TclError:
            pass
    app = AutomatedUpdateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
