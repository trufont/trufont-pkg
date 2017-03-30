import glob
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

logger = logging.getLogger(__name__)

_WIN32 = sys.platform == "win32"
_MACOS = sys.platform == "darwin"
_ext = "zip" if _WIN32 else "tar.gz"
_min = (3, 6, 1) if _WIN32 else (3, 5)
_make = "nmake" if _WIN32 else "make"

PACKAGES = [
    r"https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.8.1/PyQt5_gpl-5.8.1.%s/download" % _ext,
    r"https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.1/sip-4.19.1.%s/download" % _ext,
    # use system python
]
if not _WIN32:
    PACKAGES.append(r"https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz")

rewind = rewindSysroot = rewindModules = True


def main():
    # barriers
    if not sys.maxsize > 2**32:
        raise NotImplementedError("A 64-bit Python build is required to build TruFont.")
    if sys.version_info < _min:
        raise NotImplementedError("Python {}+ is required to build TruFont.".format(".".join(str(n) for n in _min)))
    try:
        import pyqtdeploy
    except ImportError:
        raise NotImplementedError("pyqtdeploy is required to build TruFont.")
    qmake = shutil.which("qmake")
    if qmake is None or not os.path.exists(qmake):
        # TODO: we could build as part of this script
        raise NotImplementedError("qmake is required to build TruFont. Add Qt bin/ directory to PATH!")
    version = subprocess.check_output([qmake, "-v"])
    if b"Qt version 5.8" not in version:
        raise NotImplementedError("Qt 5.8 is required to build TruFont.")
    make = shutil.which(_make)
    if make is None or not os.path.exists(make):
        raise NotImplementedError(_make+" is required to build TruFont.")
    # download build libs
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
                assert name.endswith("z") or name.endswith("zip")
            # HACK: build-sysroot.py doesn't like .tgz
            if name.endswith(".tgz"):
                name = name.replace(".tgz", ".tar.gz")
            logger.info("Fetching %s…", name)
            urllib.request.urlretrieve(url, os.path.join("root/src", name))
    # build the sysroot
    if rewindSysroot:
        logger.info("Now calling build-sysroot.py. See ya later!")
        args = [sys.executable, "build-sysroot.py", "--build", "python", "pyqt5", "sip", "--enable-dynamic-loading", "--sysroot=root"]
        if _WIN32:
            args.remove("--enable-dynamic-loading")
            args.append("--use-system-python=3.6")
        subprocess.check_call(args)
    sysroot = os.path.join(os.getcwd(), "root")
    targetPython = os.path.join(sysroot, "bin", "python" + ".exe" if _WIN32 else "")
    assert os.path.exists(targetPython)
    # download modules with the interpreter we built
    if rewindModules:
        if os.path.exists("modules"):
            logger.info("Deleting modules directory…")
            shutil.rmtree("modules")
        logger.info("Creating modules directory…")
        os.mkdir("modules")
        subprocess.check_call([targetPython, "-m", "ensurepip"])
        with open("trufont/requirements.txt") as requirements:
            for req in requirements.readlines():
                if req.startswith("pyqt5"):
                    continue
                subprocess.check_call([targetPython, "-m", "pip", "install", "--target", "modules", req])
    # run pyqtdeploy
    logger.info("Now running pyqtdeploy. Later holmes!")
    env = dict(os.environ)
    env["SYSROOT"] = sysroot
    subprocess.check_call(["pyqtdeploycli", "--verbose", "--output", "dist", "--project", "TruFont.pdy", "build"], env=env)
    # finish with qmake and make
    os.chdir("dist")
    logger.info("Now running qmake. We’re getting close!")
    subprocess.check_call(["qmake"])
    logger.info("Now running %s. Hang on…", _make)
    subprocess.check_call([_make])
    os.chdir("..")
    if not (_WIN32 or _MACOS):
        # bundle
        logger.info("Making a zip file…")
        pyclipper = glob.glob("modules/pyclipper*.so")  # TODO: DLL
        if os.path.exists("TruFont.zip"):
            logger.info("Deleting existing TruFont.zip…")
            os.remove("TruFont.zip")
        with zipfile.ZipFile("TruFont.zip", 'w') as archive:
            archive.write("dist/TruFont", arcname="TruFont.run")
            if pyclipper:
                archive.write(pyclipper[0], arcname="pyclipper.so")
        logger.info("DONE!")


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
