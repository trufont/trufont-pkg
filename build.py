import logging
import os
import shutil
import subprocess
import sys
import urllib.request

logger = logging.getLogger(__name__)

_WIN32 = sys.platform == "win32"
_ext = "zip" if _WIN32 else "tar.gz"
_min = (3, 6, 1) if _WIN32 else (3, 5)
_suffix = "" if _WIN32 else "3"

PACKAGES = [
	r"https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.8.1/PyQt5_gpl-5.8.1.%s/download" % _ext,
	r"https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.1/sip-4.19.1.%s/download" % _ext,
	# use system python
]
if not _WIN32:
	PACKAGES.append(r"https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz")

rewind = False
rewindModules = False

def main():
	# barriers
	if not sys.maxsize > 2**32:
		raise NotImplementedError("A 64-bit Python build is required to build TruFont.")
	if sys.version_info < _min:
		raise NotImplementedError("Python {}+ is required to build TruFont.".format(".".join(_min)))
	try:
		import pyqtdeploy
	except ImportError:
		raise NotImplementedError("pyqtdeploy is required to build TruFont.")
	qmake = shutil.which("qmake")
	if qmake is None:
		# TODO: we could build as part of this script
		raise NotImplementedError("qmake is required to build TruFont. Add Qt bin/ directory to PATH!")
	version = subprocess.check_output([qmake, "-v"])
	if b"Qt version 5.8" not in version:
		raise NotImplementedError("Qt 5.8 is required to build TruFont.")
	# go
	if rewind:
		if os.path.exists("root"):
			logger.info("Deleting root directory…")
			shutil.rmtree("root")
		for path in ("root", "root/src"):
			logger.info("Creating %s directory…", path)
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
			logger.info("Fetching %s…", name)
			urllib.request.urlretrieve(url, os.path.join("root/src", name))
	logger.info("Now calling build-sysroot.py. See ya later!")
	args = ["python"+_suffix, "build-sysroot.py", "--build", "python", "pyqt5", "sip", "--sysroot=root"]
	if _WIN32:
		args.remove("python")
		args.append("--use-system-python=3.6")
	subprocess.call(args)
	logger.info("Now running pyqtdeploy. Later holmes!")
	if rewindModules:
		if os.path.exists("modules"):
			logger.info("Deleting modules directory…")
			shutil.rmtree("modules")
		logger.info("Creating modules directory…")
		os.mkdir("modules")
		subprocess.call(["pip"+_suffix, "download"])
		with open("trufont/requirements.txt") as requirements:
			for req in requirements.lines():
				if req.beginswith("pyqt5"):
					continue
				logger.info("Fetching %s (%s)…", *req.split("=="))
				subprocess.call(["pip", "download", "--dest", "modules", req])
	subprocess.call(["pyqtdeploycli", "--verbose", "--output", "dist", "--project", "TruFont.pdy", "--sysroot=root", "build"])
	logger.info("Now running qmake. Almost there!")
	os.chdir("path")
	subprocess.call(["qmake"])


if __name__ == "__main__":
	main()
