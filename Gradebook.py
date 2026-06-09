from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont
import sqlite3
import string
import statistics
import os

root = Tk()
root.title("Final Project 'Grade Book' by JMJM Consulting")
root.geometry("1275x700")
root.resizable(False, False)

database_file = "Records.sqlite3"
if not os.path.exists(database_file):
    print("File Error: Database file not found.")
    quit()
conn = sqlite3.connect(database_file)
cur = conn.cursor()
print(f"Connected to {database_file} successfully.")

# GENERAL FUNCTIONS
# LETTER ONLY
def validate_letters_and_spaces(input_text):
    return all(char.isalpha() or char.isspace() for char in input_text)
validate_letters_cmd = root.register(validate_letters_and_spaces)
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
# INCLUDE DECIMALS
def validate_numbers_and_decimals_only(input_text):
    return input_text == "" or input_text.replace(".", "", 1).isdigit()
validate_numbers_and_decimals_cmd = root.register(validate_numbers_and_decimals_only)

# CALC FUNCTIONS
def calculate_final_grade(student_data, metadata, final_scores, grades):
    student_name = student_data[0]
    try:
        scores = [100 if score is None else score for score in student_data[1:]]
        weighted_sum = sum(score * weight / 100 for score, weight in zip(scores, metadata["component_weights"]))
        grade_scale = sorted(map(float, metadata["grade_scale"]), reverse=True)
        for idx, threshold in enumerate(grade_scale):
            if weighted_sum >= threshold:
                final_grade = chr(65 + idx)
                final_scores.append(weighted_sum)
                grades.append(final_grade)
                break
        else:
            final_grade = "F"
        update_fail_table(student_name, final_grade)
        return final_grade
    except Exception as e:
        print(f"Error calculating grade for {student_name}: {e}")
        return "Error"

def update_none_values(course_name):
    global conn, cur
    table_name = course_name.replace(" ", "_").replace(".", "").replace("-", "_")
    try:
        with sqlite3.connect(database_file) as conn:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info('{table_name}');")
            columns_info = cur.fetchall()
            column_names = [col[1] for col in columns_info]
            if 'Student' not in column_names or 'MetaData' not in column_names:
                raise ValueError(f"Columns 'Student' or 'MetaData' not found in table '{table_name}'.")
            start_index = column_names.index('Student') + 1
            end_index = column_names.index('MetaData')
            columns_to_update = column_names[start_index:end_index]
            for column in columns_to_update:
                cur.execute(f"""
                    UPDATE "{table_name}"
                    SET "{column}" = 100
                    WHERE "{column}" IS NULL 
                    AND "Student" NOT LIKE '_Meta_%';
                """)
            conn.commit()
            for column in columns_to_update:
                cur.execute(f"""
                    SELECT COUNT(*)
                    FROM "{table_name}"
                    WHERE "{column}" IS NULL 
                    AND "Student" NOT LIKE '_Meta_%';
                """)
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def update_stats_table(scores, grades):
    try:
        valid_scores = [score for score in scores if 0 <= score <= 100]
        mean = round(statistics.mean(valid_scores), 2)
        median = round(statistics.median(valid_scores), 2)
        std_dev = round(statistics.stdev(valid_scores), 2) if len(valid_scores) > 1 else 0.0
        mode = statistics.mode(grades) if grades else "N/A"
        stats = {"Mean": mean, "Median": median, "Mode": mode, "Std. Dev.": std_dev}
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        stats = {"Mean": "N/A", "Median": "N/A", "Mode": "N/A", "Std. Dev.": "N/A"}
    for item in statsTree.get_children():
        statsTree.delete(item)
    statsTree.insert("", "end", values=(stats["Mean"], stats["Median"], stats["Mode"], stats["Std. Dev."]))

def update_fail_table(student_name, final_grade):
    existing_rows = {row_id: failTree.item(row_id, "values") for row_id in failTree.get_children()}
    if final_grade == "D":
        for row_id, values in existing_rows.items():
            if values[0] == "":
                updated_values = (student_name, values[1])
                failTree.item(row_id, values=updated_values)
                return
        failTree.insert("", "end", values=(student_name, ""))
    elif final_grade == "F":
        for row_id, values in existing_rows.items():
            if values[1] == "":
                updated_values = (values[0], student_name)
                failTree.item(row_id, values=updated_values)
                return
        failTree.insert("", "end", values=("", student_name))

# SQL TABLE FUNCTIONS
def create_table(data):
    global conn, students
    section = f"{int(data['section']):02d}"
    course_title = f"{data['name']}:{data['number']}_{section}"
    table_name = course_title.replace(" ", "_").replace(".", "").replace("-", "_")
    with sqlite3.connect(database_file) as conn:
        conn.execute("PRAGMA busy_timeout = 5000")
        columns = ", ".join([f"'{c['component_name']}' REAL" for c in data['components']])
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" (Student TEXT PRIMARY KEY, {columns}, MetaData REAL, "Final Grade" TEXT)')
        students = [(f"Student {i}",) for i in range(1, int(data['student_count']) + 1)]
        conn.executemany(f'INSERT OR IGNORE INTO "{table_name}" (Student) VALUES (?)', students)
        grade_thresholds = list(data['grade_scale'].values())
        weights = [c['component_weight'] for c in data['components']]
        grade_and_weights = grade_thresholds + weights
        for i, value in enumerate(grade_and_weights):
            conn.executemany(f"INSERT OR IGNORE INTO '{table_name}' (Student, MetaData) VALUES (?, ?)", [(f"_Meta_{i}", value) for i, value in enumerate(grade_and_weights)])
    display_table(table_name)
    update_dropdown_courses()

