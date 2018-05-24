import sublime
import sublime_plugin
import os
import sys
import re
import subprocess
import shutil
from imp import reload

print(sys.getdefaultencoding())
reload(sys)
# sys.setdefaultencoding('utf-8')

if sys.platform == 'win32':
	package_file = os.path.normpath(os.path.abspath(__file__))
	package_path = os.path.dirname(package_file)
	lib_path =  os.path.join(package_path, "lib")
	if lib_path not in sys.path:
	    sys.path.append(lib_path)
	    print(sys.path)
	from PIL import ImageGrab
	from PIL import ImageFile
	from PIL import Image

class ImageCommand(object):
	def __init__(self, *args, **kwgs):
		super(ImageCommand, self).__init__(*args, **kwgs)
		self.settings = sublime.load_settings('imagepaste.sublime-settings')

		# get the image save dirname
		self.image_dir_name = self.settings.get('image_dir_name', None)
		if len(self.image_dir_name) == 0:
			self.image_dir_name = None
		print("[%d] get image_dir_name: %r"%(id(self.image_dir_name), self.image_dir_name))

	def run_command(self, cmd):
		cwd = os.path.dirname(self.view.file_name())
		print("cmd %r" % cmd)
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=os.environ)
		
		try:
		    outs, errs = proc.communicate(timeout=15)
		    print("outs %r %r" % (outs, proc))
		except Exception:
		    proc.kill()
		    outs, errs = proc.communicate()
		print("outs %r, errs %r" % (b'\n'.join(outs.split(b'\r\n')), errs))
		if errs is None or len(errs) == 0:
			return outs.decode()
		
	def get_filename(self):
		view = self.view
		filename = view.file_name()

		# create dir in current path with the name of current filename
		dirname, _ = os.path.splitext(filename)

		# create new image file under currentdir/filename_without_ext/filename_without_ext%d.png
		fn_without_ext = os.path.basename(dirname)
		if self.image_dir_name is not None:
			subdir_name = os.path.join(os.path.split(dirname)[0], self.image_dir_name)
		else:
			subdir_name = dirname
		if not os.path.lexists(subdir_name):
			os.mkdir(subdir_name)
		i = 0
		while True:
			# relative file path
			rel_filename = os.path.join("%s/%s%d.png" % (self.image_dir_name if self.image_dir_name else fn_without_ext, fn_without_ext, i))
			# absolute file path
			abs_filename = os.path.join(subdir_name, "%s%d.png" % (fn_without_ext, i))
			if not os.path.exists(abs_filename):
				break
			i += 1

		print("save file: " + abs_filename + "\nrel " + rel_filename)
		return abs_filename, rel_filename

class ImagePasteCommand(ImageCommand, sublime_plugin.TextCommand):

	def run(self, edit):
		view = self.view
		print("[%d] image_dir_name: %r"%(id(self.image_dir_name),self.image_dir_name))
		rel_fn = self.paste()

		if not rel_fn:
			view.run_command("paste")
			return
		for pos in view.sel():
			# print("scope name: %r" % (view.scope_name(pos.begin())))
			if 'text.html.markdown' in view.scope_name(pos.begin()):
				view.insert(edit, pos.begin(), "![](%s)" % rel_fn)
			else:
				view.insert(edit, pos.begin(), "%s" % rel_fn)
			# only the first cursor add the path
			break
			

	def paste(self):
		if sys.platform != 'win32':
			dirname = os.path.dirname(__file__)
			command = ['/usr/bin/python3', os.path.join(dirname, 'bin/imageutil.py'), 'save']
			abs_fn, rel_fn = self.get_filename()
			command.append(abs_fn)

			out = self.run_command(" ".join(command))
			if out and out[:4] == "save":
				return rel_fn
		else: # win32
			ImageFile.LOAD_TRUNCATED_IMAGES = True
			im = ImageGrab.grabclipboard()
			if im:
				abs_fn, rel_fn = self.get_filename()
				im.save(abs_fn,'PNG')	
				return rel_fn

		print('clipboard buffer is not image!')
		return None



class ImageGrabCommand(ImageCommand, sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		rel_fn = self.paste()
		if not rel_fn:
			view.run_command("paste")
			return
		for pos in view.sel():
			# print("scope name: %r" % (view.scope_name(pos.begin())))
			if 'text.html.markdown' in view.scope_name(pos.begin()):
				view.insert(edit, pos.begin(), "![](%s)" % rel_fn)
			else:
				view.insert(edit, pos.begin(), "%s" % rel_fn)
			# only the first cursor add the path
			break
			

	def paste(self):
		# ImageFile.LOAD_TRUNCATED_IMAGES = True
		dirname = os.path.dirname(__file__)
		command = ['/usr/bin/python3', os.path.join(dirname, 'bin/imageutil.py'), 'grab']
		abs_fn, rel_fn = self.get_filename()
		tempfile1 = "/tmp/imagepaste1.png"
		command.append(tempfile1)
		print("command: ", command)

		out = self.run_command(" ".join(command))
		if out and out[:4] == "grab":
			ret = sublime.ok_cancel_dialog("save to file?")
			print("ret %r" % ret)
			if ret:
				shutil.move(tempfile1, abs_fn)
				return rel_fn
			else:
				return None
		# im = ImageGrab.grabclipboard()
		# if im:
		# 	abs_fn, rel_fn = self.get_filename()
		# 	im.save(abs_fn,'PNG')	
		# 	return rel_fn
		else:
			print('clipboard buffer is not image!')
			return None


class ImagePreviewCommand(ImageCommand, sublime_plugin.TextCommand):
	def __init__(self, *args):
	#	self.view = view
		super(ImagePreviewCommand, self).__init__(*args)	    
		# self.phantom_set = sublime.PhantomSet(self.view)
		self.displayed = False




	def get_line(self):
		v = self.view
		rows, _ = v.rowcol(v.size())
		for row in range(rows+1):
			pt = v.text_point(row, 0)
			tp_line = v.line(pt)
			line = v.substr(tp_line)
			yield tp_line, line
		raise StopIteration

	def run(self, edit):
		print("run phantom")
		view = self.view
		dirname = os.path.dirname(__file__)
		for tp, line in self.get_line():
			m=re.search(r'!\[([^\]]*)\]\(([^)]*)\)', line)
			if m:
				name, file1 = m.group(1), m.group(2)
				message = ""
				file2 = os.path.join(os.path.dirname(view.file_name()), file1)
				# print("%s = %s" % (name, file1))
				region = tp

				command = ['/usr/bin/python3', os.path.join(dirname, 'bin/imageutil.py'), 'size']
				command.append(file2)

				out = self.run_command(" ".join(command))
				widthstr, heightstr = out.split(',')
				# with Image.open(file2) as im:
				# print("file: %s with size: %d %d" % (file1, im.width, im.height))
				message = '''<body>
				<img width="%s" height="%s" src="file://%s"></img>
				</body>''' % (widthstr, heightstr, file2)
				if len(name) == 0:
					name = file1

		# phantom = sublime.Phantom(region, messag e, sublime.LAYOUT_BLOCK)
				print("message %s" % message)
				if not self.displayed:
					self.view.add_phantom(name, region, message, sublime.LAYOUT_BLOCK)
				else:
					self.view.erase_phantoms(name)
		# self.phantom_set.update([phantom])
		# view.show_popup('<img src="file://c://msys64/home/chenyu/diary/diary/diary8.jpg">')
		self.displayed = not self.displayed

