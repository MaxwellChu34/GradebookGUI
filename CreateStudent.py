from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Add A New Student:")
root.geometry("825x500")
root.resizable(False, False)

# LETTER ONLY
def validate_letters_and_spaces(input_text):
    return all(char.isalpha() or char.isspace() for char in input_text)
validate_letters_cmd = root.register(validate_letters_and_spaces)
# NUM ONLY
def validate_numbers_and_decimals_only(input_text):
    return input_text == "" or input_text.replace(".", "", 1).isdigit()
validate_numbers_and_decimals_cmd = root.register(validate_numbers_and_decimals_only)

# INSTRUCTION SECTION
labelInstruction = Label(root, text="Please enter in as much as you can according to the new student's current status!", font=("Arial", 18))
labelInstruction.grid(row=0, column=0, columnspan=3, padx=60, pady=10)

# SEPARATOR
separator = ttk.Separator(root, orient="horizontal")
separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

# NAME ENTRY
labelNameStudentLabel = Label(root, text="What is the Student's NAME?:", font=("Arial", 16))
labelNameStudentLabel.grid(row=2, column=0, sticky="w", padx=50, pady=10)
labelNameStudentText = Entry(root, width=40, font=("Arial", 14), validate="key", validatecommand=(validate_letters_cmd, "%P"))
labelNameStudentText.grid(row=3, column=0, sticky="w", padx=50, pady=10)

# ADD BUTTON
def yes_student():
    print("Add")
buttonStudentAdd = Button(root, text="Add", font=("Arial", 20), width=13, command=yes_student)
buttonStudentAdd.grid(row=2, column=1, columnspan=2, sticky="w", pady=10)

# CANCEL BUTTON
def no_student():
    print("Cancel")
buttonStudentAdd = Button(root, text="Cancel", font=("Arial", 20), width=13, command=no_student)
buttonStudentAdd.grid(row=3, column=1, columnspan=2, sticky="w", pady=10)

# SEPARATOR
separator = ttk.Separator(root, orient="horizontal")
separator.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)

# TABLE
studentFrame = Frame(root, width=350, height=250)
studentFrame.grid(row=5, rowspan=4, column=0, sticky="w", padx=50, pady=10)
studentFrame.grid_propagate(False)
sqlTree = ttk.Treeview(studentFrame, show="headings", height=24)
student_vertical_scroll = ttk.Scrollbar(studentFrame, orient="vertical", command=sqlTree.yview)
sqlTree.configure(yscrollcommand=student_vertical_scroll.set)
sqlTree.grid(row=0, column=0, sticky="nsew")
student_vertical_scroll.grid(row=0, column=1, sticky="ns")
studentFrame.columnconfigure(0, weight=1)

# COMPONENT LABEL
labelComponentVarStudent = StringVar()
labelComponentVarStudent.set("Select a Component to start Grading!")
labelComponentsStudentLabel = Label(root, textvariable=labelComponentVarStudent, font=("Arial", 16))
labelComponentsStudentLabel.grid(row=5, column=1, columnspan=2, sticky="w")

# GRADE ENTRY
labelGradeStudentText = Entry(root, width=10, font=("Arial", 14), validate="key", validatecommand=(validate_numbers_and_decimals_cmd, "%P"))
labelGradeStudentText.grid(row=6, column=1, sticky="w")

# APPLY BUTTON
def apply_student():
    print("Apply")
buttonStudentAdd = Button(root, text="Apply", font=("Arial", 16), width=5, command=apply_student)
buttonStudentAdd.grid(row=6, column=2, sticky="w")

# FEEDBACK
labelFeedbackVarStudent = StringVar()
labelFeedbackVarStudent.set("Please get started and I'll help the best I can.")
labelFeedbackStudent = Label(root, textvariable=labelFeedbackVarStudent, font=("Arial", 14), wraplength=225)
labelFeedbackStudent.grid(row=7, column=1, columnspan=2)

# Configure grid to expand columns for separator
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

root.mainloop()