def edit_table(new_data, current_data_name):
    global conn, cur
    section = f"{int(new_data['section']):02d}"
    course_title = f"{new_data['name']}:{new_data['number']}_{section}"
    table_name = course_title.replace(" ", "_").replace(".", "").replace("-", "_")
    grade_scale = new_data.get("grade_scale", {})
    components = new_data.get("components", [])
    component_names = [component['component_name'] for component in components]
    columns_definition = 'Student TEXT PRIMARY KEY, ' + ', '.join(
        [f'"{name}" REAL' for name in component_names]) + ', MetaData TEXT'
    create_table_query = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {columns_definition}
        );
    '''
    with sqlite3.connect(database_file, timeout=5) as conn:
        conn.execute("PRAGMA busy_timeout = 5000")
        cur = conn.cursor()
        # GET STUDENT NAMES from the old table
        cur.execute(f'''
                    SELECT "Student"
                    FROM "{current_data_name}"
                    WHERE "Student" NOT LIKE "_Meta_%";
                ''')
        student_names = [row[0] for row in cur.fetchall()]
        # GET IDENTICAL COLUMN DATA (component scores)
        cur.execute(f'PRAGMA table_info("{current_data_name}");')
        columns = cur.fetchall()
        column_names = [column[1] for column in columns]
        try:
            start_index = column_names.index('Student') + 1
            end_index = column_names.index('MetaData')
        except ValueError as e:
            raise ValueError(
                f"Expected columns 'Student' or 'MetaData' not found in table '{current_data_name}'"
            ) from e
        selected_columns = column_names[start_index:end_index]
        common_columns = [col for col in selected_columns if col in component_names]
        if common_columns:
            quoted_common_columns = [f'"{col}"' for col in common_columns]
            columns_to_select = ", ".join(quoted_common_columns)
            query = f'''
                   SELECT "Student", {columns_to_select}
                   FROM "{current_data_name}"
                   WHERE "Student" NOT LIKE "_Meta_%";
               '''
            cur.execute(query)
            rows = cur.fetchall()
            column_data = {col: [] for col in common_columns}
            for row in rows:
                for idx, col in enumerate(common_columns):
                    column_data[col].append(row[idx + 1])
        cur.execute(f'DROP TABLE IF EXISTS "{current_data_name}";')
        cur.execute(create_table_query)
        for student in student_names:
            cur.execute(f'''
                INSERT INTO "{table_name}" (Student, MetaData)
                VALUES (?, ?);
            ''', (student, None))
        for student in student_names:
            for col in common_columns:
                for value in column_data[col]:
                    cur.execute(f'''
                        UPDATE "{table_name}"
                        SET "{col}" = ?
                        WHERE "Student" = ?;
                    ''', (value, student))
        grade_thresholds = list(grade_scale.values())
        for i, value in enumerate(grade_thresholds):
            cur.execute(f'''
                INSERT OR REPLACE INTO "{table_name}" (Student, MetaData)
                VALUES (?, ?);
            ''', (f"_Meta_{i}", value))
        component_weights = [component['component_weight'] for component in components]
        for i, weight in enumerate(component_weights):
            cur.execute(f'''
                INSERT OR REPLACE INTO "{table_name}" (Student, MetaData)
                VALUES (?, ?);
            ''', (f"_Meta_{len(grade_thresholds) + i}", weight))
        conn.commit()
    display_table(table_name)
    update_dropdown_courses()

def initialize_table():
    if course_dropdown['values']:
        course_dropdown.set(course_dropdown['values'][0])
        initial = course_dropdown.get()
        display_table(initial)
    else:
        print("No values in dropdown.")

def display_table(course_name):
    global conn, cur
    for row in sqlTree.get_children():
        sqlTree.delete(row)
    table_name = course_name.replace(" ", "_").replace(".", "").replace("-", "_")
    sqlTree.delete(*sqlTree.get_children())
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    try:
        metadata = fetch_table_metadata(table_name, conn)
        if not metadata:
            labelFeedbackVarMain.set(f"Metadata not found for table '{course_name}'.")
            return
        cur.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cur.fetchall()
        all_columns = [info[1] for info in columns_info]
        visible_columns = [col for col in all_columns if col != "MetaData" and col != "Final Grade"]
        visible_columns.append("Final Grade")
        sqlTree["columns"] = visible_columns
        font = tkfont.Font()
        column_widths = {col: font.measure(col) + 20 for col in visible_columns}
        cur.execute(f"SELECT {', '.join([f'\"{col}\"' for col in visible_columns if col != 'Final Grade'])} "
                    f"FROM '{table_name}' WHERE Student NOT LIKE '_Meta_%' "
                    f"ORDER BY CAST(SUBSTR(Student, INSTR(Student, ' ') + 1) AS INTEGER);")
        rows = cur.fetchall()
        update_none_values(table_name)
        rows_with_grades = []
        failTree.delete(*failTree.get_children())
        statsTree.delete(*statsTree.get_children())
        final_scores = []
        final_grades = []
        for row in rows:
            final_grade = calculate_final_grade(row, metadata, final_scores, final_grades)
            rows_with_grades.append(tuple(row) + (final_grade,))
        update_stats_table(final_scores, final_grades)
        for row in rows_with_grades:
            for col_idx, value in enumerate(row):
                text_width = font.measure(str(value)) + 20
                column_widths[visible_columns[col_idx]] = max(column_widths[visible_columns[col_idx]], text_width)
        total_width = 0
        for col in visible_columns:
            width = column_widths[col]
            total_width += width
            sqlTree.column(col, width=width, anchor="center", stretch=False)
            sqlTree.heading(col, text=col)
        treeview_width = 760
        if total_width < treeview_width:
            extra_width = (treeview_width - total_width) // len(visible_columns)
            for col in visible_columns:
                current_width = sqlTree.column(col, option="width")
                sqlTree.column(col, width=current_width + extra_width)
        for row in rows_with_grades:
            sqlTree.insert("", "end", values=row)
    except sqlite3.OperationalError as e:
        labelFeedbackVarMain.set(f"Error loading data: {e}")
    finally:
        conn.close()
    update_dropdown_students(table_name)
    student_dropdown.set("Select Student")

def fetch_table_metadata(table_name, connection):
    global cur
    try:
        cur = connection.cursor()
        cur.execute(f"SELECT MetaData FROM '{table_name}' WHERE Student LIKE '_Meta_%';")
        metadata_rows = [row[0] for row in cur.fetchall()]
        if not metadata_rows:
            print(f"No metadata found for {table_name}.")
            return None
        grade_scale_data = metadata_rows[:5]
        component_weights_data = metadata_rows[5:]
        grade_scale = []
        for value in grade_scale_data:
            try:
                grade_scale.append(float(value))
            except (ValueError, TypeError):
                grade_scale.append(0.0)
        component_weights = []
        for value in component_weights_data:
            try:
                component_weights.append(float(value))
            except (ValueError, TypeError):
                component_weights.append(0.0)
        return {"grade_scale": grade_scale, "component_weights": component_weights}
    except sqlite3.OperationalError as e:
        print(f"Error fetching metadata for {table_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def on_table_row_selected(event):
    selected_item = sqlTree.selection()
    if not selected_item:
        student_dropdown.set("Select Student")
        return
    student_name = sqlTree.item(selected_item[0], "values")
    if student_name:
        student_dropdown.set(student_name[0])
    else:
        student_dropdown.set("Select Student")

# COURSE FUNCTIONS
def course(current_course):
    if current_course == "Select Course":
        labelFeedbackVarMain.set("Edit Error: You must either create or select a course first!")
        return
    root.withdraw()
    window_course = Toplevel(root)
    if current_course is None:
        window_course.title("Create A New Course:")
    else:
        window_course.title("Edit A Current Course:")
    window_course.geometry("850x600")
    window_course.resizable(False, False)
    window_course.grab_set()
    root.grab_set()
    # INSTRUCTION SECTION
    if current_course is None:
        label_instruction = Label(window_course, text="Please enter in everything, be sure the weights total to 100%, and have grade scale values be logical!", font=("Arial", 18))
    else:
        label_instruction = Label(window_course, text=f"You are currently editing the following course: {current_course}", font=("Arial", 18))
    label_instruction.grid(row=0, column=0, columnspan=3, padx=20, pady=10)
    # SEPARATOR
    separator = ttk.Separator(window_course, orient="horizontal")
    separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
    # FOUR FILL BLANKS
    def create_input_field(label_text, row, column, validate_command):
        label = Label(window_course, text=label_text, font=("Arial", 16))
        label.grid(row=row, column=column, padx=5, pady=5)
        entry = Entry(window_course, font=("Arial", 14), validate="key", validatecommand=(validate_command, "%S"))
        entry.grid(row=row, column=column + 1, padx=5, pady=5)
        return entry
    course_name_text =create_input_field("What is the course NAME?", 2, 0, validate_letter_cmd)
    course_num_text = create_input_field("What is the course NUMBER?", 3, 0, validate_letters_and_numbers_cmd)
    course_sec_text = create_input_field("What is the course SECTION?", 4, 0, validate_number_cmd)
    if current_course is None:
        course_student_text = create_input_field("How many STUDENTS are there?", 5, 0, validate_number_cmd)
    else:
        course_student_disclaimer = Label(window_course, text="You can change the STUDENTS count manually in the main window!", font=("Arial", 16))
        course_student_disclaimer.grid(row = 5, column = 0, columnspan=2, padx=5, pady=5)
    # ACCEPT BUTTON
    def accept_course():
        global i, conn, cur
        course_name = course_name_text.get().strip()
        course_number = course_num_text.get().strip()
        course_section = course_sec_text.get().strip()
        student_count = 0
        if current_course is None:
            student_count = course_student_text.get().strip()
        if not course_name:
            label_feedback_var_create.set("Accept Error: Course name cannot be empty.")
            return
        if not course_number:
            label_feedback_var_create.set("Accept Error: Course number cannot be empty.")
            return
        if not course_section:
            label_feedback_var_create.set("Accept Error: Course section cannot be empty.")
            return
        course_section = course_section.lstrip('0') or '0'
        if current_course is None:
            if not student_count:
                label_feedback_var_create.set("Accept Error: Student count cannot be empty.")
                return
            student_count = student_count.lstrip('0') or '0'
        section = f"{int(course_section):02d}"
        course_title = f"{course_name}:{course_number}_{section}"
        table_name = course_title.replace(" ", "_").replace(".", "").replace("-", "_")
        try:
            with sqlite3.connect(database_file) as conn:
                cur = conn.cursor()
                if current_course is None:
                    cur.execute("""
                            SELECT name FROM sqlite_master 
                            WHERE type='table' AND name=?
                        """, (table_name,))
                    if cur.fetchone():
                        label_feedback_var_create.set(f"Duplicate Error: A course with the title '{course_title}' already exists.")
                        return
                else:
                    cur.execute("""
                                SELECT name FROM sqlite_master 
                                WHERE type='table'
                            """)
                    existing_tables = [row[0] for row in cur.fetchall()]
                    if table_name != current_course and table_name in existing_tables:
                        label_feedback_var_create.set(f"Duplicate Error: A course with the title '{course_title}' already exists.")
                        return
        except sqlite3.OperationalError as e:
            label_feedback_var_create.set(f"Database Error: {e}")
            return
        total_weight = 0
        for child in tree.get_children():
            component_weight = tree.item(child)["values"][1]
            total_weight += int(component_weight)
        if total_weight != 100:
            label_feedback_var_create.set("Accept Error: The total weight of components must equal 100%.")
            return
        grade_scale_values = []
        for i, entry in enumerate(grade_entries):
            grade_value = entry.get().strip()
            if not grade_value:
                label_feedback_var_create.set(f"Accept Error: '{grade_ranges[i]}' does not have a value.")
                return
            if not grade_value.isdigit():
                label_feedback_var_create.set(f"Accept Error: '{grade_ranges[i]}' must be a valid number.")
                return
            grade_value_int = int(grade_value)
            if i == 0 and grade_value_int > 100:
                label_feedback_var_create.set(f"Accept Error: '{grade_ranges[i]}' cannot be greater than 100.")
                return
            grade_scale_values.append(grade_value_int)
        for i in range(3):
            if grade_scale_values[i] <= grade_scale_values[i + 1]:
                label_feedback_var_create.set(
                    f"Accept Error: '{grade_ranges[i]}' must be greater than '{grade_ranges[i + 1]}'.")
                return
        if grade_scale_values[3] != grade_scale_values[4]:
            label_feedback_var_create.set("Accept Error: 'D >=' must equal 'F <'.")
            return
        if current_course is None:
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
            create_table(course_data)
            labelFeedbackVarMain.set(f"You have successfully created the course: {course_name}")
        else:
            course_data = {
                "name": course_name,
                "number": course_number,
                "section": course_section,
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
            edit_table(course_data, current_course)
            labelFeedbackVarMain.set(f"You have successfully edited the course: {course_name}")
        cancel_new_course()
    if current_course is None:
       button_name_accept = "Accept"
    else:
       button_name_accept = "Save"
    button_course_accept = Button(window_course, text=button_name_accept, font=("Arial", 16), width=5, height=2, command=accept_course)
    button_course_accept.grid(row=2, rowspan=2, column=2, padx=5, pady=10)
    # CANCEL BUTTON
    def cancel_new_course():
        course_name_text.delete(0, END)
        course_num_text.delete(0, END)
        course_sec_text.delete(0, END)
        if current_course is None:
            course_student_text.delete(0, END)
        for child in tree.get_children():
            tree.delete(child)
        for entry in grade_entries:
            entry.delete(0, END)
        course_selected_entry.config(state="normal")
        course_selected_entry.delete(0, END)
        course_selected_entry.config(state="readonly")
        label_feedback_var_create.set("Please get started and I'll help the best I can.")
        window_course.grab_release()
        root.deiconify()
        window_course.destroy()
    button_course_new_cancel = Button(window_course, text="Cancel", font=("Arial", 16), width=5, height=2, command=cancel_new_course)
    button_course_new_cancel.grid(row=4, rowspan=2, column=2, padx=5, pady=10)
    # SEPARATOR
    separator = ttk.Separator(window_course, orient="horizontal")
    separator.grid(row=6, column=0, columnspan=3, sticky="ew", pady=10)
    # COMPONENTS LABEL
    components_main_label = Label(window_course, text="Class Components:", font=("Arial", 18))
    components_main_label.grid(row=7, column=0)
    # FRAME
    table_frame = Frame(window_course)
    table_frame.grid(row=8, column=0, columnspan=1, padx=10, pady=10, sticky="nsew")
    # FRAME > TREE TABLE
    def on_row_select(event):
        selected_item = tree.selection()
        if selected_item:
            item_values = tree.item(selected_item[0], "values")
            if item_values:
                selected_text = f"{item_values[0]} ({item_values[1]}%)"
                course_selected_entry.config(state="normal")
                course_selected_entry.delete(0, END)
                course_selected_entry.insert(0, selected_text)
                course_selected_entry.config(state="readonly")
    tree = ttk.Treeview(table_frame, columns=("Component", "Weight"), show="headings", height=8)
    tree.pack(side=LEFT, fill=BOTH, expand=True)
    tree.heading("Component", text="Component Name")
    tree.heading("Weight", text="Weight (%)")
    tree.column("Component", width=200, anchor="center")
    tree.column("Weight", width=100, anchor="center")
    tree.bind("<ButtonRelease-1>", on_row_select)
    # FRAME > SCROLLBAR
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=scrollbar.set)
    # ADD SECTION FRAME
    add_section_frame = Frame(window_course)
    add_section_frame.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
    # NEW COMPONENT ENTRY
    course_component_add_label = Label(add_section_frame, text="Enter Class Component (Name):", font=("Arial", 12))
    course_component_add_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    course_component_add_entry = Entry(add_section_frame, font=("Arial", 10))
    course_component_add_entry.grid(row=0, column=1, padx=5, pady=5)
    # NEW WEIGHT ENTRY
    course_weight_add_label = Label(add_section_frame, text="Enter Respective Weight (1-100):", font=("Arial", 12))
    course_weight_add_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    course_weight_add_entry = Entry(add_section_frame, font=("Arial", 10), validate="key", validatecommand=(validate_number_cmd, "%S"))
    course_weight_add_entry.grid(row=1, column=1, padx=5, pady=5)
    # SELECTED COMPONENT/WEIGHT VIEW
    course_selected_label = Label(add_section_frame, text="Selected Component From Table:", font=("Arial", 12))
    course_selected_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    course_selected_entry = Entry(add_section_frame, font=("Arial", 10), state="readonly")
    course_selected_entry.grid(row=2, column=1, padx=5, pady=5)
    # ADD BUTTON
    def add_component():
        forbidden_names = {"Student", "MetaData", "Final Grade"}
        component_name = course_component_add_entry.get().strip()
        component_weight = course_weight_add_entry.get().strip()
        component_weight = component_weight.lstrip('0') or '0'
        if not component_name:
            label_feedback_var_create.set("Add Error: Component name cannot be empty.")
            return
        if not component_weight.isdigit() or not (1 <= int(component_weight) <= 100):
            label_feedback_var_create.set("Add Error: Weight must be a number between 1 and 100.")
            return
        if component_name in forbidden_names:
            label_feedback_var_create.set(f"Add Error: '{component_name}' is not allowed as a component name.")
            return
        existing_components = [tree.item(child)["values"][0] for child in tree.get_children()]
        if component_name in existing_components:
            label_feedback_var_create.set(f"Add Error: Component name '{component_name}' already exists.")
            return
        tree.insert("", "end", values=(component_name, component_weight))
        label_feedback_var_create.set(f"Successfully added component '{component_name}' with weight {component_weight}%.")
        course_component_add_entry.delete(0, END)
        course_weight_add_entry.delete(0, END)
    add_component_button = Button(add_section_frame, text="Add", font=("Arial", 12), width=4, height=2, command=add_component)
    add_component_button.grid(row=0, column=2)
    # CHANGE BUTTON
    def change_component():
        forbidden_names = {"Student", "MetaData", "Final Grade"}
        selected_item = tree.selection()
        if not selected_item:
            label_feedback_var_create.set("Change Error: No component selected to change.")
            return
        new_component_name = course_component_add_entry.get().strip()
        new_component_weight = course_weight_add_entry.get().strip()
        new_component_weight = new_component_weight.lstrip('0') or '0'
        if not new_component_name:
            label_feedback_var_create.set("Change Error: Component name cannot be empty.")
            return
        if new_component_name in forbidden_names:
            label_feedback_var_create.set(f"Change Error: '{new_component_name}' is not allowed as a component name.")
            return
        if not new_component_weight.isdigit() or not (1 <= int(new_component_weight) <= 100):
            label_feedback_var_create.set("Change Error: Weight must be a number between 1 and 100.")
            return
        existing_components = [tree.item(child)["values"][0] for child in tree.get_children()]
        current_item_values = tree.item(selected_item[0], "values")
        if new_component_name in existing_components and new_component_name != current_item_values[0]:
            label_feedback_var_create.set(f"Change Error: Component name '{new_component_name}' already exists.")
            return
        tree.item(selected_item[0], values=(new_component_name, new_component_weight))
        label_feedback_var_create.set(
            f"Successfully changed to '{new_component_name}' with weight {new_component_weight}%.")
        course_component_add_entry.delete(0, END)
        course_weight_add_entry.delete(0, END)
        course_selected_entry.config(state="normal")
        course_selected_entry.delete(0, END)
        course_selected_entry.config(state="readonly")
    change_component_button = Button(add_section_frame, text="Change", font=("Arial", 12), width=4, height=2, command=change_component)
    change_component_button.grid(row=1, column=2)
    # DELETE BUTTON
    def delete_component():
        selected_item = tree.selection()
        if not selected_item:
            label_feedback_var_create.set("Delete Error: No component selected to delete.")
            return
        tree.delete(selected_item[0])
        course_selected_entry.delete(0, END)
        label_feedback_var_create.set("Successfully deleted the selected component.")
        course_selected_entry.config(state="normal")
        course_selected_entry.delete(0, END)
        course_selected_entry.config(state="readonly")
    delete_component_button = Button(add_section_frame, text="Delete", font=("Arial", 12), width=4, height=2, command=delete_component)
    delete_component_button.grid(row=2, column=2)
    # GRADE LABEL
    grade_label = Label(window_course, text="Grade Scale:", font=("Arial", 18))
    grade_label.grid(row=7, column=1)
    # GRADE ENTRY FRAME "TABLE"
    grade_frame = Frame(window_course)
    grade_frame.grid(row=8, column=1, padx=5, pady=5, sticky="e")
    grade_ranges = ["A >=", "B >=", "C >=", "D >=", "F <"]
    grade_entries = []
    for i, grade_range in enumerate(grade_ranges):
        grade_label_widget = Label(grade_frame, text=grade_range, font=("Arial", 16))
        grade_label_widget.grid(row=i, column=0, padx=5, pady=2)
        grade_entry_widget = Entry(grade_frame, font=("Arial", 14), width=5, validate="key", validatecommand=(validate_number_cmd, "%S"))
        grade_entry_widget.grid(row=i, column=1, padx=5, pady=2)
        grade_entries.append(grade_entry_widget)
    # FEEDBACK SECTION
    label_feedback_var_create = StringVar()
    label_feedback_var_create.set("Please get started and I'll help the best I can.")
    label_feedback_create = Label(window_course, textvariable=label_feedback_var_create, font=("Arial", 14), anchor="e", wraplength=300)
    label_feedback_create.grid(row=9, column=1, columnspan=2)
    # FILL IN ALL COMPONENT BLANKS
    if current_course is not None:
        # TOP SECTION
        def parse_current_course(current_course):
            global course_name, course_number, course_section
            course_parts = current_course.split(":")
            course_name = course_parts[0]
            course_number, course_section = course_parts[1].split("_")
            return course_name.replace("_", " "), course_number, course_section
        course_name, course_number, course_section = parse_current_course(current_course)
        course_name_text.insert(0, course_name)
        course_num_text.insert(0, course_number)
        course_sec_text.insert(0, course_section)
        # BOTTOM-LEFT SECTION
        def get_filtered_columns(table_name, excluded_columns):
            global conn, cur, filtered_columns
            try:
                with sqlite3.connect(database_file) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA table_info([{table_name}]);")
                    columns = cur.fetchall()
                    filtered_columns = [column[1] for column in columns if column[1] not in excluded_columns]
                    return filtered_columns
            except sqlite3.OperationalError as e:
                print(f"Error accessing table '{table_name}': {e}")
                return []
        filtered_columns = get_filtered_columns(current_course, {"Student", "MetaData", "Final Grade"})
        def get_metadata(table_name):
            global conn, cur, metadata_values
            with sqlite3.connect(database_file) as conn:
                cur = conn.cursor()
                query = f'SELECT MetaData FROM "{table_name}";'
                cur.execute(query)
                metadata_values = [row[0] for row in cur.fetchall() if row[0] is not None]
            return metadata_values
        metadata_values = get_metadata(current_course)
        weight_values = metadata_values[5:]
        for i, weight in enumerate(weight_values):
            tree.insert("", "end", values=(filtered_columns[i], int(weight)))
        # BOTTOM-RIGHT SECTION
        grade_values = metadata_values[:5]
        for i, entry_widget in enumerate(grade_entries):
            if i < len(grade_values):
                grade_int = int(grade_values[i])
                entry_widget.insert(0, str(grade_int))
            else:
                print(f"Default grade for {grade_ranges[i]} not set")
    # Configure grid to expand columns for separator
    window_course.grid_columnconfigure(0, weight=1)
    window_course.grid_columnconfigure(1, weight=1)
    window_course.grid_columnconfigure(2, weight=1)
    window_course.protocol("WM_DELETE_WINDOW", cancel_new_course)
    root.grab_release()
    window_course.wait_window()

def update_dropdown_courses():
    global conn, cur
    conn = sqlite3.connect(database_file)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    courses_from_db = cur.fetchall()
    conn.close()
    formatted_courses = [course[0] for course in courses_from_db]
    course_dropdown['values'] = formatted_courses
    if formatted_courses:
        course_dropdown.set(formatted_courses[0])
        display_table(formatted_courses[0])

def course_selected(event):
    selected_course = course_dropdown.get()
    if selected_course != "Select Course":
        display_table(selected_course)

def remove_course(current_course):
    root.withdraw()
    window_course_remove = Toplevel(root)
    window_course_remove.title("Remove a Course:")
    window_course_remove.geometry("925x275")
    window_course_remove.grab_set()
    current = current_course
    #QUESTION SECTION
    label_question = Label(window_course_remove,text=f"Are you sure you would like to delete the following course and all of its information:\n\n {current}", font=("Arial", 24), anchor="center")
    label_question.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
    #Y/N BUTTONS
    def cancel_remove():
        window_course_remove.grab_release()
        root.deiconify()
        window_course_remove.destroy()
    def accept_remove(course):
        global conn, cur
        if course == "Select Course":
            labelFeedbackVarMain.set(f"Remove Error: You cannot remove any more courses, please create a new course.")
            cancel_remove()
        else:
            try:
                conn = sqlite3.connect(database_file)
                cur = conn.cursor()
                table_name = course.replace(" ", "_").replace(".", "").replace("-", "_")
                cur.execute(f"DROP TABLE IF EXISTS '{table_name}'")
                conn.commit()
                conn.close()
                course_dropdown['values'] = tuple(v for v in course_dropdown['values'] if v != course)
                course_dropdown.set("Select Course")
                update_dropdown_students(course_dropdown.get())
                if sqlTree.get_children():
                    sqlTree.delete(*sqlTree.get_children())
                sqlTree["columns"] = []
                labelFeedbackVarMain.set(f"You have successfully deleted the course: {course}")
            except sqlite3.OperationalError as e:
                labelFeedbackVarMain.set(f"Error deleting course: {e}")
            finally:
                cancel_remove()
    button_cancel_remove = Button(window_course_remove, text="No", font=("Arial", 25), width=10, height=3, command=cancel_remove)
    button_cancel_remove.grid(row=1, column=0, padx=10, pady=40)
    button_accept_remove = Button(window_course_remove, text="Yes", font=("Arial", 25), width=10, height=3, command=lambda: accept_remove(current))
    button_accept_remove.grid(row=1, column=1, padx=10, pady=40)
    window_course_remove.grid_columnconfigure(0, weight=1)
    window_course_remove.grid_columnconfigure(1, weight=1)
    window_course_remove.protocol("WM_DELETE_WINDOW", cancel_remove)
    root.grab_release()
    window_course_remove.wait_window()

# STUDENT FUNCTIONS
def student(current_course, current_student):
    if current_student == "Select Student":
        labelFeedbackVarMain.set("Edit Student Error: Please select a student to edit their grades first.")
        return
    root.withdraw()
    window_student = Toplevel(root)
    if current_student is None:
        window_student.title("Add a New Student")
    else:
        window_student.title("Edit A Current Student:")
    window_student.geometry("825x500")
    window_student.grab_set()
    root.grab_set()
    label_instruction = Label(window_student, text="Please enter in as much as you can according to the new student's current status!", font=("Arial", 18))
    label_instruction.grid(row=0, column=0, columnspan=3, padx=60, pady=10)
    # SEPARATOR
    separator = ttk.Separator(window_student, orient="horizontal")
    separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
    # NAME ENTRY
    name_student_label = Label(window_student, text="What is the Student's NAME?:", font=("Arial", 16))
    name_student_label.grid(row=2, column=0, sticky="w", padx=50, pady=10)
    name_student_text = Entry(window_student, width=40, font=("Arial", 14), validate="key", validatecommand=(validate_letters_cmd, "%P"))
    name_student_text.grid(row=3, column=0, sticky="w", padx=50, pady=10)
    # ADD BUTTON
    def yes_student():
        global conn, cur, table_name, student_row
        student_name = name_student_text.get().strip()
        if not student_name:
            label_feedback_var_student.set("Add Error: Student's name is required.")
            return
        try:
            conn = sqlite3.connect(database_file)
            cur = conn.cursor()
            table_name = current_course.replace(" ", "_").replace(".", "").replace("-", "_")
            table_name = f"`{table_name}`"
            cur.execute(f"SELECT 1 FROM {table_name} WHERE `Student` = ?", (student_name,))
            existing_student = cur.fetchone()
            if existing_student:
                label_feedback_var_student.set("Add Error: Student with this name already exists.")
                return
            cur.execute(f"PRAGMA table_info({table_name})")
            columns_info = cur.fetchall()
            column_names = [info[1] for info in columns_info]
            column_names = [f"`{col}`" for col in column_names]
            new_student_row = (student_name,) + (None,) * (len(column_names) - 1)
            student_rows = []
            metadata_rows = []
            cur.execute(f"SELECT * FROM {table_name} ORDER BY ROWID")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == "_Meta_0" or row[0].startswith("_Meta_"):
                    metadata_rows.append(row)
                else:
                    student_rows.append(row)
            student_rows.append(new_student_row)
            conn.execute("BEGIN TRANSACTION")
            placeholders = ', '.join(['?'] * len(column_names))
            cur.execute(f"DELETE FROM {table_name}")
            for student_row in student_rows:
                if len(student_row) != len(column_names):
                    print(f"Error: Student row length mismatch. Row: {student_row}, Columns: {column_names}")
                    continue
                cur.execute(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})",
                            student_row)
            for metadata_row in metadata_rows:
                if len(metadata_row) != len(column_names):
                    print(f"Error: Metadata row length mismatch. Row: {metadata_row}, Columns: {column_names}")
                    continue
                updated_metadata_row = list(metadata_row)
                if updated_metadata_row[0] == "_Meta_0":
                    updated_metadata_row[1] = len(student_rows)  # Update student count
                cur.execute(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})", updated_metadata_row)
            conn.commit()
            labelFeedbackVarMain.set(f"{student_name} has been added successfully!")
        except sqlite3.Error as e:
            print(f"Database Error: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
        update_dropdown_courses()
        update_dropdown_students(current_course)
        display_table(current_course)
        edit_student(student_name, current_course)
    def edit_student(student, current_course):
        global table_name
        global grade, components, conn, cur, student_row
        grades_to_update = {}
        student_name = name_student_text.get().strip()
        if not student_name:
            label_feedback_var_student.set("Edit Error: Student's name is required.")
            return
        for row in student_tree.get_children():
            item_values = student_tree.item(row, "values")
            component_name = item_values[0]
            try:
                grade = float(item_values[1])
                grades_to_update[component_name] = grade
            except ValueError:
                label_feedback_var_student.set("Edit Error: Invalid grade.")
                return
        components = get_columns_between_student_and_metadata(current_course)
        try:
            conn = sqlite3.connect(database_file)
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM `{table_name}` WHERE `Student` = ?", (student,))
            student_row = cur.fetchone()
            if not student_row:
                label_feedback_var_student.set(f"Edit Error: No data found for student {student}.")
                return
            updated_row = list(student_row)
            for i, component in enumerate(components):
                selected_item = student_tree.get_children()[i]
                item_values = student_tree.item(selected_item, "values")
                try:
                    grade = float(item_values[1])
                    if grade < 0 or grade > 100:
                        raise ValueError(f"Grade must be between 0 and 100.")
                    component_index = i + 1  # +1 to skip the 'Student' column
                    updated_row[component_index] = grade
                except ValueError as e:
                    label_feedback_var_student.set(f"Edit Error: Invalid grade for {component}. {str(e)}")
                    return
            update_query = f"UPDATE `{table_name}` SET {', '.join([f'`{col}` = ?' for col in components])} WHERE `Student` = ?"
            cur.execute(update_query, (*[updated_row[i + 1] for i in range(len(components))], student))
            if student != student_name:
                update_query = f"UPDATE `{table_name}` SET {', '.join([f'`{col}` = ?' for col in components])}, `Student` = ? WHERE `Student` = ?"
                cur.execute(update_query, (*[updated_row[i + 1] for i in range(len(components))], student_name, student))
                labelFeedbackVarMain.set(f"Student name and grades updated successfully!")
            else:
                update_query = f"UPDATE `{table_name}` SET {', '.join([f'`{col}` = ?' for col in components])} WHERE `Student` = ?"
                cur.execute(update_query, (*[updated_row[i + 1] for i in range(len(components))], student))
                labelFeedbackVarMain.set(f"Grades for {student} updated successfully!")
            conn.commit()
            display_table(table_name)
        except sqlite3.Error as e:
            print(f"Database Error: {str(e)}")
            conn.rollback()
            label_feedback_var_student.set(f"Error: {str(e)}")
        finally:
            conn.close()
        no_student()
    if current_student is None:
        button_student_add = Button(window_student, text="Add", font=("Arial", 20), width=13, command=yes_student)
    else:
        button_student_add = Button(window_student, text="Edit", font=("Arial", 20), width=13, command=lambda:edit_student(current_student, current_course))
    button_student_add.grid(row=2, column=1, columnspan=2, sticky="w", pady=10)
    # CANCEL BUTTON
    def no_student():
        name_student_text.delete(0, END)
        for child in student_tree.get_children():
            student_tree.delete(child)
        label_grade_student_text.delete(0, END)
        label_component_var_student.set("Select a Component to start Grading!")
        label_feedback_var_student.set("Please get started and I'll help the best I can.")
        window_student.grab_release()
        root.deiconify()
        window_student.destroy()
    button_student_cancel = Button(window_student, text="Cancel", font=("Arial", 20), width=13, command=no_student)
    button_student_cancel.grid(row=3, column=1, columnspan=2, sticky="w", pady=10)
    # SEPARATOR
    separator = ttk.Separator(window_student, orient="horizontal")
    separator.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
    # TABLE
    def on_row_select(event):
        selected_item = student_tree.selection()
        if selected_item:
            item_values = student_tree.item(selected_item[0], "values")
            component_name = item_values[0]
            component_grade = item_values[1]
            label_component_var_student.set(f"Editing Grade for: {component_name}")
            label_grade_student_text.delete(0, END)
            label_grade_student_text.insert(0, component_grade)
    student_frame = Frame(window_student, width=350, height=250)
    student_frame.grid(row=5, rowspan=4, column=0, sticky="w", padx=50, pady=10)
    student_frame.grid_propagate(False)
    student_tree = ttk.Treeview(student_frame, show="headings", height=24)
    student_tree["columns"] = ("Components", "Grades")
    student_tree.heading("Components", text="Components")
    student_tree.heading("Grades", text="Grades")
    student_tree.column("Components", anchor="center", width=225)
    student_tree.column("Grades", anchor="center", width=75)
    student_vertical_scroll = ttk.Scrollbar(student_frame, orient="vertical", command=student_tree.yview)
    student_tree.configure(yscrollcommand=student_vertical_scroll.set)
    student_tree.grid(row=0, column=0, sticky="nsew")
    student_tree.bind("<<TreeviewSelect>>", on_row_select)
    student_vertical_scroll.grid(row=0, column=1, sticky="ns")
    student_frame.columnconfigure(0, weight=1)
    # COMPONENT LABEL
    label_component_var_student = StringVar()
    label_component_var_student.set("Select a Component to start Grading!")
    label_component_student_label = Label(window_student, textvariable=label_component_var_student, font=("Arial", 16))
    label_component_student_label.grid(row=5, column=1, columnspan=2, sticky="w")
    # GRADE ENTRY
    label_grade_student_text = Entry(window_student, width=10, font=("Arial", 14), validate="key", validatecommand=(validate_numbers_and_decimals_cmd, "%P"))
    label_grade_student_text.grid(row=6, column=1, sticky="w")
    # APPLY BUTTON
    def apply_student():
        student_grade = label_grade_student_text.get()
        try:
            student_grade = float(student_grade)
            if student_grade < 0 or student_grade > 100:
                raise ValueError("Grade must be between 0 and 100.")
            student_grade = round(student_grade, 2)
            selected_item = student_tree.selection()
            if selected_item:
                item_values = student_tree.item(selected_item[0], "values")
                component_name = item_values[0]
                student_tree.item(selected_item[0], values=(component_name, student_grade))
                label_feedback_var_student.set(f"Grade for {component_name} updated successfully!")
            else:
                label_feedback_var_student.set("Apply Error: No component selected for grading.")
        except ValueError as e:
            label_feedback_var_student.set(f"Apply Error: {str(e)}")
    button_student_add = Button(window_student, text="Apply", font=("Arial", 16), width=5, command=apply_student)
    button_student_add.grid(row=6, column=2, sticky="w")
    # FEEDBACK
    label_feedback_var_student = StringVar()
    label_feedback_var_student.set("Please get started and I'll help the best I can.")
    label_feedback_student = Label(window_student, textvariable=label_feedback_var_student, font=("Arial", 14), wraplength=225)
    label_feedback_student.grid(row=7, column=1, columnspan=2)
    # FILL IN THE BLANKS
    if current_student is not None:
        name_student_text.insert(0, current_student)
    def get_columns_between_student_and_metadata(course_name):
        global conn, cur, table_name
        table_name = course_name.replace(" ", "_").replace(".", "").replace("-", "_")
        conn = sqlite3.connect(database_file)
        cur = conn.cursor()
        try:
            cur.execute(f"PRAGMA table_info('{table_name}');")
            columns_info = cur.fetchall()
            column_names = [info[1] for info in columns_info]
            start_index = column_names.index("Student") + 1
            end_index = column_names.index("MetaData")
            relevant_columns = column_names[start_index:end_index]
            return relevant_columns
        except ValueError as e:
            raise ValueError(f"'Student' or 'MetaData' column not found in table '{table_name}'.") from e
        finally:
            conn.close()
    components = get_columns_between_student_and_metadata(current_course)
    escaped_components = [f"`{component}`" for component in components]
    display_components = [component.replace('`', '') for component in components]
    if current_student is None:
        for component in display_components:
            grade = 100.0
            student_tree.insert("", "end", values=(component, grade))
    else:
        table_name = current_course.replace(" ", "_").replace(".", "").replace("-", "_")
        conn = sqlite3.connect(database_file)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT {', '.join(escaped_components)} FROM `{table_name}` WHERE `Student` = ?", (current_student,))
            student_row = cur.fetchone()
            if not student_row:
                print(f"No data found for student {current_student}")
            else:
                for component, grade in zip(display_components, student_row):
                    if grade is None:
                        grade = 100.0
                    student_tree.insert("", "end", values=(component, grade))
        except sqlite3.Error as e:
            print(f"Database Error: {str(e)}")
        finally:
            conn.close()
    # Configure grid to expand columns for separator
    window_student.grid_columnconfigure(0, weight=1)
    window_student.grid_columnconfigure(1, weight=1)
    window_student.grid_columnconfigure(2, weight=1)
    window_student.protocol("WM_DELETE_WINDOW", no_student)
    root.grab_release()
    window_student.wait_window()

def update_dropdown_students(current_course):
    global conn, cur, students
    table_name = current_course.replace(" ", "_").replace(".", "").replace("-", "_")
    table_name = f"`{table_name}`"
    if table_name == "`Select_Course`":
        students = []
        student_dropdown['values'] = students
        student_dropdown.set("Select Student")
        labelFeedbackVarMain.set("Please select or make a valid course.")
        return
    else:
        try:
            conn = sqlite3.connect(database_file)
            cur = conn.cursor()
            cur.execute(f"SELECT Student FROM {table_name} WHERE Student NOT LIKE '_Meta_%'")
            students = [row[0] for row in cur.fetchall()]
            student_dropdown['values'] = students
        except sqlite3.Error as e:
            print(f"Error fetching students for {current_course}: {e}")
        finally:
            conn.close()

def student_selected(event):
    selected_student = student_dropdown.get()
    if selected_student == "Select Student":
        labelFeedbackVarMain.set("Student Error: Invalid Student selected")

def remove_student(current_course, current_student):
    root.withdraw()
    window_student_remove = Toplevel(root)
    window_student_remove.title("Remove a Student:")
    window_student_remove.geometry("1000x275")
    window_student_remove.grab_set()
    #QUESTION SECTION
    label_question = Label(window_student_remove,text=f"Please confirm that you would like to delete the following student and their information:\n\n {current_student} in {current_course}", font=("Arial", 24), anchor="center")
    label_question.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
    #Y/N BUTTONS
    def cancel_remove():
        window_student_remove.grab_release()
        root.deiconify()
        window_student_remove.destroy()
    def accept_remove(course, student):
        global conn, cur
        if course == "Select Course":
            labelFeedbackVarMain.set(f"Remove Error: You cannot remove any more courses, please create a new course.")
            cancel_remove()
        elif student == "Select Student":
            labelFeedbackVarMain.set("Remove Error: You cannot remove a student you have not chosen, please select a student first.")
            cancel_remove()
        else:
            try:
                conn = sqlite3.connect(database_file)
                cur = conn.cursor()
                table_name = course.replace(" ", "_").replace(".", "").replace("-", "_")
                cur.execute(f"DELETE FROM '{table_name}' WHERE Student = ?", (student,))
                conn.commit()
                update_dropdown_students(current_course)
                display_table(current_course)
                labelFeedbackVarMain.set(f"You have successfully deleted the student: {student}")
            except sqlite3.OperationalError as e:
                labelFeedbackVarMain.set(f"Error deleting course: {e}")
            finally:
                cancel_remove()
    button_cancel_remove = Button(window_student_remove, text="No", font=("Arial", 25), width=10, height=3, command=cancel_remove)
    button_cancel_remove.grid(row=1, column=0, padx=10, pady=40)
    button_accept_remove = Button(window_student_remove, text="Yes", font=("Arial", 25), width=10, height=3, command=lambda: accept_remove(current_course, current_student))
    button_accept_remove.grid(row=1, column=1, padx=10, pady=40)
    window_student_remove.grid_columnconfigure(0, weight=1)
    window_student_remove.grid_columnconfigure(1, weight=1)
    window_student_remove.protocol("WM_DELETE_WINDOW", cancel_remove)
    root.grab_release()
    window_student_remove.wait_window()

# COURSE DROPDOWN
labelSelectCourse = Label(root, text="Select Course:", font=("Arial", 20))
labelSelectCourse.grid(row=0, column=0, pady=10)
course_dropdown = ttk.Combobox(root, values=[], state="readonly", font=("Arial", 16))
course_dropdown.set("Select Course")
course_dropdown.grid(row=1, column=0, padx=10)
course_dropdown.bind("<<ComboboxSelected>>", course_selected)

# STUDENT DROPDOWN
labelSelectStudent = Label(root, text="Select Student:", font=("Arial", 20), pady=10)
labelSelectStudent.grid(row=0, column=3, pady=10)
student_dropdown = ttk.Combobox(root, values=[], state="readonly", font=("Arial", 16))
student_dropdown.set("Select Student")
student_dropdown.grid(row=1, column=3, padx=10)
student_dropdown.bind("<<ComboboxSelected>>", student_selected)

# FEEDBACK
labelFeedbackVarMain = StringVar()
labelFeedbackVarMain.set("Welcome! This is your Grade Book application. Please get started and I'll help the best I can.")
labelFeedback = Label(root, textvariable=labelFeedbackVarMain, font=("Arial", 18), wraplength=600)
labelFeedback.grid(row=0, rowspan=2, column=1, columnspan=2, padx=50)

# STATS REPORT
statsFrame = Frame(root)
statsFrame.grid(row=4, column=1, padx=50, pady=10)
statsTree = ttk.Treeview(statsFrame, columns=("Mean", "Median", "Mode", "Std. Dev."), show="headings", height=2)
statsTree.pack()
statColumns = ["Mean", "Median", "Mode", "Std. Dev."]
for column in statColumns:
    statsTree.heading(column, text=column)
    statsTree.column(column, width=75, anchor="center")

# FAIL REPORT
failFrame = Frame(root)
failFrame.grid(row=4, column=2, padx=50, pady=10)
failScrollbar = Scrollbar(failFrame, orient="vertical")
failScrollbar.pack(side="right", fill="y")
failTree = ttk.Treeview(failFrame, columns=("D Students", "F Students"), show="headings", height=5, yscrollcommand=failScrollbar.set)
failTree.pack(side="left", fill="both", expand=True)
failScrollbar.config(command=failTree.yview)
failColumns = ["D Students", "F Students"]
for column in failColumns:
    failTree.heading(column, text=column)
    failTree.column(column, width=150, anchor="center")

# COURSE BUTTONS
buttonCourseCreate = Button(root, text="Create Course", font=("Arial", 20), width=13, height=5, command=lambda: course(None))
buttonCourseCreate.grid(row=2, column=0, padx=10, pady=40)
buttonCourseEdit = Button(root, text="Edit Course", font=("Arial", 20), width=13, height=5, command=lambda: course(course_dropdown.get()))
buttonCourseEdit.grid(row=3, column=0, padx=10, pady=40)
buttonCourseRemove = Button(root, text="Remove Course", font=("Arial", 20), width=13, height=5, command=lambda: remove_course(course_dropdown.get()))
buttonCourseRemove.grid(row=4, column=0, padx=10, pady=40)

# STUDENT BUTTONS
buttonStudentAdd = Button(root, text="Add Student", font=("Arial", 20), width=13, height=5, command=lambda: student(course_dropdown.get(), None))
buttonStudentAdd.grid(row=2, column=3, padx=10, pady=40)
buttonStudentEdit = Button(root, text="Edit Student", font=("Arial", 20), width=13, height=5, command=lambda: student(course_dropdown.get(), student_dropdown.get()))
buttonStudentEdit.grid(row=3, column=3, padx=10, pady=40)
buttonStudentRemove = Button(root, text="Remove Student", font=("Arial", 20), width=13, height=5, command=lambda: remove_student(course_dropdown.get(), student_dropdown.get()))
buttonStudentRemove.grid(row=4, column=3, padx=10, pady=40)

# DISPLAY SQL TABLE
sqlFrame = Frame(root, width=760, height=400)
sqlFrame.grid(row=0, rowspan=5, column=1, columnspan=2)
sqlFrame.grid_propagate(False)
sqlTree = ttk.Treeview(sqlFrame, show="headings", height=24)
vertical_scroll = ttk.Scrollbar(sqlFrame, orient="vertical", command=sqlTree.yview)
horizontal_scroll = ttk.Scrollbar(sqlFrame, orient="horizontal", command=sqlTree.xview)
sqlTree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
sqlTree.grid(row=0, column=0, sticky="nsew")
sqlTree.bind("<<TreeviewSelect>>", on_table_row_selected)
vertical_scroll.grid(row=0, column=1, sticky="ns")
horizontal_scroll.grid(row=1, column=0, sticky="ew")
sqlFrame.rowconfigure(0, weight=1)
sqlFrame.columnconfigure(0, weight=1)

update_dropdown_courses()
initialize_table()
root.mainloop()
