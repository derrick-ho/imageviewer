import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fd
import tkinter.messagebox
import os
import PIL.Image as pi
import PIL.ImageTk as itk
import math
import imghdr # For image check
import csv # To cache file directory
import configparser
import zipfile
import io

# TODO: Config file
#       Scrolling
#      Save settings to config on close

class Window(tk.Tk):
    def __init__(self, *args, **kwargs):
        #=================== Primary Window ===================#
        tk.Tk.__init__(self, *args, **kwargs)

        #self.__dir = ''
        
        self.wm_title("Image Viewer")

        try:
            path = os.path.dirname(os.path.realpath(__file__))
            self.wm_iconbitmap(path+"\\Books.ico") 
        except:
            print("No bitmap found. Using default.")
            pass

        self.minsize(400,600)

        self._read_config()

        self.show_side = True

        # Window Starting Location
        screenX = ((self.winfo_screenwidth() / 2) - (self.__width / 2))
        screenY = (self.winfo_screenheight() / 2) - (self.__height / 2)

        self.geometry('%dx%d+%d+%d' % (self.__width,
                                       self.__height,
                                       screenX,
                                       screenY))

        #======================== Menu ========================#
        self.__menu_bar = tk.Menu(self)
        self.__fileMenu = tk.Menu(self.__menu_bar, tearoff=0)
        self.__helpMenu = tk.Menu(self.__menu_bar, tearoff=0)

        # To open a already existing file
        self.__fileMenu.add_command(label="Open",
                                        command=self.openFile)

        # To create a line in the dialog        
        self.__fileMenu.add_separator()                                         
        self.__fileMenu.add_command(label="Exit",
                                        command=self.__quit_app)
        self.__menu_bar.add_cascade(label="File",
                                       menu=self.__fileMenu)
      
        # To create a feature of description of the notepad
        self.__helpMenu.add_command(label="About Image Viewer",
                                        command=self.__about) 
        self.__menu_bar.add_cascade(label="Help",
                                       menu=self.__helpMenu)
  
        self.config(menu=self.__menu_bar)

        #====================== Frames ========================#
        self.container = tk.Frame(self, height=self.__height, width=self.__width)
        self.container.pack(side="top", fill="both", expand=True)

        # Create a Dictionary of Frames
        self.frames = {}
        
        # Slideshow
        for F in (MainPage, Library):
            frame = F(self.container, self)

            # the windows class acts as the root window for the frames.
            self.frames[F] = frame
            frame.grid(row=0, column=1, sticky="nsew")

        # Configure Side Panel
        panel = SidePanel(self.container, self, self.__dir)
        panel.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.frames[SidePanel] = panel

        nav = NavigationBar(self.container, self)
        nav.grid(row=1, column=1, sticky="sew")
        self.frames[NavigationBar] = nav

        # Allocate Frames
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, minsize=200, weight = 0)
        self.container.grid_columnconfigure(1, weight=4)
        self.container.grid_rowconfigure(1, weight=0)

        # Switch to Main Frame
        self.show_frame(MainPage)
        self.focus_set()

    def _read_config(self):
        path = os.path.dirname(os.path.realpath(__file__))
        cp = configparser.ConfigParser()

        cp.read(path+'\\config.ini')

        if 'General' in cp:
            self.__width = int(cp.get('General', 'width'))
            self.__height = int(cp.get('General', 'height'))
            self.__dir = cp.get('General', 'home_dir')

            if not os.path.isdir(self.__dir):
                print("Invalid file")


        else:
            cp.add_section('General')
            cp['General']['width'] = '1500'
            cp['General']['height'] = '1000'

            self.__dir = fd.askdirectory(title="Choose a home directory.")
            cp.set('General', 'home_dir', self.__dir)

            fp=open(path+'\\config.ini', 'w')
            cp.write(fp)
            fp.close()
            
    def set_config(self):
        path = os.path.dirname(os.path.realpath(__file__))
        cp = configparser.ConfigParser()
        cp['DEFAULT'] = {'width' : '1500',
                         'height' : '1000',
                         'home_dir' : ''}
        
        fp=open(path+'\\config.ini', 'w')
        cp.write(fp)
        fp.close()

    # raises Frame cont to the top
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    # Show/Hide a frame (currently just used for sidebar)
    def toggle_frame(self, cont):
        if self.show_side:
            self.container.grid_columnconfigure(0, minsize=0)
            self.frames[cont].grid_remove()
        else:
            self.frames[cont].grid()

        self.show_side = not self.show_side
          
    def __quit_app(self):
        self.__root.destroy()
        #TODO: Save config file
  
    def __about(self):
        tk.messagebox.showinfo("Image Viewer","Derrick")

    # Open File and Display image in MainPage
    def openFile(self, file_name=None):
        if not file_name:
            file_name = tk.filedialog.askopenfilename(defaultextension=".jpg",
                                               filetypes=[("All Files","*.*"),
                                                        ("JPG files","*.jpg"),
                                                        ("PNG files","*.png")])
        if bool(file_name):
            self.title(os.path.basename(file_name))
            self.frames[MainPage].display_file(file_name)

    # Open File and Display image in MainPage
    def open_folder(self, folder=None):
        if not folder:
            folder = tk.filedialog.askdirectory(defaultextension=".jpg",
                                               filetypes=[("All Files","*.*"),
                                                        ("JPG files","*.jpg"),
                                                        ("PNG files","*.png")])

        if bool(folder):
            self.title(folder)

            if '.' not in folder:
                contents = []
                for f_name in os.listdir(folder):
                    if f_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                        contents.append(folder+'\\'+ f_name)
                    # print(f_name)

                self.frames[MainPage].display_folder(contents)
            else:
                self.frames[MainPage].display_folder(folder)


    def change_mode(self):
        self.frames[MainPage].change_mode()

    def dual_pages(self):
        self.frames[MainPage].dual_pages()

    def next(self):
        self.frames[MainPage].next()

    def prev(self):
        self.frames[MainPage].prev()

