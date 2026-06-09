from tkinter import *
from tkinter import ttk
import string

root = Tk()
root.title("Create A New Course:")
root.geometry("850x600")
root.resizable(False, False)

# INSTRUCTION SECTION
labelInstruction = Label(root, text="Please enter in everything, be sure the weights total to 100%, and have grade scale values be logical!", font=("Arial", 18))
labelInstruction.grid(row=0, column=0, columnspan=3, padx=20, pady=10)

# SEPARATOR
separator = ttk.Separator(root, orient="horizontal")
separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

# NO NUM
def validate_letters_only(input_text):
    allowed_chars = string.ascii_letters + string.punctuation + " "
    return all(char in allowed_chars for char in input_text)
validate_letter_cmd = root.register(validate_letters_only)
# LETTERS AND NUM ONLY
def validate_letters_and_numbers(input_text):
    allowed_chars = string.ascii_letters + string.digits
    return all(char in allowed_chars for char in input_text)
validate_letters_and_numbers_cmd = root.register(validate_letters_and_numbers)
# NUM ONLY
def validate_numbers_only(input_text):
    return input_text.isdigit()
validate_number_cmd = root.register(validate_numbers_only)

# COURSE NAME
courseNameLabel = Label(root, text="What is the course NAME?", font=("Arial", 16))
courseNameLabel.grid(row=2, column=0, padx=5, pady=5)
courseNameText = Entry(root, font=("Arial", 14), validate="key", validatecommand=(validate_letter_cmd, "%S"))
courseNameText.grid(row=2, column=1, padx=5, pady=5)
# COURSE NUMBER
courseNumLabel = Label(root, text="What is the course NUMBER?", font=("Arial", 16))
courseNumLabel.grid(row=3, column=0, padx=5, pady=5)
courseNumText = Entry(root, font=("Arial", 14), validate="key", validatecommand=(validate_letters_and_numbers_cmd, "%S"))
courseNumText.grid(row=3, column=1, padx=5, pady=5)
# COURSE SECTION
courseSecLabel = Label(root, text="What is the course SECTION?", font=("Arial", 16))
courseSecLabel.grid(row=4, column=0, padx=5, pady=5)
courseSecText = Entry(root, font=("Arial", 14), validate="key",  validatecommand=(validate_number_cmd, "%S"))
courseSecText.grid(row=4, column=1, padx=5, pady=5)
# STUDENT COUNT
courseStudentLabel = Label(root, text="How many STUDENTS are there?", font=("Arial", 16))
courseStudentLabel.grid(row=5, column=0, padx=5, pady=5)
courseStudentText = Entry(root, font=("Arial", 14), validate="key",  validatecommand=(validate_number_cmd, "%S"))
courseStudentText.grid(row=5, column=1, padx=5, pady=5)

# ACCEPT BUTTON
def accept_new_course():
    global i
    course_name = courseNameText.get().strip()
    course_number = courseNumText.get().strip()
    course_section = courseSecText.get().strip()
    student_count = courseStudentText.get().strip()
    if not course_name:
        labelFeedbackVarCreate.set("Accept Error: Course name cannot be empty.")
        return
    if not course_number:
        labelFeedbackVarCreate.set("Accept Error: Course number cannot be empty.")
        return
    if not course_section:
        labelFeedbackVarCreate.set("Accept Error: Course section cannot be empty.")
        return
    course_section = course_number.lstrip('0') or '0'
    if not student_count:
        labelFeedbackVarCreate.set("Accept Error: Student count cannot be empty.")
        return
    student_count = student_count.lstrip('0') or '0'
    total_weight = 0
    for child in tree.get_children():
        component_weight = tree.item(child)["values"][1]
        total_weight += int(component_weight)
    if total_weight != 100:
        labelFeedbackVarCreate.set("Accept Error: The total weight of components must equal 100%.")
        return
    grade_scale_values = []
    for i, entry in enumerate(grade_entries):
        grade_value = entry.get().strip()
        if not grade_value:
            labelFeedbackVarCreate.set(f"Accept Error: '{grade_ranges[i]}' does not have a value.")
            return
        if not grade_value.isdigit():
            labelFeedbackVarCreate.set(f"Accept Error: '{grade_ranges[i]}' must be a valid number.")
            return
        grade_value_int = int(grade_value)
        if i == 0 and grade_value_int > 100:
            labelFeedbackVarCreate.set(f"Accept Error: '{grade_ranges[i]}' cannot be greater than 100.")
            return
        grade_scale_values.append(grade_value_int)
    for i in range(3):
        if grade_scale_values[i] <= grade_scale_values[i + 1]:
            labelFeedbackVarCreate.set(
                f"Accept Error: '{grade_ranges[i]}' must be greater than '{grade_ranges[i + 1]}'.")
            return
    if grade_scale_values[3] != grade_scale_values[4]:
        labelFeedbackVarCreate.set("Accept Error: 'D >=' must equal 'F <'.")
        return
    course_data = {
        "name": course_name,
        "number": course_number,
        "section": course_section,
        "student_count": student_count,
        "components": [],
        "grade_scale": {grade_ranges[i]: grade_scale_values[i] for i in range(5)}
    }
    for child in tree.get_children():
        component_name = tree.item(child)["values"][0]
        component_weight = tree.item(child)["values"][1]
        course_data["components"].append({
            "component_name": component_name,
            "component_weight": component_weight
        })
    print(f"Course '{course_name}' created successfully!")
    print(course_data)
    labelFeedbackVarCreate.set(f"Course '{course_name}' created successfully!")
    courseNameText.delete(0, END)
    courseNumText.delete(0, END)
    courseSecText.delete(0, END)
    courseStudentText.delete(0, END)
    for child in tree.get_children():
        tree.delete(child)
    courseSelectedEntry.config(state="normal")
    courseSelectedEntry.delete(0, END)
    courseSelectedEntry.config(state="readonly")
    labelFeedbackVarCreate.set("Please get started and I'll help the best I can.")
