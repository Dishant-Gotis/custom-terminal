import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import subprocess
import os
import threading
import queue

class CustomTerminal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dishant's Custom Terminal")
        self.root.geometry("900x600")
        
        # Command history
        self.command_history = []
        self.history_index = 0
        
        # Output queue for thread-safe updates
        self.output_queue = queue.Queue()
        
        self.setup_gui()
        self.update_output()
        
        # Set initial working directory
        self.current_dir = os.getcwd()
        self.update_prompt()
        
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Output area
        self.output_text = ScrolledText(
            main_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 11), 
            bg="black", 
            fg="lime",
            insertbackground="lime"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Input frame
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Prompt label
        self.prompt_label = tk.Label(
            input_frame, 
            font=("Consolas", 11), 
            bg="black", 
            fg="lime"
        )
        self.prompt_label.pack(side=tk.LEFT)
        
        # Command entry
        self.entry = tk.Entry(
            input_frame, 
            font=("Consolas", 11), 
            bg="black", 
            fg="white", 
            insertbackground="white"
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Bind events
        self.entry.bind("<Return>", self.run_command)
        self.entry.bind("<Up>", self.history_up)
        self.entry.bind("<Down>", self.history_down)
        self.entry.bind("<Tab>", self.tab_completion)
        
        self.entry.focus()
        
    def update_prompt(self):
        """Update the prompt to show current directory"""
        try:
            # Get relative path if possible
            home = os.path.expanduser("~")
            if self.current_dir.startswith(home):
                display_dir = "~" + self.current_dir[len(home):]
            else:
                display_dir = self.current_dir
                
            self.prompt_label.config(text=f"{display_dir}> ")
        except:
            self.prompt_label.config(text="> ")
    
    def add_to_history(self, command):
        """Add command to history"""
        if command.strip() and (not self.command_history or command != self.command_history[-1]):
            self.command_history.append(command)
        self.history_index = len(self.command_history)
    
    def history_up(self, event):
        """Navigate up in command history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])
        return "break"
    
    def history_down(self, event):
        """Navigate down in command history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
        return "break"
    
    def tab_completion(self, event):
        """Basic tab completion for files and directories"""
        current_text = self.entry.get()
        if not current_text.strip():
            return "break"
            
        # Get the word being completed
        words = current_text.split()
        if not words:
            return "break"
            
        last_word = words[-1]
        dir_path = os.path.dirname(last_word) if os.path.dirname(last_word) else "."
        base_name = os.path.basename(last_word)
        
        try:
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.startswith(base_name)]
                if len(files) == 1:
                    # Complete the word
                    new_word = files[0]
                    if os.path.isdir(os.path.join(dir_path, new_word)):
                        new_word += "/"
                    
                    words[-1] = os.path.join(dir_path, new_word) if dir_path != "." else new_word
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, " ".join(words))
                elif len(files) > 1:
                    # Show possibilities
                    self.output_text.insert(tk.END, "\n" + " ".join(files) + "\n")
                    self.output_text.see(tk.END)
        except:
            pass
            
        return "break"
    
    def run_command(self, event=None):
        """Execute the command"""
        command = self.entry.get().strip()
        if not command:
            return
            
        # Add to history
        self.add_to_history(command)
        
        # Clear entry
        self.entry.delete(0, tk.END)
        
        # Display command
        self.output_text.insert(tk.END, f"{self.prompt_label.cget('text')}{command}\n")
        self.output_text.see(tk.END)
        
        # Handle special commands
        if command.lower() == "exit":
            self.root.destroy()
            return
        elif command.lower() == "clear":
            self.output_text.delete(1.0, tk.END)
            return
        elif command.startswith("cd "):
            self.handle_cd(command)
            return
        
        # Run command in separate thread
        threading.Thread(target=self.execute_command, args=(command,), daemon=True).start()
    
    def handle_cd(self, command):
        """Handle cd command to change directory"""
        try:
            new_dir = command[3:].strip()
            if new_dir == "~":
                new_dir = os.path.expanduser("~")
            elif new_dir == "-":
                # Go back to previous directory
                if hasattr(self, 'previous_dir'):
                    new_dir = self.previous_dir
                else:
                    self.output_text.insert(tk.END, "No previous directory\n")
                    return
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(self.current_dir, new_dir)
            
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.previous_dir = self.current_dir
                self.current_dir = os.path.abspath(new_dir)
                os.chdir(self.current_dir)
                self.update_prompt()
            else:
                self.output_text.insert(tk.END, f"Directory not found: {new_dir}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error changing directory: {e}\n")
        
        self.output_text.see(tk.END)
    
    def execute_command(self, command):
        """Execute command in separate thread"""
        try:
            # Set up environment
            env = os.environ.copy()
            
            # Run command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.current_dir,
                env=env
            )
            
            # Read output in real-time
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.output_queue.put(line)
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code != 0:
                self.output_queue.put(f"\nProcess exited with code {return_code}\n")
                
        except Exception as e:
            self.output_queue.put(f"Error: {e}\n")
    
    def update_output(self):
        """Update output from queue (called periodically)"""
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(100, self.update_output)
    
    def run(self):
        """Start the terminal"""
        self.root.mainloop()

if __name__ == "__main__":
    terminal = CustomTerminal()
    terminal.run()