# Displays the image
class MainPage(tk.Frame):
    image = None
    original = None
    folder = []
    images = []
    cur_page = 0
    total_pages = 1

    # 0 = fit to screen ; 1 = fit to width ; 2 = fit to height
    cur_mode = 0 # Fit to screen on default
    two_page = False

    def __init__(self, parent, controller, color='black'):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Main Page")
        label.pack(padx=10, pady=10)

        self.display = tk.Canvas(self, bd=0, bg=color, highlightthickness=0)
        self.display.pack(fill=tk.BOTH, expand=1)

        self.bind("<Configure>", self.__fit_to_screen)
        self.bind("<Left>", self.prev)
        self.bind("<Right>", self.next)

        
        switch_window_button = tk.Button(
            self,
            text="Go to the Side Page",
            command=lambda: controller.show_frame(Library),
        )

        switch_window_button.pack(side="bottom", fill=tk.X)

    def change_mode(self, mode=None):
        self.cur_mode = mode if mode else (self.cur_mode + 1) % 3
        if self.image:
            self.__resize_image(self.winfo_width(), self.winfo_height())

    def dual_pages(self):
        self.two_page = not self.two_page

    # Used when displaying from folder/file
    def display_file(self, file_name):
        if bool(file_name):
            img_file = pi.open(file_name)
            self.image = itk.PhotoImage(img_file)
            self.original = img_file
            self.__resize_image(self.winfo_width(), self.winfo_height())
            self.focus()

    # Used when displaying directly from zip
    def display_image(self, img):
        if bool(img):
            self.image = itk.PhotoImage(img)
            self.original = img
            self.__resize_image(self.winfo_width(), self.winfo_height())
            self.focus()

    def display_folder(self, folder):
        if bool(folder):
            self.folder = folder
            self.cur_page = 0
    
            if isinstance(folder, str):
                self.images = []
                zippedImgs = zipfile.ZipFile(folder, 'r')
                zip_len = len(zippedImgs.namelist())

                for file_in_zip in zippedImgs.namelist():
                    # print("iter", i, " ", file_in_zip) # Iterates and prints out all zipped files
                    
                    if (file_in_zip.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))):
                        try:
                            data = zippedImgs.read(file_in_zip)
                            dataEnc = io.BytesIO(data)
                            img = pi.open(dataEnc)
                            self.images.append(img)
                            self.display_image(img)
                        except:
                            print("Image Broken")
                            pass

                self.display_image(self.images[0])

                self.total_pages = zip_len

            else:
                self.total_pages = len(folder)

                self.display_file(folder[0])

    def __fit_to_screen(self, event):
        # If currently displaying an image
        if self.original:
            self.__resize_image(event.width, event.height)

    # Resize image to fit screen
    def __resize_image(self, w, h):
        size = (w, h)
        img_size = self.original.size

        fit_width = size[0] / img_size[0]
        fit_height = size[1] / img_size[1]

        if self.cur_mode == 0:
            ratio = min(fit_width, fit_height)
        elif self.cur_mode == 1:
            ratio = fit_width
        else:
            ratio = fit_height

        img_size = tuple(math.ceil(ratio*dim) for dim in img_size)
        
        # Just using the fastest method for resizing
        resized = self.original.resize(img_size, pi.NEAREST)

        self.image = itk.PhotoImage(resized)
        self.display.delete("IMG")
        self.display.create_image(size[0]/2, img_size[1]/2, image=self.image, tags="IMG") #, anchor='nw'

    def next(self, event=None):
        if self.cur_page < self.total_pages - 1:
            self.cur_page += 1
            
            if "." in self.folder:
                self.display_image(self.images[self.cur_page])
            else:
                self.display_file(self.folder[self.cur_page])

    def prev(self, event=None):
        if self.cur_page > 0:
            self.cur_page -= 1

            if "." in self.folder:
                self.display_image(self.images[self.cur_page])
            else:
                self.display_file(self.folder[self.cur_page])

