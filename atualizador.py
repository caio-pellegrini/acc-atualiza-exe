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

        # --- State Management ---
        self.ignore_list = []
        self.identified_files = []
        self.planned_actions = []
        
        # --- Paths ---
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.log_file_path = os.path.join(application_path, "log.txt")
        
        self.pasta_atualizacao = tk.StringVar(value="Atualizacao")
        self.pasta_progs = tk.StringVar(value="C:\\PROGS")
        
        # --- UI Setup ---
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
        top_frame = ttk.Frame(self.root, padding=(10,5))
        top_frame.pack(fill='x', side='top')
        
        title_label = ttk.Label(top_frame, text="Sistema de Atualização Automatizado de Arquivos (.exe, .dll)", style='Title.TLabel')
        title_label.pack(pady=(5, 10))

        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

        left_pane = ttk.Frame(content_frame, style='TFrame')
        left_pane.pack(side='left', fill='both', expand=True, padx=(0, 5))

        right_pane = ttk.Frame(content_frame, style='TFrame')
        right_pane.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
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

        ignore_frame = ttk.LabelFrame(left_pane, text="Pastas a Ignorar", padding="10")
        ignore_frame.pack(fill='x', pady=(0, 10), anchor='n')
        
        ttk.Label(ignore_frame, text="Pastas listadas aqui não serão analisadas nem atualizadas.", style='Instruction.TLabel').pack(anchor='w', pady=(0,5))
        
        listbox_frame = ttk.Frame(ignore_frame)
        listbox_frame.pack(fill='x', expand=True)

        self.ignore_listbox = tk.Listbox(listbox_frame, height=3, font=('Segoe UI', 9), selectmode=tk.EXTENDED)
        self.ignore_listbox.pack(side='left', fill='x', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.ignore_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.ignore_listbox.config(yscrollcommand=scrollbar.set)
        
        ignore_buttons_frame = ttk.Frame(ignore_frame)
        ignore_buttons_frame.pack(fill='x', pady=(5,0))
        
        btn_add_ignore = ttk.Button(ignore_buttons_frame, text="Adicionar", style='Small.TButton', command=self.add_ignore_folder)
        btn_add_ignore.pack(side='left', expand=True, fill='x', padx=(0,2))
        
        btn_remove_ignore = ttk.Button(ignore_buttons_frame, text="Remover", style='Small.TButton', command=self.remove_ignore_folder)
        btn_remove_ignore.pack(side='left', expand=True, fill='x', padx=(2,0))
        
        options_frame = ttk.LabelFrame(left_pane, text="Opções de Atualização", padding="10")
        options_frame.pack(fill='x', pady=(0, 10), anchor='n')
        
        self.backup_var = tk.BooleanVar(value=True)
        self.create_backup_check = ttk.Checkbutton(options_frame, text="Backup antes de sobrescrever arquivos", variable=self.backup_var)
        self.create_backup_check.pack(anchor='w', pady=(0,2))
        ttk.Label(options_frame, text="Renomeia o arquivo atual em PROGS para 'arquivoDDMMAAAA' antes de copiar o novo.", style='Instruction.TLabel').pack(anchor='w', padx=(20,0), pady=(0,5))

        action_buttons_frame = ttk.LabelFrame(left_pane, text="Fluxo de Execução Controlado", padding="10")
        action_buttons_frame.pack(fill='both', expand=True, pady=(0, 10), anchor='n')

        self.btn_step1 = ttk.Button(action_buttons_frame, text="Etapa 1 - Identificar Arquivos", style='Main.TButton', command=self.start_step1_identification)
        self.btn_step1.pack(fill='x', pady=5)
        
        self.btn_step2 = ttk.Button(action_buttons_frame, text="Etapa 2 - Comparar Arquivos", style='Main.TButton', command=self.start_step2_comparison, state='disabled')
        self.btn_step2.pack(fill='x', pady=5)

        self.btn_step3 = ttk.Button(action_buttons_frame, text="Etapa 3 - Executar Atualização", style='Critical.TButton', command=self.start_step3_execution, state='disabled')
        self.btn_step3.pack(fill='x', pady=5)

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
        if not folder: return

        normalized_folder = os.path.normpath(folder)
        var.set(normalized_folder)
        self.log_message(f"Pasta '{folder_name}' definida para: {normalized_folder}", 'info')
        
        if folder_name == "Atualização":
            progs_path = os.path.normpath(self.pasta_progs.get())
            if os.path.commonpath([progs_path, normalized_folder]) == progs_path and normalized_folder not in self.ignore_list:
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

    def remove_ignore_folder(self):
        selected_indices = self.ignore_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Nenhuma Seleção", "Por favor, selecione uma pasta para remover.")
            return
        for index in sorted(selected_indices, reverse=True):
            self.ignore_list.pop(index)
        self.update_ignore_listbox()

    def update_ignore_listbox(self):
        self.ignore_listbox.delete(0, tk.END)
        for folder in sorted(self.ignore_list):
            self.ignore_listbox.insert(tk.END, folder)

    def log_message(self, message, tag='info'):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        full_message_for_gui = f"[{timestamp}] {message.replace(os.linesep, f'{os.linesep}[{timestamp}] ')}\n"
        self.log_text.insert(tk.END, full_message_for_gui, tag)
        self.log_text.see(tk.END)
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f_log:
                f_log.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"[{timestamp}] !!! CRITICAL: Falha ao escrever no arquivo de log: {e} !!!\n", 'error')
        self.root.update_idletasks()

    def clear_log(self):
        if messagebox.askyesno("Limpar Log", "Tem certeza que deseja limpar o log na tela?"):
            self.log_text.delete(1.0, tk.END)
            self.log_message("Log da tela limpo pelo usuário.", "info")

    def validate_paths(self):
        if not all(os.path.exists(p) for p in [self.pasta_progs.get(), self.pasta_atualizacao.get()]):
            messagebox.showerror("Erro de Validação", "Um ou mais caminhos de pasta são inválidos.")
            return False
        return True

    def toggle_ui_state(self, is_operating):
        state = 'disabled' if is_operating else 'normal'
        self.btn_step1.config(state=state)
        # Sequencialmente habilita os botões
        self.btn_step2.config(state='disabled' if is_operating or not self.identified_files else 'normal')
        self.btn_step3.config(state='disabled' if is_operating or not self.planned_actions else 'normal')
        
        for child in (self.root.winfo_children()):
             if isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Button, ttk.Entry, tk.Listbox, ttk.Checkbutton)) and widget not in [self.btn_step1, self.btn_step2, self.btn_step3, self.btn_finalize]:
                        widget.config(state=state)

    # --- ETAPA 1: IDENTIFICATION ---
    def start_step1_identification(self):
        if not self.validate_paths(): return
        self.identified_files.clear()
        self.planned_actions.clear()
        self.toggle_ui_state(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 1: Identificando arquivos em PROGS...")
        threading.Thread(target=self._run_step1_identification, daemon=True).start()

    def _run_step1_identification(self):
        try:
            self.log_message("--- INICIANDO ETAPA 1: IDENTIFICAÇÃO DE ARQUIVOS ---", 'header')
            path_progs_str = os.path.normpath(self.pasta_progs.get())
            normalized_ignore_list = [os.path.normpath(p) for p in self.ignore_list]
            
            for root, dirs, files in os.walk(path_progs_str, topdown=True):
                if any(os.path.normpath(root).startswith(p) for p in normalized_ignore_list):
                    dirs[:] = []
                    continue
                for filename in files:
                    if filename.lower().endswith(('.exe', '.dll')):
                        self.identified_files.append(os.path.join(root, filename))
            
            self.log_message(f"Etapa 1 concluída. Total de arquivos encontrados: {len(self.identified_files)}", 'success')
            self.status_var.set(f"Etapa 1 concluída. {len(self.identified_files)} arquivo(s) pronto(s) para comparação.")
        except Exception as e:
            self.log_message(f"Erro na Etapa 1: {e}", 'error')
            self.status_var.set("Erro na Etapa 1.")
        finally:
            self.progress_bar.stop()
            self.toggle_ui_state(False)

    # --- ETAPA 2: COMPARISON ---
    def start_step2_comparison(self):
        if not self.identified_files:
            messagebox.showwarning("Aviso", "Execute a Etapa 1 primeiro.")
            return
        self.planned_actions.clear()
        self.toggle_ui_state(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 2: Comparando arquivos...")
        threading.Thread(target=self._run_step2_comparison, daemon=True).start()

    def _run_step2_comparison(self):
        try:
            self.log_message("--- INICIANDO ETAPA 2: COMPARAÇÃO DE ARQUIVOS ---", 'header')
            base_progs = Path(self.pasta_progs.get())
            base_atualizacao = Path(self.pasta_atualizacao.get())
            
            for file_str in self.identified_files:
                progs_path = Path(file_str)
                try:
                    relative_path = progs_path.relative_to(base_progs)
                    atualizacao_path = base_atualizacao / relative_path
                    if atualizacao_path.exists() and atualizacao_path.stat().st_mtime > progs_path.stat().st_mtime:
                        self.planned_actions.append({'source': str(atualizacao_path), 'dest': str(progs_path)})
                        self.log_message(f"-> Planejada atualização para: {progs_path.name}", 'warning')
                except ValueError:
                    self.log_message(f"ERRO: {progs_path} não está em {base_progs}.", "error")

            if not self.planned_actions:
                self.log_message("Etapa 2 concluída. Nenhum arquivo precisa ser atualizado.", 'success')
                self.status_var.set("Etapa 2 concluída. Nenhum arquivo para atualizar.")
            else:
                self.log_message(f"Etapa 2 concluída. Total de arquivos para atualizar: {len(self.planned_actions)}", 'success')
                self.status_var.set(f"Etapa 2 concluída. {len(self.planned_actions)} arquivo(s) pronto(s) para atualização.")
        except Exception as e:
            self.log_message(f"Erro na Etapa 2: {e}", 'error')
            self.status_var.set("Erro na Etapa 2.")
        finally:
            self.progress_bar.stop()
            self.toggle_ui_state(False)

    # --- ETAPA 3: EXECUTION ---
    def start_step3_execution(self):
        if not self.planned_actions:
            messagebox.showwarning("Aviso", "Nenhuma atualização planejada. Execute a Etapa 2 primeiro.")
            return

        confirm_msg = f"{len(self.planned_actions)} arquivo(s) serão atualizados.\nEsta operação é crítica e modifica arquivos.\n\nDeseja continuar?"
        if not messagebox.askyesno("Confirmação Crítica", confirm_msg, icon='warning'):
            self.log_message("Atualização cancelada pelo usuário.", 'warning')
            return
            
        self.toggle_ui_state(True)
        self.progress_bar.start()
        self.status_var.set("Etapa 3: Executando atualizações...")
        threading.Thread(target=self._run_step3_execution, daemon=True).start()

    def _run_step3_execution(self):
        self.log_message("--- INICIANDO ETAPA 3: EXECUÇÃO DA ATUALIZAÇÃO ---", 'header')
        updated_count, error_count = 0, 0
        
        for action in self.planned_actions:
            dest_path = Path(action['dest'])
            source_path = Path(action['source'])
            
            try:
                self.log_message(f"Processando: '{dest_path.name}'", 'info')
                self._remove_legacy_files(dest_path.parent, dest_path.stem, dest_path.suffix)
                if self.backup_var.get() and dest_path.exists():
                    self._backup_current_file(dest_path)
                shutil.copy2(str(source_path), str(dest_path))
                self.log_message(f" -> SUCESSO: '{dest_path.name}' atualizado.", 'success')
                updated_count += 1
            except Exception as e:
                self.log_message(f" -> ERRO AO ATUALIZAR '{dest_path.name}': {e}", 'error')
                error_count += 1
        
        summary_msg = f"Processo finalizado!\n\n✅ Sucessos: {updated_count}\n❌ Erros: {error_count}"
        self.log_message(summary_msg, 'success' if error_count == 0 else 'warning')
        self.status_var.set(f"Etapa 3 concluída. Sucessos: {updated_count}, Erros: {error_count}")
        self.root.after(0, lambda: messagebox.showinfo("Resumo da Atualização", summary_msg))
        
        self.progress_bar.stop()
        self.planned_actions.clear() # Limpa as ações após execução
        self.toggle_ui_state(False)

    def _remove_legacy_files(self, target_dir: Path, base_name: str, extension: str):
        prefix_pattern = re.compile(rf"^old_{re.escape(base_name)}.*", re.IGNORECASE)
        original_filename_lower = (base_name + extension).lower()
        base_name_lower = base_name.lower()

        for item in target_dir.iterdir():
            if item.is_file() and item.suffix.lower() == extension.lower():
                if item.name.lower() == original_filename_lower: continue

                should_remove = False
                if prefix_pattern.match(item.stem):
                    should_remove = True
                elif item.stem.lower().startswith(base_name_lower) and len(item.stem) > len(base_name):
                    if not item.stem[len(base_name)].isalpha():
                        should_remove = True

                if should_remove:
                    try:
                        item.unlink()
                        self.log_message(f"   Removido arquivo legado: {item.name}", 'detail')
                    except Exception as e:
                        self.log_message(f"   ERRO ao remover legado '{item.name}': {e}", 'error')

    def _backup_current_file(self, file_path: Path):
        date_str = datetime.now().strftime('%d%m%Y')
        backup_name = f"{file_path.stem}{date_str}{file_path.suffix}"
        backup_path = file_path.parent / backup_name
        
        counter = 1
        while backup_path.exists():
            backup_name = f"{file_path.stem}{date_str}_{counter}{file_path.suffix}"
            backup_path = file_path.parent / backup_name
            counter += 1
        
        try:
            file_path.rename(backup_path)
            self.log_message(f"   Backup criado: '{file_path.name}' -> '{backup_path.name}'", 'detail')
        except Exception as e:
            self.log_message(f"   ERRO ao criar backup para '{file_path.name}': {e}", 'error')
            raise

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    root = tk.Tk()
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    except Exception: pass
    if os.name == 'nt':
        try: ttk.Style().theme_use('vista')
        except tk.TclError: pass
    app = AutomatedUpdateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
