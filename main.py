from game import Game
import os

try:
    import tkinter.messagebox as tk_msg
    import tkinter.ttk as ttk
    import tkinter as tk
except ImportError:
    tk_msg = tk = ttk = None

if 'LD_DEVEL' in os.environ:
    tk_msg = tk = None


RESOLUTIONS = [
    (1024, 600),
    (1024, 768),
    (1200, 900),
    (1280, 720),
    (1280, 1024),
    (1366, 768),
    (1920, 1080),
    (2560, 1440),
]


def get_res():
    if tk is None:
        return 1280, 720, 0, 0

    yay = False
    res = 1280, 720

    root = tk.Tk()
    root.withdraw()
    root.title('Brink')
    root.iconbitmap('assets/icon.ico')
    root.resizable(False, False)
    frame = tk.Frame()

    tk.Label(frame, text='Select screen resolution:').grid(row=0, column=1, columnspan=2)

    def update_btn(x):
        nonlocal res

        def f():
            nonlocal res
            res = x
            btn.config(text='{}x{}'.format(*x))
        return f

    popup = tk.Menu(frame, tearoff=0)
    for i in RESOLUTIONS:
        popup.add_command(label='{}x{}'.format(*i), command=update_btn(i))

    btn = ttk.Button(frame, text='{}x{}'.format(*res))
    btn.grid(row=1, column=1, columnspan=2, sticky='EW')

    def btn_popup(event):
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            popup.grab_release()
    btn.bind("<Button-1>", btn_popup)

    def cont():
        nonlocal yay
        root.destroy()
        yay = True

    radio = tk.IntVar()
    f1 = tk.Frame(frame)
    ttk.Radiobutton(f1, variable=radio, value=0).grid(row=0, column=0, sticky=tk.E)
    tk.Label(f1, text='Windowed', justify=tk.LEFT).grid(row=0, column=1, sticky=tk.W)
    f1.grid(row=2, column=1)
    f2 = tk.Frame(frame)
    ttk.Radiobutton(f2, variable=radio, value=1).grid(row=0, column=0, sticky=tk.E)
    tk.Label(f2, text='Fullscreen', justify=tk.LEFT).grid(row=0, column=1, sticky=tk.W)
    f2.grid(row=2, column=2)

    dif_radio = tk.IntVar()
    f1 = tk.Frame(frame)
    ttk.Radiobutton(f1, variable=dif_radio, value=0).grid(row=0, column=0, sticky=tk.E)
    tk.Label(f1, text='Normal', justify=tk.LEFT).grid(row=0, column=1, sticky=tk.W)
    f1.grid(row=3, column=1)
    f2 = tk.Frame(frame)
    ttk.Radiobutton(f2, variable=dif_radio, value=1).grid(row=0, column=0, sticky=tk.E)
    tk.Label(f2, text='No Mobs', justify=tk.LEFT).grid(row=0, column=1, sticky=tk.W)
    f2.grid(row=3, column=2)

    ttk.Button(frame, text='Continue', command=cont).grid(row=4, column=1)
    ttk.Button(frame, text='Exit', command=root.destroy).grid(row=4, column=2)

    img = tk.PhotoImage(file='assets/icon128.png')
    tk.Label(frame, image=img).grid(row=0, column=0, rowspan=frame.grid_size()[1])
    root.img = img

    PAD = 5
    col_count, row_count = frame.grid_size()
    for col in range(col_count):
        frame.grid_columnconfigure(col, pad=PAD)
    for row in range(row_count):
        frame.grid_rowconfigure(row, pad=PAD)

    frame.pack(padx=PAD, pady=PAD)
    root.deiconify()
    root.lift()
    root.mainloop()

    if not yay:
        return None, None, None, None
    return (*res, radio.get(), dif_radio.get())


# noinspection PyBroadException
def main():
    try:
        w, h, f, d = get_res()
    except Exception:
        w, h, f, d = 0, 0, 1, 0

    if w is None or h is None:
        return

    try:
        Game(w, h, f, d).mainloop()
    except Exception:
        import traceback
        traceback.print_exc()

        if tk_msg is not None:
            try:
                import pygame
                pygame.quit()
            except Exception:
                pass

            tk.Tk().withdraw()
            msg = 'Something went wrong.\nPlease report this along with the following traceback:\n\n'
            tk_msg.showerror('Error', msg + traceback.format_exc())

        exit(1)


if __name__ == '__main__':
    main()
