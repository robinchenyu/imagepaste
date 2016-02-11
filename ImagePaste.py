import sublime, sublime_plugin
import os
try:
	from PIL import ImageGrab
	from PIL import ImageFile
except ImportError:
	import sys
	sys.path.append(os.path.dirname(__file__))
	from PIL import ImageGrab
	from PIL import ImageFile


class ImagePasteCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		rel_fn = self.paste()
		if not rel_fn:
			view.run_command("paste")
			return
		for pos in view.sel():
			view.insert(edit, pos.begin(), "![](%s)" % rel_fn)
			# only the first cursor add the path
			break
			

	def paste(self):
		ImageFile.LOAD_TRUNCATED_IMAGES = True
		im = ImageGrab.grabclipboard()
		if im:
			abs_fn, rel_fn = self.get_filename()
			im.save(abs_fn,'PNG')	
			return rel_fn
		else:
			print('clipboard buffer is not image!')
			return None

	def get_filename(self):
		view = self.view
		filename = view.file_name()

		# create dir in current path with the name of current filename
		dirname, _ = os.path.splitext(filename)

		# create new image file under currentdir/filename_without_ext/filename_without_ext%d.png
		fn_without_ext = os.path.basename(dirname)
		if not os.path.lexists(dirname):
			os.mkdir(dirname)
		i = 0
		while True:
			# relative file path
			rel_filename = os.path.join("./%s/%s%d.png" % (fn_without_ext, fn_without_ext, i))
			# absolute file path
			abs_filename = os.path.join(dirname, "%s%d.png" % ( fn_without_ext, i))
			if not os.path.exists(abs_filename):
				break
			i += 1

		print("save file: " + abs_filename + "\nrel " + rel_filename)
		return abs_filename, rel_filename