# Shows File Directory and Sends selected folder to be opened
class SidePanel(tk.Frame):
    def __init__(self, parent, controller, start):
        tk.Frame.__init__(self, parent, bg='gray', width=100)
        label = tk.Label(self, text="Library", bg='gray')
        label.pack(padx=10, pady=5)

        # Display Directory
        self.lib = ttk.Treeview(self, show='tree', selectmode='browse')

        # Generate Scroll Bar
        ybar = tk.Scrollbar(self, orient=tk.VERTICAL,
                  command=self.lib.yview)   

        self.lib.configure(yscroll=ybar.set)
        self.directory = start
        self.__cont = controller

        path = os.path.abspath(self.directory)
        self.node = self.lib.insert('','end',text=path,open=True)

        # Generate directory tree
        self.__traverse_dir(self.node, path)

        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lib.pack(fill=tk.Y, expand=True)

        self.lib.bind('<<TreeviewSelect>>', self.__selected)

        change_dir_button = tk.Button(
            self,
            text="Change Directory",
            command=lambda: self.new_dir(),
        )
        change_dir_button.pack(side="bottom", fill=tk.X)

    # Populate TreeView
    def __traverse_dir(self, parent, path, lvl=0):
        for d in os.listdir(path):
            full_path=os.path.join(path,d)
            isdir = os.path.isdir(full_path)

            # Display only images and folders
            #if isdir or d.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            iid=self.lib.insert(parent,'end',text=d,open=False)
            
            # Prevent diving too deep into directory
            if isdir and lvl < 5:
                try:
                    self.__traverse_dir(iid,full_path, lvl+1)
                except:
                    print(full_path, " failed to load.")
                    pass

    # Automatically open image when file is selected
    def __selected(self, event):
        sel_id = self.lib.selection()
        file_loc = self.lib.item(sel_id, 'text')

        parent_node = self.lib.parent(sel_id)
        while (parent_node != ''):
            parent_loc = self.lib.item(parent_node, 'text')
            file_loc= os.path.join(parent_loc, file_loc)
            parent_node = self.lib.parent(parent_node)

        try:
            # Open image
            self.__cont.openFile(file_loc)
        except:
            self.__cont.open_folder(file_loc)
            pass

    def new_dir(self):
        new_loc = fd.askdirectory(title="Select a root folder.")
            
        if new_loc:
            # Delete old treeview
            self.lib.delete(*self.lib.get_children())

            path = os.path.abspath(new_loc)
            self.node = self.lib.insert('','end',text=path,open=True)

            self.__traverse_dir(self.node, path)

# Sets of buttons that changes state through controller
class NavigationBar(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, height=50)
        label = tk.Label(self, text="Navigation Buttons Here")
        label.pack(padx=10, pady=10)

        switch_window_button = ttk.Button(
            self, text="Toggle Sidebar", command=lambda: controller.toggle_frame(SidePanel)
        )
        switch_window_button.pack(side="bottom", fill=tk.X)
        
        last_folder = ttk.Button(self, text="<<", width = 5)
        last_folder.pack(side='left', expand = True)
        
        last_page = ttk.Button(self, text="<", width = 5, command=controller.prev)
        last_page.pack(side='left', expand = True)

        multipage = ttk.Button(self, text="[]", width = 5, command=controller.change_mode)
        multipage.pack(side='left', expand = True)

        multipage = ttk.Button(self, text="//", width = 5, command=controller.dual_pages)
        multipage.pack(side='left', expand = True)

        next_page = ttk.Button(self, text=">", width = 5, command=controller.next)
        next_page.pack(side='left', expand = True)
        
        next_folder = ttk.Button(self, text=">>", width = 5)
        next_folder.pack(side='left', expand = True)

class Library(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Alt Page")
        label.pack(padx=10, pady=10)

        switch_window_button = tk.Button(
            self,
            text="Back to Main Screen",
            command=lambda: controller.show_frame(MainPage),
        )
        switch_window_button.pack(side="bottom", fill=tk.X)

if __name__ == "__main__":
    Window().mainloop()