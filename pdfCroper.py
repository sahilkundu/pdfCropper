import fitz  # PyMuPDF
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import copy

class PDFCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Crop Tool")
        self.pdf_document = None
        self.current_page = 0
        self.rect = None
        self.scale_factor = 1.0
        self.crop_history = {}  # For undo/redo
        self.undo_stack = {}
        self.redo_stack = {}

        self.init_ui()

    def init_ui(self):
        # Control buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="Open PDF", command=self.open_pdf).grid(row=0, column=0, padx=5)
        tk.Button(control_frame, text="Previous Page", command=self.previous_page).grid(row=0, column=1, padx=5)
        tk.Button(control_frame, text="Next Page", command=self.next_page).grid(row=0, column=2, padx=5)
        tk.Button(control_frame, text="Crop Current Page", command=self.crop_page).grid(row=0, column=3, padx=5)
        tk.Button(control_frame, text="Apply Crop to All Pages", command=self.apply_crop_to_all).grid(row=0, column=4, padx=5)
        tk.Button(control_frame, text="Undo", command=self.undo_crop).grid(row=0, column=5, padx=5)
        tk.Button(control_frame, text="Redo", command=self.redo_crop).grid(row=0, column=6, padx=5)
        tk.Button(control_frame, text="Save PDF", command=self.save_pdf).grid(row=0, column=7, padx=5)

        # Canvas
        self.canvas = tk.Canvas(self.root, width=800, height=800)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.finish_crop)

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if pdf_path:
            self.pdf_document = fitz.open(pdf_path)
            self.crop_history = {i: page.cropbox for i, page in enumerate(self.pdf_document)}
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.current_page = 0
            self.show_page(self.current_page)

    def show_page(self, page_num):
        if self.pdf_document:
            self.canvas.delete("all")
            page = self.pdf_document[page_num]
            pix = page.get_pixmap()
            self.scale_factor = min(800 / pix.height, 800 / pix.width)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((int(img.width * self.scale_factor), int(img.height * self.scale_factor)), Image.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

    def next_page(self):
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def start_crop(self, event):
        self.rect = [event.x, event.y, event.x, event.y]

    def update_crop(self, event):
        if self.rect:
            self.canvas.delete("crop_rect")
            self.rect[2], self.rect[3] = event.x, event.y
            self.canvas.create_rectangle(*self.rect, outline="red", tag="crop_rect")

    def finish_crop(self, event):
        self.rect[2], self.rect[3] = event.x, event.y
        self.canvas.create_rectangle(*self.rect, outline="red", tag="crop_rect")

    def crop_page(self):
        if self.rect and self.pdf_document:
            page = self.pdf_document[self.current_page]
            # Save current cropbox for undo
            self.undo_stack.setdefault(self.current_page, []).append(copy.deepcopy(page.cropbox))
            self.redo_stack.pop(self.current_page, None)

            scaled_rect = [coord / self.scale_factor for coord in self.rect]
            cropbox = fitz.Rect(*scaled_rect)
            page.set_cropbox(cropbox)
            messagebox.showinfo("Success", f"Cropped page {self.current_page + 1} successfully.")

    def apply_crop_to_all(self):
        if self.pdf_document and self.rect:
            scaled_rect = [coord / self.scale_factor for coord in self.rect]
            cropbox = fitz.Rect(*scaled_rect)
            for i, page in enumerate(self.pdf_document):
                # Save current cropbox for undo
                self.undo_stack.setdefault(i, []).append(copy.deepcopy(page.cropbox))
                try:
                    page.set_cropbox(cropbox)
                except Exception as e:
                    messagebox.showerror("Error", f"Error cropping page {i+1}: {e}")
            messagebox.showinfo("Success", "Crop applied to all pages.")

    def save_pdf(self):
        if self.pdf_document:
            output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            if output_path:
                self.pdf_document.save(output_path)
                messagebox.showinfo("Saved", "PDF saved successfully.")

    def undo_crop(self):
        if self.pdf_document and self.current_page in self.undo_stack and self.undo_stack[self.current_page]:
            page = self.pdf_document[self.current_page]
            current_crop = copy.deepcopy(page.cropbox)
            last_crop = self.undo_stack[self.current_page].pop()
            self.redo_stack.setdefault(self.current_page, []).append(current_crop)
            page.set_cropbox(last_crop)
            self.show_page(self.current_page)
            messagebox.showinfo("Undo", f"Undo successful on page {self.current_page + 1}.")

    def redo_crop(self):
        if self.pdf_document and self.current_page in self.redo_stack and self.redo_stack[self.current_page]:
            page = self.pdf_document[self.current_page]
            current_crop = copy.deepcopy(page.cropbox)
            next_crop = self.redo_stack[self.current_page].pop()
            self.undo_stack.setdefault(self.current_page, []).append(current_crop)
            page.set_cropbox(next_crop)
            self.show_page(self.current_page)
            messagebox.showinfo("Redo", f"Redo successful on page {self.current_page + 1}.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFCropperApp(root)
    root.mainloop()
