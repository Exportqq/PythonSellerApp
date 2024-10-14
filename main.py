from PyQt6.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 400, 600)
        self.setWindowTitle('Order Management System')

        self.menu = self.menuBar()
        file_menu = self.menu.addMenu('File')

        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open Order', '', 'Order Files (*.xlsx)')
        if filename:
            self.load_file(filename)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save Order', '', 'Order Files (*.xlsx)')
        if filename:
            self.save_file(filename)

    def load_file(self, filename):
        # Загружаем файл в таблицу данных
        try:
            data = pd.read_excel(filename)
            # Обновляем интерфейс
            self.update_ui(data)
        except Exception as e:
            print(f'Error: {e}')

    def save_file(self, filename):
        # Сохраняем таблицу данных в файл
        try:
            data = self.get_data()
            data.to_excel(filename, index=False)
        except Exception as e:
            print(f'Error: {e}')

    def get_data(self):
        # Получаем данные из интерфейса
        return data

    def update_ui(self, data):
        # Обновляем интерфейс
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())