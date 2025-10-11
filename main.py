import pandas as pd

import os
import sys
import tempfile
from io import BytesIO
import json
from PIL.ImageQt import QPixmap

# from reportlab.lib.units import toLength

import logic
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QToolBar,
                               QHBoxLayout, QSplitter, QLineEdit, QCheckBox, QButtonGroup,
                               QPushButton, QScrollArea, QGridLayout, QFileDialog, QSlider,
                               QDialog, QColorDialog, QDialogButtonBox, QPlainTextEdit, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView



class IssueWindow(QDialog):
    def __init__(self, d, parent=None):
        super().__init__(parent)

        self.setMinimumSize(700, 500)
        self.d3 = d


        label = QLabel("Опишите, пожалуйста проблему")
        self.te = QPlainTextEdit("Разраб дурачок ...")
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.te)
        label2 = QLabel("После сохранения отправьте файл мне в телеграм @barnianK")
        label3 = QLabel("Сформированный отчёт содержит данные лабораторной работы, а также версию системы и настройки")
        layout.addWidget(label2)
        layout.addWidget(label3)


        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        self.d3['tx'] = self.te.toPlainText()
        self.d3['os'] = os.name
        return self.d3


class InstructionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Инструкция")
        self.resize(600, 500)

        main_layout = QVBoxLayout(self)

        image_label = QLabel()
        pixmap = QPixmap(logic.resource_path("primer.png"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(400, 300,
                                          Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(image_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)

        text_label = QLabel("Данная программа может строить графики различных типов, по точкам и погрешностям, которые вы вносите в таблицу excel в особым образом. Ниже вы видите пример того, как должна выглядеть таблица, чтобы по ней можно было построить график. В столбцы X и Y вносятся соответствующие координаты точек. В столбцы dX и dY погрешности для каждой точки по двум осям. Отдельно, в клетке под degX(degY) вносится показатель степени 10, на которую необходимо домножить вашу величину и её погрешность. Если выносить степень нет необходимости, напишите туда 0. Степень для величины X и её погрешности dX, может отличаться от величины Y и её погрешности dy. Пожалуйста, используйте только целые числа для показателей степени. Все точки при выборе обработки сплайном или ломаной (градуировочный) будут отсортированы по возрастанию x параметра. Если вы используете другой тип графика, то это не критично. Для начала работы, нажмите «Загрузить результаты», выберете файл excel по которому будете строить график. В программе могут встречаться баги/неточности, если вы их увидели нажмите «сообщить об ошибке», сформированный отчет отправьте по указанному адресу. Я буду очень рад вашим предложениям, или сообщениям об ошибках!")
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(text_label)

        scroll_area.setWidget(text_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)


class SettingsWindow(QDialog):
    def __init__(self, oldconf, parent=None):
        super().__init__(parent)
        self.chosen_size = oldconf['size']
        self.setWindowTitle("setting")
        self.ttff = oldconf['font']
        self.color = oldconf['color']
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout()
        label1 = QLabel("Настройки миллиметровки")
        label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout1 = QHBoxLayout()
        label2 = QLabel("Цвет миллиметровки в RGB")
        but = QPushButton("Сменить цвет")
        but.clicked.connect(self.colorpicker)
        layout1.addWidget(label2)
        layout1.addWidget(but)
        layout2 = QHBoxLayout()
        label3 = QLabel("Прозрачность графика, осей, цифр")
        self.inp4 = QSlider(Qt.Orientation.Horizontal)
        self.inp4.setRange(0,100)
        self.inp4.setValue(oldconf['opacity'])
        layout2.addWidget(label3)
        layout2.addWidget(self.inp4)
        layout.addLayout(layout1)
        layout.addLayout(layout2)

        layout3 = QHBoxLayout()

        processing_label = QLabel("тип шрифта:")
        layout3.addWidget(processing_label)
        layout_proc = QHBoxLayout()
        processing_options = [
            "DejaVuSans",
            "DejaVuSans-Bold",
        ]



        self.processing_group = QButtonGroup(self)
        self.processing_group.setExclusive(True)  # Делаем чекбоксы взаимоисключающими

        self.processing_checks = []
        for option_text in processing_options:
            checkbox = QCheckBox(option_text)
            self.processing_group.addButton(checkbox)
            layout_proc.addWidget(checkbox)
            self.processing_checks.append(checkbox)
            if option_text==oldconf['font']:
                checkbox.setChecked(True)
        self.processing_group.buttonClicked.connect(self.choose_font)
        layout3.addLayout(layout_proc)

        layout.addLayout(layout3)
        self.checkbox_size_mm = QCheckBox("Уменьшить область отрисовки миллиметровки")
        self.checkbox_size_mm.clicked.connect(self.choose_size)
        layout.addWidget(self.checkbox_size_mm)





        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return {'color': self.color,
                'opacity': self.inp4.value(),
                'font': self.ttff,
                'size': self.chosen_size
                }

    def choose_font(self, ch):
        self.ttff = ch.text()

    def choose_size(self, ch):
        self.chosen_size = ch

    def colorpicker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color[0] = color.red()
            self.color[1] = color.green()
            self.color[2] = color.blue()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.checkbox5 = None
        self.checkbox6 = None
        self.checkbox7 = None
        self.checkbox8 = None
        self.nax_x = None
        self.nax_y = None
        self.ddraw_y = None
        self.ddraw_x = None
        self.pdf_view = None
        self.pdf_document = None
        self.processing_checks = None
        self.processing_group = None
        self.line_edit4 = None
        self.line_edit3 = None
        self.line_edit2 = None
        self.line_edit1 = None
        self.checkbox4 = None
        self.checkbox3 = None
        self.checkbox2 = None
        self.checkbox1 = None
        self.chart_title_input = None
        self.splitter = None
        self.conf = {
            'color': [153, 193, 241],
            'opacity': 0.0,
            'font': 'DejaVuSans',
            'size': 0,
        }
        # self.color = [0.6, 0.6, 0.6]
        self.temp_pdf_path = None
        self.current_pdf_buffer = ""
        self.results = ""
        self.type = ""
        self.x_errors = 0
        self.y_errors = 0
        self.ed_1 = ""
        self.ed_2 = ""
        self.q_1 = ""
        self.q_2 = ""
        self.graph_title = ""
        self.label_axes = 0
        self.x_multiplier = 0
        self.y_multiplier = 0
        self.connect_lines = 0
        self.orientation = 0
        self.setWindowTitle("OrlovKM inc. - Laboratory Assistant")
        self.setGeometry(100, 100, 1200, 800)
        self.second_window = None
        self.setup_toolbar()
        self.setup_central_widget()


    def setup_toolbar(self):
        # Создание панели инструментов
        toolbar = QToolBar("My Toolbar")
        self.addToolBar(toolbar)

        # Увеличение высоты через размер иконок
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMinimumHeight(40)  # Удвоенная высота

        # Настройка отступов и расстояний
        toolbar.layout().setContentsMargins(25, 10, 15, 10)
        toolbar.layout().setSpacing(20)  # Увеличенное расстояние между элементами

        # Добавление действий
        action1 = QAction("Сохранить в PDF", self)
        action2 = QAction("Загрузить результаты", self)

        action3 = QAction("Настройки", self)
        action4 = QAction("Инструкция", self)
        action5 = QAction("Сообщить об ошибке", self)

        action1.triggered.connect(self.save_pdf)
        action2.triggered.connect(self.get_excel)
        action3.triggered.connect(self.settings)
        action4.triggered.connect(self.instruction)
        action5.triggered.connect(self.report_issue)

        toolbar.addAction(action1)
        toolbar.addAction(action2)
        toolbar.addAction(action3)
        toolbar.addAction(action4)
        toolbar.addAction(action5)


        toolbar.setStyleSheet("QToolButton { padding: 10px; }")



    def setup_central_widget(self):
        # Создаем центральный виджет и основной layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Разделитель для рабочей области (60/40):cite[3]
        self.splitter = QSplitter(Qt.Orientation.Horizontal)


        # Левая панель (60%)
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Поле "Введите название графика"
        layout_naming = QHBoxLayout()
        chart_title_label = QLabel("Введите название графика:")
        self.chart_title_input = QLineEdit()
        layout_naming.addWidget(chart_title_label)
        layout_naming.addWidget(self.chart_title_input)
        left_layout.addLayout(layout_naming)
        grid_layout = QGridLayout()

        switch_options = [
            "Вертикальная ориентация",
            "Рисовать погрешности по оси x?",
            "Рисовать погрешности по оси y?",
            "Подписывать величину и степень осей?",
            "Не рисовать ось X",
            "Не рисовать ось Y",
            "Не подписывать значения на оси X",
            "Не подписывать значения на оси Y"
        ]

        self.checkbox1 = QCheckBox(switch_options[0])
        self.checkbox2 = QCheckBox(switch_options[1])
        self.checkbox3 = QCheckBox(switch_options[2])
        self.checkbox4 = QCheckBox(switch_options[3])
        self.checkbox5 = QCheckBox(switch_options[4])
        self.checkbox6 = QCheckBox(switch_options[5])
        self.checkbox7 = QCheckBox(switch_options[6])
        self.checkbox8 = QCheckBox(switch_options[7])
        grid_layout.addWidget(self.checkbox1, 0, 0)
        grid_layout.addWidget(self.checkbox2, 0, 1)
        grid_layout.addWidget(self.checkbox3, 1, 0)
        grid_layout.addWidget(self.checkbox4, 1, 1)
        grid_layout.addWidget(self.checkbox5, 2, 0)
        grid_layout.addWidget(self.checkbox6, 2, 1)
        grid_layout.addWidget(self.checkbox7, 3, 0)
        grid_layout.addWidget(self.checkbox8, 3, 1)



        self.checkbox1.stateChanged.connect(self.vert_o)
        self.checkbox2.stateChanged.connect(self.x_er)
        self.checkbox3.stateChanged.connect(self.y_er)
        self.checkbox4.stateChanged.connect(self.label_axis)
        self.checkbox5.stateChanged.connect(self.dont_draw_x)
        self.checkbox6.stateChanged.connect(self.dont_draw_y)
        self.checkbox7.stateChanged.connect(self.num_ax_x)
        self.checkbox8.stateChanged.connect(self.num_ax_y)

        left_layout.addLayout(grid_layout)

        label1 = QLabel("Еденицы измерения для оси x")
        label2 = QLabel("Еденицы измерения для оси y")
        label3 = QLabel("Физическая величина для оси x")
        label4 = QLabel("Физическая величина для оси y")
        self.line_edit1 = QLineEdit()
        self.line_edit2 = QLineEdit()
        self.line_edit3 = QLineEdit()
        self.line_edit4 = QLineEdit()
        layout_p1 = QHBoxLayout()
        layout_p2 = QHBoxLayout()
        layout_p3 = QHBoxLayout()
        layout_p4 = QHBoxLayout()
        layout_p1.addWidget(label1)
        layout_p1.addWidget(self.line_edit1)
        layout_p2.addWidget(label2)
        layout_p2.addWidget(self.line_edit2)
        layout_p3.addWidget(label3)
        layout_p3.addWidget(self.line_edit3)
        layout_p4.addWidget(label4)
        layout_p4.addWidget(self.line_edit4)
        grid_p = QGridLayout()
        grid_p.addLayout(layout_p1, 0, 0)
        grid_p.addLayout(layout_p2, 0, 1)
        grid_p.addLayout(layout_p3, 1, 0)
        grid_p.addLayout(layout_p4, 1, 1)
        left_layout.addLayout(grid_p)

        # Тип обработки (взаимоисключающие чекбоксы)
        processing_label = QLabel("тип обработки:")
        left_layout.addWidget(processing_label)
        layout_proc = QHBoxLayout()
        processing_options = [
            "Градуировочный",
            "Наименьшие квадраты",
            "Кубический сплайн",
            "Нет"
        ]

        self.processing_group = QButtonGroup(self)
        self.processing_group.setExclusive(True)  # Делаем чекбоксы взаимоисключающими

        self.processing_checks = []
        for option_text in processing_options:
            checkbox = QCheckBox(option_text)
            self.processing_group.addButton(checkbox)
            layout_proc.addWidget(checkbox)
            self.processing_checks.append(checkbox)
        # Подключаем сигнал buttonClicked от QButtonGroup к своей функции
        self.processing_group.buttonClicked.connect(self.on_processing_checkbox_clicked)
        left_layout.addLayout(layout_proc)

        # Кнопка "Сохранить"
        but_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_pdf)

        # Кнопка "Построить"
        plot_button = QPushButton("Построить")
        plot_button.clicked.connect(self.preview_pdf)
        but_layout.addWidget(plot_button)
        but_layout.addWidget(save_button)
        left_layout.addLayout(but_layout)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_layout.setSpacing(50)
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_document)


        # Добавляем панели в разделитель
        left_widget.setLayout(left_layout)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.pdf_view)



        main_layout.addWidget(self.splitter)

    def showEvent(self, event):
        """Вызывается при показе окна"""
        super().showEvent(event)  # Важно: вызываем родительский метод


        self.splitter.setSizes([int(self.splitter.width() * 0.4), int(self.splitter.width() * 0.6)])






    def vert_o(self, ch):
        self.orientation = ch

    def x_er(self, ch):
        self.x_errors = ch

    def y_er(self, ch):
        self.y_errors = ch

    def label_axis(self, ch):
        self.label_axes = ch
    def dont_draw_x(self, ch):
        self.ddraw_x = ch
    def dont_draw_y(self, ch):
        self.ddraw_y = ch
    def num_ax_x(self, ch):
        self.nax_x = ch
    def num_ax_y(self, ch):
        self.nax_y = ch

    def on_processing_checkbox_clicked(self, checkbox):
        self.type = checkbox.text()

    def generate_pdf(self):
        """Генерирует PDF и возвращает буфер с данными."""
        buffer = BytesIO()

        if self.results == "":
            self.get_excel()
        pdf = logic.LogicaPdf({
            'orientation': self.orientation,
            'connect_lines': self.connect_lines,
            'y_multiplier': self.y_multiplier,
            'x_multiplier': self.x_multiplier,
            'y_errors': self.y_errors,
            'x_errors': self.x_errors,
            'num_X': self.nax_x,
            'num_Y': self.nax_y,
            'draw_X': self.ddraw_x,
            'draw_Y': self.ddraw_y,
            'label_axes': self.label_axes,
            'graph_title': self.chart_title_input.text(),
            "ed_2": self.line_edit1.text(),
            "ed_1": self.line_edit2.text(),
            "q_2": self.line_edit3.text(),
            "q_1": self.line_edit4.text(),
            "type": self.type, }, buffer, self.conf, self.parser(self.results))


        buffer.seek(0)  # Важно: перемотать буфер в начало

        return buffer

    def preview_pdf(self):
        """Генерирует PDF и показывает его в интерфейсе."""
        # Генерируем PDF и сохраняем буфер
        self.current_pdf_buffer = self.generate_pdf()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            self.temp_pdf_path = tmp_file.name  # Сохраняем путь
            tmp_file.write(self.current_pdf_buffer.getvalue())


        self.pdf_document.load(self.temp_pdf_path)

    def save_pdf(self):
        """Сохраняет текущий PDF в постоянный файл."""
        if self.current_pdf_buffer is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF", self.chart_title_input.text(), "PDF Files (*.pdf)")

        if file_path:
            # Сбрасываем позицию в буфере и записываем в файл
            self.current_pdf_buffer.seek(0)
            with open(file_path, 'wb') as f:
                f.write(self.current_pdf_buffer.getvalue())



    def get_excel(self):

        file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить .xlsx", "", "Excel Files (*.xlsx)")
        self.results = file_path



    def settings(self):
        """Метод для открытия второго окна"""
        self.second_window = SettingsWindow(self.conf)  # self в качестве parent

        # Запускаем диалог и проверяем результат
        if self.second_window.exec() == QDialog.DialogCode.Accepted:
            # Получаем данные из второго окна
            self.conf = self.second_window.get_data()

        # После закрытия окна, освобождаем ссылку
        self.second_window = None

    def instruction(self):
        self.second_window = InstructionWindow(self)  # self в качестве parent

        # Запускаем диалог и проверяем результат
        if self.second_window.exec() == QDialog.DialogCode.Accepted:
            pass

        # После закрытия окна, освобождаем ссылку
        self.second_window = None

    def report_issue(self):
        if self.results=='':
            self.get_excel()
        a, b, h, j, m, n = self.parser(self.results)
        megadict = {"degx": m,
                    "degy": n,
                    }

        megadict.update({
                'orientation': self.orientation,
                'connect_lines': self.connect_lines,
                'y_multiplier': self.y_multiplier,
                'x_multiplier': self.x_multiplier,
                'y_errors': self.y_errors,
                'x_errors': self.x_errors,
                'num_X': self.nax_x,
                'num_Y': self.nax_y,
                'draw_X': self.ddraw_x,
                'draw_Y': self.ddraw_y,
                'label_axes': self.label_axes,
                'graph_title': self.chart_title_input.text(),
                "ed_1": self.line_edit1.text(),
                "ed_2": self.line_edit2.text(),
                "q_1": self.line_edit3.text(),
                "q_2": self.line_edit4.text(),
                "type": self.type,
                'tx': '',
                'os':'',
                "X":a,
                "Y": b,
                "dX": h,
                "dY": j,
            })
        megadict.update(self.conf)
        self.second_window = IssueWindow(megadict, parent=self)
        if self.second_window.exec() == QDialog.DialogCode.Accepted:
            issue = self.second_window.get_data()
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить Json", 'issues_report',
                                                       "Json Files (*.json)")

            if file_path:
                # Сбрасываем позицию в буфере и записываем в файл
                # self.current_pdf_buffer.seek(0)
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(issue, file, ensure_ascii=False, indent=4)

    def parser(self, filepath: str):
        df = pd.read_excel(filepath)

        dict_list = df.to_dict(orient='records')
        dy, dx, y, x = [], [], [], []

        degx = dict_list[0].get("degX", 0)
        degy = dict_list[0].get("degY", 0)

        try:
            for i in dict_list:

                    x.append(i["X"])
                    y.append(i["Y"])
                    dx.append(i["dX"])
                    dy.append(i["dY"])
        except KeyError:
            self.showWarMes()
            x = [1, 2, 3, 4, 5]
            y = [2, 4, 6, 8, 10]
            dx = [0.1, 0.2, 0.3, 0.4, 0.5]
            dy = [0.1, 0.2, 0.3, 0.4, 0.5]


        return [x, y, dx, dy, int(round(degx)), int(round(degy))]

    def showWarMes(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Предупреждение")
        msg_box.setIcon(QMessageBox.Icon.Warning)  # Иконка предупреждения
        msg_box.setText(
            "Произошла ошибка при обработке вашего Excel, пожалуйста проверьте соответствие шаблону и попробуйте снова. Сейчас введены случайные значения")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)  # Кнопка "OK"
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


