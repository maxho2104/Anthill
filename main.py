import sys
from PyQt5.QtWidgets import QApplication
from Forms.MainWindow import MainWindow

def use_PyQt5():
    app = QApplication([])
    window = MainWindow()
    window.setWindowTitle(f"МУРАВЕЙНИК")
    window.show()
    sys.exit(app.exec_())



if __name__ == '__main__':
    use_PyQt5()

