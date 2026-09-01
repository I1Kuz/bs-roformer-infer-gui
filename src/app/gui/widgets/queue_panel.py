import tkinter as tk
from tkinter import ttk
from app.inference.job import Job, JobStatus

class QueuePanel(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Queue", padding=10)
        self.jobs = {}
        
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.tree = ttk.Treeview(self, columns=("File", "Model", "Status", "Progress"), show="headings", height=8)
        self.tree.heading("File", text="File")
        self.tree.heading("Model", text="Model")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Progress", text="Progress")
        
        self.tree.column("File", width=200)
        self.tree.column("Model", width=150)
        self.tree.column("Status", width=150)
        self.tree.column("Progress", width=80)
        
        self.tree.pack(fill="both", expand=True)
        
        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.tree.bind("<Button-3>", self._show_context_menu)
        
    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            job = self.jobs.get(iid)
            if job:
                # Rebuild menu
                self.context_menu.delete(0, "end")
                
                if job.status == JobStatus.PENDING:
                    self.context_menu.add_command(label="Remove", command=self._on_remove)
                    self.context_menu.add_command(label="Process Next", command=self._on_process_next)
                
                if job.status == JobStatus.PROCESSING:
                    self.context_menu.add_command(label="Cancel Transform", command=self._on_cancel_transform)
                    
                if self.context_menu.index("end") is not None:
                    self.context_menu.add_separator()
                    
                self.context_menu.add_command(label="Open File", command=self._on_open_file)
                self.context_menu.add_command(label="Reveal Input", command=self._on_reveal)
                
                if job.status == JobStatus.FINISHED:
                    self.context_menu.add_command(label="Reveal Output", command=self._on_reveal_output)

                self.context_menu.post(event.x_root, event.y_root)
                
    def _on_cancel_transform(self):
        selection = self.tree.selection()
        if not selection: return
        job_id = selection[0]
        if hasattr(self, 'queue_manager') and self.queue_manager:
            if self.queue_manager.current_job and self.queue_manager.current_job.id == job_id:
                self.queue_manager.cancel_current()
                
    def _on_reveal_output(self):
        selection = self.tree.selection()
        if not selection: return
        job = self.jobs.get(selection[0])
        if job:
            import os
            os.startfile(job.output_dir)
                
    def _on_remove(self):
        selection = self.tree.selection()
        if not selection: return
        job_id = selection[0]
        # queue_manager is not passed here, let's call a callback or just fire an event
        # Wait, I need to pass queue_manager into QueuePanel
        if hasattr(self, 'queue_manager') and self.queue_manager:
            self.queue_manager.remove_job(job_id)
        self.tree.delete(job_id)
        del self.jobs[job_id]
        
    def _on_process_next(self):
        selection = self.tree.selection()
        if not selection: return
        job_id = selection[0]
        if hasattr(self, 'queue_manager') and self.queue_manager:
            self.queue_manager.prioritize_job(job_id)
            # Reorder treeview visually
            self.tree.move(job_id, "", 0)
            
    def _on_open_file(self):
        selection = self.tree.selection()
        if not selection: return
        job = self.jobs.get(selection[0])
        if job:
            import os
            os.startfile(job.input_file)
            
    def _on_reveal(self):
        selection = self.tree.selection()
        if not selection: return
        job = self.jobs.get(selection[0])
        if job:
            import subprocess
            subprocess.Popen(f'explorer /select,"{job.input_file}"')

    def update_job(self, job: Job):
        import os
        filename = os.path.basename(job.input_file)
        status_str = job.status_text if job.status_text else job.status.value
        if job.status == JobStatus.FAILED and job.error:
            status_str = f"Failed: {job.error}"
            
        if job.status in (JobStatus.PROCESSING,):
            prog_str = job.progress_str if job.progress_str else f"{int(job.progress * 100)}%"
        else:
            prog_str = ""
        
        if job.id in self.jobs:
            self.tree.item(job.id, values=(
                filename,
                job.model_id,
                status_str,
                prog_str
            ))
        else:
            self.tree.insert("", "end", iid=job.id, values=(
                filename,
                job.model_id,
                status_str,
                prog_str
            ))
            self.jobs[job.id] = job

    def clear_completed(self):
        for job_id, job in list(self.jobs.items()):
            if job.status == JobStatus.COMPLETED:
                self.tree.delete(job_id)
                del self.jobs[job_id]
                
    def clear_all(self):
        for job_id in list(self.jobs.keys()):
            self.tree.delete(job_id)
            del self.jobs[job_id]
