# -*- coding: utf-8 -*-
# @Author: John Hammond
# @Date:   2019-05-07 17:57:40
# @Last Modified by:   John Hammond
# @Last Modified time: 2019-06-01 20:49:03

import time
import tkinter
from PIL import ImageTk, Image
import threading
import os


class GUIThread(threading.Thread):
	'''
	This is a thread to keep Tkinter encapsulated.
	It is created from the Tkinter root widget, and it has both that widget
	and Katana itself passed into it. It runs "infinitely" so it works as 
	its own thread.
	'''

	def __init__(self, tk_root, katana):
		# Store the arguments passed, and create a thread for itself.
		self.root = tk_root
		self.katana = katana
		threading.Thread.__init__(self)

	def run(self):
		# Call katana.evaluate, so the real application runs.
		self.katana.evaluate()
		# Loop forever, so this thread stays alive.
		try:
			while 1:
				time.sleep(1)
		except KeyboardInterrupt:
			return


class GUIKatana(tkinter.Tk):
	'''
	This object encapsulates the Tkinter window, and all of its widgets.
	It has the Katana object passed into it, so it can give it to its thread.
	'''

	def __init__( self, katana ):
		super(GUIKatana, self).__init__()

		# Tell Katana about this object, so it can add_images appropriately.
		katana.gui = self
		self.geometry('900x600')
		self.title('Katana - Image Results')
		# Create its thread with Katana passed along, so it can run evaluate.
		self.thread = GUIThread(self, katana )

		# Build the widgets.
		self.left_frame = tkinter.Frame(self)
		self.left_frame.pack(side = tkinter.BOTTOM, expand=False, \
							 fill = tkinter.BOTH)

		self.listbox = tkinter.Listbox(self.left_frame)
		self.listbox.pack(anchor='s', fill=tkinter.X, expand=False)
		self.listbox.focus_set()
		
		self.right_frame = tkinter.Frame(self)
		self.right_frame.pack(side = tkinter.TOP, expand=True, \
							  fill = tkinter.BOTH)

		self.copy_of_image = None
		self.image_label = tkinter.Label(self.right_frame, \
										 text = "No Images Found Yet")
		self.image_label.bind('<Configure>', self.resize_image)
		self.image_label.pack(expand = True, fill = tkinter.BOTH )

		# This is the function bound for when a list item is selected;
		# it updates the image if it is an accessible file.
		def list_select(event):
			listbox = event.widget

			try:
				index = int(listbox.curselection()[0])
			except IndexError:
				return
			value = listbox.get(index)

			if os.path.exists( value ):
				try:
					raw_image = Image.open(value)
					image = ImageTk.PhotoImage(raw_image)
					self.copy_of_image = raw_image.copy()
					raw_image_w, raw_image_h = raw_image.size

					self.image_label.configure(image = image, text = '')
					self.image_label.image = image

					window_w = self.thread.root.winfo_width()
					window_h = self.thread.root.winfo_height()
					if window_w < raw_image_w or window_h < raw_image_h:
						
						image = self.copy_of_image.resize((window_w, window_h-150))
						photo = ImageTk.PhotoImage(image)
						self.image_label.config(image = photo)
						self.image_label.image = photo #avoid garbage collection
				except OSError as e:
					self.image_label.configure(text = e.args, image = '')

		# Bind the selection function, and start the thread so Katana runs!
		self.listbox.bind('<<ListboxSelect>>', list_select)
		self.thread.start()


	def resize_image(self, event):
		new_width = event.width
		new_height = event.height
		if self.copy_of_image is not None:
			image = self.copy_of_image.resize((new_width, new_height))
			photo = ImageTk.PhotoImage(image)
			self.image_label.config(image = photo)
			self.image_label.image = photo #avoid garbage collection


	def insert(self, filename):
		'''
		This function adds to the images list. If it is the first image added,
		it goes ahead and shows that image.
		'''
		self.listbox.insert(tkinter.END, filename)
		if len(self.listbox.curselection()) == 0:
			self.listbox.selection_set(0)
			try:
				index = int(self.listbox.curselection()[0])
			except IndexError:
				return
			value = self.listbox.get(index)

			if os.path.exists( value ):
				raw_image = Image.open(value)
				raw_image_w, raw_image_h = raw_image.size
				self.copy_of_image = raw_image.copy()
				image = ImageTk.PhotoImage(raw_image)
				self.image_label.configure(image = image)
				self.image_label.image = image
				window_w = self.thread.root.winfo_width()
				window_h = self.thread.root.winfo_height()
				if window_w < raw_image_w or window_h < raw_image_h:
					
					image = self.copy_of_image.resize((window_w, window_h-150))
					photo = ImageTk.PhotoImage(image)
					self.image_label.config(image = photo)
					self.image_label.image = photo #avoid garbage collection


	def evaluate(self):
		'''
		This function just lets Tkinter run. It is named "evaluate" just to
		match the format of what Katana already uses.
		'''
		try:
			tkinter.mainloop()
		except KeyboardInterrupt:
			return