import os
import shutil
import subprocess
import sys
import urllib.request

_WIN32 = sys.platform == "win32"

if _WIN32:
	PACKAGES = [
		r"https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.8.1/PyQt5_gpl-5.8.1.zip/download",
		r"https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.1/sip-4.19.1.zip/download",
		# use system python
	]
else:
	PACKAGES = [
		r"https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.8.1/PyQt5_gpl-5.8.1.tar.gz/download",
		r"https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.1/sip-4.19.1.tar.gz/download",
		r"https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz",
	]

rewind = False

def main():
	if sys.version_info < (3, 5):
		raise NotImplementedError("Python 3.5+ is required to build TruFont.")
	if rewind:
		if os.path.exists("root"):
			print("Deleting root directory...")
			shutil.rmtree("root")
		for path in ("root", "root/src"):
			print("Creating", path, "directory...")
			os.mkdir(path)
		for url in PACKAGES:
			names = url.rsplit("/", 2)
			name = names[-1]
			if not name.endswith("z"):
				name = names[-2]
				assert name.endswith("z")
			# HACK: build-sysroot.py doesn't like .tgz
			if name.endswith(".tgz"):
				name.replace(".tgz", ".tar.gz")
			print("Fetching", name + "...")
			urllib.request.urlretrieve(url, os.path.join("root/src", name))
	print("Now calling build-sysroot.py. See ya later!")
	args = ["python3", "build-sysroot.py", "--build", "python", "pyqt5", "sip", "--sysroot=root"]
	if _WIN32:
		args.remove("python")
	subprocess.call(args)


if __name__ == "__main__":
    main()
