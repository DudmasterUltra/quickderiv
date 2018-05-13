import cx_Freeze, os

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

cx_Freeze.setup(
    name="quickderiv",
    options={"build_exe": {"packages": ["pygame"],
                           "include_files": ["bad.wav",
                                             "blood-dragon-theme.mp3",
                                             "discodeckchrome.ttf",
                                             "quickderiv-side-gradient.png",
                                             "quickderiv-title.png",
                                             "quickderiv-title-gradient.png",
                                             "select.wav",
                                             "zap.wav"]}},
    description="Calculus game by Rory Eckel",
    version="1.0",
    executables = [cx_Freeze.Executable("__main__.py")]
    )
