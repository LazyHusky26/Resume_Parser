import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import csv
import re
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_job_title(job_title_from_url):
    cleaned_title = job_title_from_url.replace("-", " ").title()
    return cleaned_title

def find_matching_job(job_search):
    matching_job = None
    matching_skills = None

    try:
        with open('job_skills.csv', mode='r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)

            for row in csv_reader:
                job_url, required_skills = row
                job_title_from_url = re.search(r'view/(.*?)-\d+', job_url)

                if job_title_from_url:
                    job_title = clean_job_title(job_title_from_url.group(1))
                else:
                    continue

                if job_search.lower() in job_title.lower():
                    matching_job = job_title
                    matching_skills = required_skills
                    break
    except FileNotFoundError:
        return None, None

    return matching_job, matching_skills

def compare_skills(user_skills, matching_skills):
    user_skills_list = [skill.strip() for skill in user_skills.split(",")]
    new_skills_list = [skill.strip() for skill in matching_skills.split(",")]

    user_skills_set = set(skill.lower() for skill in user_skills_list)
    new_skills_set = set(skill.lower() for skill in new_skills_list)

    missing_skills = new_skills_set - user_skills_set
    if missing_skills:
        missing_skills_list = [skill for skill in new_skills_list if skill.lower() in missing_skills]
        grouped_skills = [", ".join(missing_skills_list[i:i + 3]) for i in range(0, len(missing_skills_list), 3)]
        return "\n".join(grouped_skills)
    else:
        return "You have all the required skills!"

def extract_resume_text(pdf_path):
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text()
    return full_text

def clean_resume_text(resume_text):
    cleaned_text = re.sub(r'http\S+|www\S+|[\d]{4}-[\d]{2}-[\d]{2}|[\d]{4}-[\d]{2}|[\d]{2}/\d{2}/\d{4}', '', resume_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def split_into_sections(resume_text):
    sections = re.split(r'\n\s*\n', resume_text)
    return sections

def extract_skills_from_section(section):
    section = section.lower()
    section = re.sub(r'[^\w\s,•]', '', section)
    skill_list = [skill.strip() for skill in re.split(r'[,\n•]', section) if skill.strip()]
    return skill_list

def identify_skill_sections(sections):
    vectorizer = TfidfVectorizer()
    section_vectors = vectorizer.fit_transform(sections)
    similarity_matrix = cosine_similarity(section_vectors)

    skill_sections = []
    for i, section in enumerate(sections):
        if similarity_matrix[i].max() > 0.2:
            skill_sections.append(section)

    return skill_sections

def on_search_button_click():
    global current_skills

    job_search = job_title_entry.get().strip()

    if not job_search:
        messagebox.showerror("Input Error", "Job title is required!")
        return
    
    if skill_choice.get() == "Manual":
        user_skills = skills_entry.get().strip()

        if not user_skills:
            messagebox.showerror("Input Error", "Skills are required if manually entered!")
            return

        matching_job, matching_skills = find_matching_job(job_search)

        if matching_job:
            result_text = f"Matching job found: {matching_job}\n\n"
            missing_skills = compare_skills(user_skills, matching_skills)
            result_text += f"Other Skills Required:\n{missing_skills}"

            additional_skills_label.grid(row=5, column=0, padx=10, pady=10)
            additional_skills_entry.grid(row=5, column=1, padx=10, pady=10)
            add_skills_button.grid(row=6, column=0, columnspan=2, pady=10)

            current_skills = user_skills

        else:
            result_text = "No matching job found."

    elif skill_choice.get() == "Upload Resume":
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

        if not file_path:
            messagebox.showerror("Input Error", "Please upload a resume!")
            return

        resume_text = extract_resume_text(file_path)
        cleaned_resume_text = clean_resume_text(resume_text)

        sections = split_into_sections(cleaned_resume_text)
        skill_sections = identify_skill_sections(sections)

        all_skills = []
        for section in skill_sections:
            skills = extract_skills_from_section(section)
            all_skills.extend(skills)

        extracted_skills = ", ".join(all_skills)
        matching_job, matching_skills = find_matching_job(job_search)

        if matching_job:
            result_text = f"Matching job found: {matching_job}\n\n"
            missing_skills = compare_skills(extracted_skills, matching_skills)
            result_text += f"Other Skills Required:\n{missing_skills}"

            additional_skills_label.grid(row=5, column=0, padx=10, pady=10)
            additional_skills_entry.grid(row=5, column=1, padx=10, pady=10)
            add_skills_button.grid(row=6, column=0, columnspan=2, pady=10)

            current_skills = extracted_skills

        else:
            result_text = "No matching job found."

    result_text_box.config(state=tk.NORMAL)
    result_text_box.delete(1.0, tk.END)
    result_text_box.insert(tk.END, result_text)
    result_text_box.config(state=tk.DISABLED)

def add_more_skills():
    global current_skills
    additional_skills = additional_skills_entry.get().strip()

    if not additional_skills:
        messagebox.showerror("Input Error", "Please enter some additional skills!")
        return

    updated_skills = current_skills + ", " + additional_skills

    matching_job, matching_skills = find_matching_job(job_title_entry.get().strip())
    updated_result = compare_skills(updated_skills, matching_skills)

    updated_result_text = f"Updated Missing Skills:\n{updated_result}"

    result_text_box.config(state=tk.NORMAL)
    result_text_box.delete(1.0, tk.END)
    result_text_box.insert(tk.END, updated_result_text)
    result_text_box.config(state=tk.DISABLED)

root = tk.Tk()
root.title("Job Skill Matcher")

job_title_label = tk.Label(root, text="Enter Job Title:")
job_title_label.grid(row=0, column=0, padx=10, pady=10)
job_title_entry = tk.Entry(root, width=50)
job_title_entry.grid(row=0, column=1, padx=10, pady=10)

skill_choice = tk.StringVar(value="Manual")

manual_skills_radio = tk.Radiobutton(root, text="Manual Skills", variable=skill_choice, value="Manual")
manual_skills_radio.grid(row=1, column=0, padx=10, pady=10)

upload_resume_radio = tk.Radiobutton(root, text="Upload Resume", variable=skill_choice, value="Upload Resume")
upload_resume_radio.grid(row=1, column=1, padx=10, pady=10)

skills_label = tk.Label(root, text="Enter Your Skills (comma separated):")
skills_entry = tk.Entry(root, width=50)

def update_skills_field():
    if skill_choice.get() == "Manual":
        skills_label.grid(row=2, column=0, padx=10, pady=10)
        skills_entry.grid(row=2, column=1, padx=10, pady=10)
    else:
        skills_label.grid_forget()
        skills_entry.grid_forget()

skill_choice.trace("w", lambda *args: update_skills_field())

search_button = tk.Button(root, text="Find Matching Job", command=on_search_button_click)
search_button.grid(row=3, column=0, columnspan=2, pady=20)

result_text_box = tk.Text(root, width=80, height=10, wrap=tk.WORD, padx=10, pady=10)
result_text_box.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
result_text_box.config(state=tk.DISABLED)

additional_skills_label = tk.Label(root, text="Enter Additional Skills (comma separated):")
additional_skills_entry = tk.Entry(root, width=50)

add_skills_button = tk.Button(root, text="Update Missing Skills", command=add_more_skills)

root.mainloop()
