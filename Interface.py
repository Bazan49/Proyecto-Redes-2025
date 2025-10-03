import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import LinkLayer
from MessageType import MessageType 
from Frame_Manager import FrameManager
import threading
import os
from datetime import datetime

# Clase encargada de la interfaz visual del proyecto 
class AlternativeInterface:
    def __init__(self, interface):
        # Cosas visuales
        self.username = None
        self.ask_username()
        if not self.username:
            return
        self.window = tk.Tk()
        self.window.title("Link-Chat")
        self.window.geometry('700x500')
        self.bg_color = "#f0f0f0"
        self.window.configure(bg=self.bg_color)
        self.setup_main_interface()

        # Contactos (Amigos): Diccionario local sólo en memoria
        self.dic_usuarios = {"todos": "ff:ff:ff:ff:ff:ff"}

        # Inicializaciones app
        self.interface = interface
        self.link_layer = None
        self.stop_event = None
        self.local_mac = self.link_layer.get_Mac(self.interface)
        app.start()

    def ask_username(self):
        root = tk.Tk()
        root.withdraw()
        while True:
            username = simpledialog.askstring("Nombre de usuario", "Por favor, ingrese su nombre de usuario:", parent=root)
            if username is None:
                break
            username = username.strip()
            if username:
                self.username = username
                break
            messagebox.showwarning("Campo requerido", "Debe ingresar un nombre de usuario válido.", parent=root)
        root.destroy()

    def setup_main_interface(self):
        tk.Label(self.window, text=f"Hola {self.username}!", bg=self.bg_color, font=("Arial", 12, "italic")).pack(anchor='nw', padx=10, pady=5)

        controls_frame = tk.Frame(self.window, bg=self.bg_color)
        controls_frame.pack(anchor='nw', padx=10, pady=5, fill='x')

        self.search_friends_button = tk.Button(controls_frame, text="Buscar Amigos", command=self.search_friends)
        self.search_friends_button.pack(side='left')

        self.add_friend_button = tk.Button(controls_frame, text="Añadir Amigo", command=self.add_friend)
        self.add_friend_button.pack(side='left', padx=(10, 0))

        self.selected_user = tk.StringVar(value=list(self.dic_usuarios.keys())[0])
        tk.Label(controls_frame, text="Enviar a:", bg=self.bg_color).pack(side='left', padx=(20,5))
        self.user_optionmenu = tk.OptionMenu(controls_frame, self.selected_user, *self.dic_usuarios.keys())
        self.user_optionmenu.pack(side='left', padx=10)

        # self.users = ["Todos", "Usuario1", "Usuario2", "Usuario3"]
        # self.selected_user = tk.StringVar(value=self.users[0])
        # tk.Label(controls_frame, text="Enviar a:", bg=self.bg_color).pack(side='left', padx=(20,5))
        # self.user_optionmenu = tk.OptionMenu(controls_frame, self.selected_user, *self.users)
        # self.user_optionmenu.pack(side='left')

        self.chat_canvas = tk.Canvas(self.window, bg="white")
        self.chat_canvas.pack(padx=10, pady=10, fill='both', expand=True)

        self.scrollbar = tk.Scrollbar(self.window, orient="vertical", command=self.chat_canvas.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.chat_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.chat_frame = tk.Frame(self.chat_canvas, bg="white")
        self.chat_canvas.create_window((0,0), window=self.chat_frame, anchor='nw')
        self.chat_frame.bind("<Configure>", self.on_frame_configure)

        bottom_frame = tk.Frame(self.window, bg=self.bg_color)
        bottom_frame.pack(side='bottom', fill='x', padx=10, pady=(0,10))
        self.entry = tk.Entry(bottom_frame)
        self.entry.pack(side='left', fill='x', expand=True)

        self.filepath = None
        self.file_button = tk.Button(bottom_frame, text="Seleccionar Archivo", command=self.select_file)
        self.file_button.pack(side='left', padx=(10,5))

        self.send_button = tk.Button(bottom_frame, text="Enviar", command=self.send_message)
        self.send_button.pack(side='left', padx=(5,10))
        self.entry.bind('<Return>', self.enter_key_pressed)

    def on_frame_configure(self, event):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)

    def add_message_bubble(self, sender, destinatario, message, is_own):
        bubble_frame = tk.Frame(self.chat_frame, bg="white")
        bg_color = "#dcf8c6" if is_own else "#ffffff"
        bubble = tk.Frame(
            bubble_frame,
            bg=bg_color,
            bd=1,
            relief="raised",
            padx=10,
            pady=5
        )
        
        label_text = f"{sender} a {destinatario}:\n{message}"
        label = tk.Label(bubble, text=label_text, bg=bg_color, justify='left', wraplength=300)
        label.pack()

        if is_own:
            bubble_frame.pack(anchor='w', pady=5, padx=10)
            bubble.pack(anchor='w')
        else:
            bubble_frame.pack(anchor='e', pady=5, padx=10)
            bubble.pack(anchor='e')

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def send_message(self):
        username = self.username
        message = self.entry.get().strip()
        destinatario = self.dic_usuarios[self.selected_user.get()]
        if not message and not self.filepath:
            messagebox.showwarning("Campo requerido", "Ingrese un mensaje o seleccione un archivo para enviar.", parent=self.window)
            return
        
        frame_list = None

        if message:
            self.add_message_bubble(username, destinatario, f"{message}", is_own=True)
            frame_list = FrameManager.CreateFrame(destinatario, self.local_mac, MessageType.TEXT, message) 

        if self.filepath:
            self.add_message_bubble(username, destinatario, f"[Archivo] {self.filepath}", is_own=True)
            # frame_list = self.frame_manager.CreateFrame(destinatario, self.local_mac, MessageType.FILE, )
            # self.filepath = None

        if frame_list: #se envia el frame
            self.link_layer.send_frame(frame_list) 
            self.entry.delete(0, tk.END)

    def poll_incoming(self):
        # Revisar si hay frames en la cola
        while not self.link_layer.incoming_queue.empty():
            decoded_frame = self.link_layer.incoming_queue.get()

            if(decoded_frame.Type == MessageType.TEXT):
                # Mostrar en la GUI como mensaje recibido
                self.add_message_bubble("Amigo", self.username, decoded_frame.payload, is_own=False)

            elif(decoded_frame.Type == MessageType.FILE):
                # Guardar el archivo
                self.receive_and_save_file(decoded_frame.payload, decoded_frame.FileName, decoded_frame.src_mac) 

            elif(decoded_frame.Type == MessageType.FRIEND_REQUEST):
                # Mostrar solicitud de amistad
                self.show_friend_request(decoded_frame.payload, decoded_frame.src_mac)

            elif(decoded_frame.Type == MessageType.FRIEND_ANSWER):
                # Mostrar aviso de que la solicitud fue aceptada
                self.show_friend_acceptance(decoded_frame.payload, decoded_frame.src_mac)

        # Programar que se vuelva a ejecutar
        self.window.after(1000, self.poll_incoming)

    # TRABAJO CON SOLICITUDES Y AGREGO DE AMISTAD:

    # Agregar un amigo desde la interfaz grafica
    def add_friend(self):
        name = simpledialog.askstring("Nuevo amigo", "Ingrese el nombre del amigo:", parent=self.window)
        if not name:
            return
        mac = simpledialog.askstring("MAC de amigo", f"Ingrese la MAC de {name}:", parent=self.window)
        if not mac:
            return

        self.add_new_friend(name, mac)
        
    def add_new_friend(self, name, mac):
        if mac not in self.dic_usuarios.values():
            unic_name = self.generate_unic_name(name, self.dic_usuarios)
            self.dic_usuarios[unic_name] = mac
            self.update_user_optionmenu()
            messagebox.showinfo("Éxito", f"Amigo {name} agregado correctamente.")
        else:
            messagebox.showwarning("Error", f"Ya es amigo de {name}.")
        
    def generate_unic_name(self, base, dic):
        if base not in dic:
            return base
        i = 1
        while f"{base}{i}" in dic:
            i += 1
        return f"{base}{i}"

    # Método para actualizar OptionMenu
    def update_user_optionmenu(self):
        menu = self.user_optionmenu['menu']
        menu.delete(0, 'end')
        for user in self.dic_usuarios.keys():
            menu.add_command(label=user, command=lambda value=user: self.selected_user.set(value))

    def show_friend_request(self, src_name, src_mac):
        # Mostrar un cuadro de diálogo preguntando si aceptar la solicitud
        answer = messagebox.askyesno(
            "Solicitud de amistad",
            f"{src_name} te ha enviado una solicitud de amistad. ¿Deseas aceptarla?",
            parent=self.window
        )
        if answer:
            # Si acepta, enviar un frame de FRIEND_ANSWER
            self.accept_friend_request(src_name, src_mac)

    def accept_friend_request(self, src_name, src_mac):
        # Crear un frame de FRIEND_ANSWER y enviarlo
        self.add_new_friend(src_name, src_mac)
        frame = FrameManager.CreateFrame(src_mac, self.local_mac, MessageType.FRIEND_ANSWER, self.username)
        self.link_layer.send_frame(frame)

    def show_friend_acceptance(self, src_name, src_mac):
        self.add_new_friend(src_name, src_mac)
        # Mostrar un mensaje de que la solicitud fue aceptada
        messagebox.showinfo(
            "Solicitud aceptada",
            f"{src_name} ha aceptado tu solicitud de amistad. Ahora está en tu lista de amigos.",
            parent=self.window
        )

    def search_friends(self):
        frame = FrameManager.CreateFrame(self.dic_usuarios["todos"], self.local_mac, MessageType.FRIEND_REQUEST, self.username) #crear frame de solicitud de amistad
        self.link_layer.send_frame(frame)
        # Notificar que fue enviada una solicitud
        messagebox.showinfo("Solicitud enviada", "Has enviado una solicitud de amistad a todos los usuarios de la red.", parent=self.window)

    # TRABAJO CON ARCHIVOS

    def select_file(self):
        filepath = filedialog.askopenfilename(parent=self.window)
        if filepath:
            self.filepath = filepath
            messagebox.showinfo("Archivo seleccionado", f"Archivo seleccionado:\n{filepath}", parent=self.window)

    # # Método para recibir y guardar archivos
    # def receive_and_save_file(self, file_data, filename, sender):
    #     try:
    #         # Crear carpeta de descargas si no existe
    #         downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "LinkChat_Files")
    #         if not os.path.exists(downloads_folder):
    #             os.makedirs(downloads_folder)
            
    #         # Si el archivo ya existe, agregar timestamp
    #         base_name, extension = os.path.splitext(filename)
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
    #         # Crear nombre único para el archivo
    #         unique_filename = f"{base_name}_{timestamp}{extension}"
    #         file_path = os.path.join(downloads_folder, unique_filename)
            
    #         # Guardar el archivo
    #         with open(file_path, 'wb') as file:
    #             file.write(file_data)

    #         # Mostrar mensaje en el chat
    #         self.add_message_bubble(sender, self.username, f"[Archivo recibido] {filename}", is_own=False)
            
    #         return True
            
    #     except Exception as e:
    #         print(f"Error al guardar archivo: {e}")
    #         messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}", parent=self.window)
    #         return False

    # OTROS

    def on_closing(self):
        self.stop_event.set() #Indica que los hilos deben parar
        if self.link_layer:
            self.link_layer.close()
        self.window.destroy()

    def enter_key_pressed(self, event):
        self.send_message()

    def start_threads(self):
        # Crear hilo de recepción
        self.receive_thread = threading.Thread(
            target=self.link_layer.receive_thread,
            args=(self.stop_event),
            daemon=True
        )
        self.receive_thread.start()

    def start(self):
        if self.username:
            self.link_layer = LinkLayer.LinkLayer(self.interface)
            self.stop_event = threading.Event()

            # Iniciar hilo de recepción
            self.receive_thread = threading.Thread(
                target=self.link_layer.receive_thread,
                args=(self.stop_event,),
                daemon=True
            )

            self.receive_thread.start()

            # Iniciar polling de mensajes
            self.poll_incoming()

            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.window.mainloop()


if __name__ == "__main__":
    app = AlternativeInterface("anp0s3")

