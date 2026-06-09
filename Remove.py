from tkinter import *

root = Tk()
root.title("Remove a Course:")
root.geometry("925x275")
root.resizable(False, False)

labelQuestion = Label(root, text="Are you sure you would like to delete the following course and all of its information:\n\n This course", font=("Arial", 24), anchor="center")
labelQuestion.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

def cancel_remove():
    print("Pfft")

def accept_remove():
    print("Fart")


buttonCancelRemove = Button(root, text="Cancel", font=("Arial", 25), width=10, height=3, command=cancel_remove)
buttonCancelRemove.grid(row=1, column=0, padx=10, pady=40)

buttonAcceptRemove = Button(root, text="Do it", font=("Arial", 25), width=10, height=3, command=accept_remove)
buttonAcceptRemove.grid(row=1, column=1, padx=10, pady=40)

root.mainloop()