buttonCourseNewAccept = Button(root, text="Accept", font=("Arial", 16), width=5, height=2, command=accept_new_course)
buttonCourseNewAccept.grid(row=2, rowspan=2, column=2, padx=5, pady=10)

# CANCEL BUTTON
def cancel_new_course():
    print("Cancelled")
buttonCourseNewCancel = Button(root, text="Cancel", font=("Arial", 16), width=5, height=2, command=cancel_new_course)
buttonCourseNewCancel.grid(row=4, rowspan=2, column=2, padx=5, pady=10)

# SEPARATOR
separator = ttk.Separator(root, orient="horizontal")
separator.grid(row=6, column=0, columnspan=3, sticky="ew", pady=10)

# COMPONENTS LABEL
componentsMainLabel = Label(root, text="Class Components:", font=("Arial", 18))
componentsMainLabel.grid(row=7, column=0)
# FRAME
table_frame = Frame(root)
table_frame.grid(row=8, column=0, columnspan=1, padx=10, pady=10, sticky="nsew")
# COMPONENTS & WEIGHT TABLE
def on_row_select(event):
    selected_item = tree.selection()
    if selected_item:
        item_values = tree.item(selected_item[0], "values")
        if item_values:
            selected_text = f"{item_values[0]} ({item_values[1]}%)"
            courseSelectedEntry.config(state="normal")
            courseSelectedEntry.delete(0, END)
            courseSelectedEntry.insert(0, selected_text)
            courseSelectedEntry.config(state="readonly")
tree = ttk.Treeview(table_frame, columns=("Component", "Weight"), show="headings", height=8)
tree.pack(side=LEFT, fill=BOTH, expand=True)
tree.heading("Component", text="Component Name")
tree.heading("Weight", text="Weight (%)")
tree.column("Component", width=200, anchor="center")
tree.column("Weight", width=100, anchor="center")
tree.bind("<ButtonRelease-1>", on_row_select)
# SCROLLBAR
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side=RIGHT, fill=Y)
tree.configure(yscrollcommand=scrollbar.set)

# ADD SECTION FRAME
add_section_frame = Frame(root)
add_section_frame.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
# NEW COMPONENT ENTRY
courseComponentAddLabel = Label(add_section_frame, text="Enter Class Component (Name):", font=("Arial", 12))
courseComponentAddLabel.grid(row=0, column=0, padx=5, pady=5, sticky="w")
courseComponentAddEntry = Entry(add_section_frame, font=("Arial", 10))
courseComponentAddEntry.grid(row=0, column=1, padx=5, pady=5)
# NEW WEIGHT ENTRY
courseWeightAddLabel = Label(add_section_frame, text="Enter Respective Weight (1-100):", font=("Arial", 12))
courseWeightAddLabel.grid(row=1, column=0, padx=5, pady=5, sticky="w")
courseWeightAddEntry = Entry(add_section_frame, font=("Arial", 10), validate="key", validatecommand=(validate_number_cmd, "%S"))
courseWeightAddEntry.grid(row=1, column=1, padx=5, pady=5)
# SELECTED COMPONENT/WEIGHT VIEW
courseSelectedLabel = Label(add_section_frame, text="Selected Component From Table:", font=("Arial", 12))
courseSelectedLabel.grid(row=2, column=0, padx=5, pady=5, sticky="w")
courseSelectedEntry = Entry(add_section_frame, font=("Arial", 10), state="readonly")
courseSelectedEntry.grid(row=2, column=1, padx=5, pady=5)

