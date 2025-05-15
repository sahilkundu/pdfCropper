import fitz  # PyMuPDF
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class PDFCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Crop Tool")
        self.pdf_document = None
        self.current_page = 0
        self.rect = None
        self.scale_factor = 1.0  # For scaling the image
        
        self.init_ui()
    
    def init_ui(self):
        tk.Button(self.root, text="Open PDF", command=self.open_pdf).pack(pady=10)
        tk.Button(self.root, text="Crop Current Page", command=self.crop_page).pack(pady=10)
        tk.Button(self.root, text="Apply Crop to All Pages", command=self.apply_crop_to_all).pack(pady=10)
        self.canvas = tk.Canvas(self.root, width=800, height=800)  # Adjust canvas size if needed
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.finish_crop)

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if pdf_path:
            self.pdf_document = fitz.open(pdf_path)
            self.current_page = 0  # Start with the first page
            self.show_page(self.current_page)

    def show_page(self, page_num):
        if self.pdf_document:
            self.canvas.delete("all")
            page = self.pdf_document[page_num]
            pix = page.get_pixmap()
            
            # Calculate scale factor to fit the canvas
            self.scale_factor = min(800 / pix.height, 800 / pix.width)  # Scale to fit canvas
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Resize image according to scale factor
            img = img.resize((int(img.width * self.scale_factor), int(img.height * self.scale_factor)), Image.LANCZOS)

            # Convert image to PhotoImage for Tkinter
            self.photo_image = ImageTk.PhotoImage(img)
            
            # Draw the image on the canvas
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
            self.canvas.update_idletasks()

    def start_crop(self, event):
        self.rect = [event.x, event.y, event.x, event.y]

    def update_crop(self, event):
        if self.rect:
            self.canvas.delete("crop_rect")
            self.rect[2] = event.x
            self.rect[3] = event.y
            self.canvas.create_rectangle(self.rect[0], self.rect[1], self.rect[2], self.rect[3], outline="red", tag="crop_rect")

    def finish_crop(self, event):
        self.rect[2] = event.x
        self.rect[3] = event.y
        self.canvas.create_rectangle(self.rect[0], self.rect[1], self.rect[2], self.rect[3], outline="red", tag="crop_rect")

    def crop_page(self):
        if self.rect and self.pdf_document:
            # Adjust the rectangle according to the scale factor
            scaled_rect = [coord / self.scale_factor for coord in self.rect]
            page = self.pdf_document[self.current_page]
            page.set_cropbox(fitz.Rect(scaled_rect[0], scaled_rect[1], scaled_rect[2], scaled_rect[3]))
            messagebox.showinfo("Success", f"Cropped page {self.current_page + 1} successfully.")

    def apply_crop_to_all(self):
        if self.pdf_document and self.rect:
            for i in range(len(self.pdf_document)):
                page = self.pdf_document[i]
                media_box = page.rect

                # Adjust the rectangle according to the scale factor
                scaled_rect = [coord / self.scale_factor for coord in self.rect]

                # Ensure the crop rectangle is within the MediaBox
                scaled_rect = [
                    max(media_box.x0, min(scaled_rect[0], media_box.x1)),
                    max(media_box.y0, min(scaled_rect[1], media_box.y1)),
                    max(media_box.x0, min(scaled_rect[2], media_box.x1)),
                    max(media_box.y0, min(scaled_rect[3], media_box.y1))
                ]

                # Ensure the crop box has a valid area
                if scaled_rect[2] > scaled_rect[0] and scaled_rect[3] > scaled_rect[1]:
                    try:
                        page.set_cropbox(fitz.Rect(scaled_rect[0], scaled_rect[1], scaled_rect[2], scaled_rect[3]))
                    except ValueError as e:
                        messagebox.showerror("Error", f"Error cropping page {i + 1}: {e}")
                        continue

            output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            if output_path:
                self.pdf_document.save(output_path)
                messagebox.showinfo("Success", "Cropped PDF saved successfully.")
            self.pdf_document.close()
            self.pdf_document = None  # Reset the document reference


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFCropperApp(root)
    root.mainloop()