# ADD BUTTON
def add_component():
    component_name = courseComponentAddEntry.get().strip()
    component_weight = courseWeightAddEntry.get().strip()
    component_weight = component_weight.lstrip('0') or '0'
    if not component_name:
        labelFeedbackVarCreate.set("Add Error: Component name cannot be empty.")
        return
    if not component_weight.isdigit() or not (1 <= int(component_weight) <= 100):
        labelFeedbackVarCreate.set("Add Error: Weight must be a number between 1 and 100.")
        return
    existing_components = [tree.item(child)["values"][0] for child in tree.get_children()]
    if component_name in existing_components:
        labelFeedbackVarCreate.set(f"Add Error: Component name '{component_name}' already exists.")
        return
    tree.insert("", "end", values=(component_name, component_weight))
    labelFeedbackVarCreate.set(f"Successfully added component '{component_name}' with weight {component_weight}%.")
    courseComponentAddEntry.delete(0, END)
    courseWeightAddEntry.delete(0, END)
add_component_button = Button(add_section_frame, text="Add", font=("Arial", 12), width=4, height=2, command=add_component)
add_component_button.grid(row=0, column=2)
# CHANGE BUTTON
def change_component():
    selected_item = tree.selection()
    if not selected_item:
        labelFeedbackVarCreate.set("Change Error: No component selected to change.")
        return
    new_component_name = courseComponentAddEntry.get().strip()
    new_component_weight = courseWeightAddEntry.get().strip()
    new_component_weight = new_component_weight.lstrip('0') or '0'
    if not new_component_name:
        labelFeedbackVarCreate.set("Change Error: Component name cannot be empty.")
        return
    if not new_component_weight.isdigit() or not (1 <= int(new_component_weight) <= 100):
        labelFeedbackVarCreate.set("Change Error: Weight must be a number between 1 and 100.")
        return
    existing_components = [tree.item(child)["values"][0] for child in tree.get_children()]
    current_item_values = tree.item(selected_item[0], "values")
    if new_component_name in existing_components and new_component_name != current_item_values[0]:
        labelFeedbackVarCreate.set(f"Change Error: Component name '{new_component_name}' already exists.")
        return
    tree.item(selected_item[0], values=(new_component_name, new_component_weight))
    labelFeedbackVarCreate.set(f"Successfully changed to '{new_component_name}' with weight {new_component_weight}%.")
    courseComponentAddEntry.delete(0, END)
    courseWeightAddEntry.delete(0, END)
    courseSelectedEntry.config(state="normal")
    courseSelectedEntry.delete(0, END)
    courseSelectedEntry.config(state="readonly")
change_component_button = Button(add_section_frame, text="Change", font=("Arial", 12), width=4, height=2, command=change_component)
change_component_button.grid(row=1, column=2)
# DELETE BUTTON
def delete_component():
    selected_item = tree.selection()
    if not selected_item:
        labelFeedbackVarCreate.set("Delete Error: No component selected to delete.")
        return
    tree.delete(selected_item[0])
    courseSelectedEntry.delete(0, END)
    labelFeedbackVarCreate.set("Successfully deleted the selected component.")
    courseSelectedEntry.config(state="normal")
    courseSelectedEntry.delete(0, END)
    courseSelectedEntry.config(state="readonly")
delete_component_button = Button(add_section_frame, text="Delete", font=("Arial", 12), width=4, height=2, command=delete_component)
delete_component_button.grid(row=2, column=2)

# GRADE LABEL
gradeLabel = Label(root, text="Grade Scale:", font=("Arial", 18))
gradeLabel.grid(row=7, column=1)
# GRADE ENTRY FRAME "TABLE"
grade_frame = Frame(root)
grade_frame.grid(row=8, column=1, padx=5, pady=5, sticky="e")
grade_ranges = ["A >=", "B >=", "C >=", "D >=", "F <"]
grade_entries = []
for i, grade_range in enumerate(grade_ranges):
    grade_label_widget = Label(grade_frame, text=grade_range, font=("Arial", 16))
    grade_label_widget.grid(row=i, column=0, padx=5, pady=2)
    grade_entry_widget = Entry(grade_frame, font=("Arial", 14), width=5, validate="key", validatecommand=(validate_number_cmd, "%S"))
    grade_entry_widget.grid(row=i, column=1, padx=5, pady=2)
    grade_entries.append(grade_entry_widget)

#FEEDBACK SECTION
labelFeedbackVarCreate = StringVar()
labelFeedbackVarCreate.set("Please get started and I'll help the best I can.")
labelFeedbackCreate = Label(root, textvariable=labelFeedbackVarCreate, font=("Arial", 14), anchor="e")
labelFeedbackCreate.grid(row=9, column=1, columnspan=2)

# Configure grid to expand columns for separator
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)

root.mainloop()