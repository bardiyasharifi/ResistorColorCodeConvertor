import sys
from re import findall
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter, QPen, QColor, QBrush, QFont, QClipboard
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QComboBox, QRadioButton,
    QLabel, QTextEdit, QFrame, QPushButton, QFileDialog
)

colors = ["Black", "Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White"]
colors_without_black = ["Brown", "Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Gray", "White"]
multipliers = {"Black": 1, "Brown": 10, "Red": 100, "Orange": 1000, "Yellow": 10000, "Green": 10 ** 5, "Blue": 10 ** 6,
               "Violet": 10 ** 7, "Gray": 10 ** 8, "White": 10 ** 9, "Gold": 0.1, "Silver": 0.01}
reversed_multipliers = {value: key for key, value in multipliers.items()}  # To use in ohm to color code conversion
tolerances = {"Brown": 1, "Red": 2, "Orange": 3, "Yellow": 4, "Green": 0.5, "Blue": 0.25, "Violet": 0.1, "Gray": 0.05,
              "Gold": 5, "Silver": 10}
tempco = {"Brown": 100, "Red": 50, "Orange": 15, "Yellow": 25, "Blue": 10, "Violet": 5}

BODY_COLOR = "#47e2d9"
TERMINAL_COLOR = "#555d6a"
DEFAULT_BAND_COLOR = "#aeb8b1"


class RCCC(QMainWindow):

    def __init__(self):
        super().__init__()

        self.band = None

        #  Window Properties
        self.setWindowTitle("Resistor Color Code Convertor")
        self.setWindowIcon(QIcon(r"icon.ico"))
        self.setGeometry(350, 180, 800, 500)
        self.setFixedSize(800, 500)

        # Applying styles loaded from 'styles.qss'
        with open("styles.qss", "r") as styles:
            self.setStyleSheet(styles.read())

        # Creating a QLabel to show the QPixmap which will include our resistor drawing
        self.resistor_pixmap = QLabel(self)
        self.resistor_pixmap.setGeometry(300, 15, 450, 335)

        self.canvas = QPixmap(450, 350)
        self.canvas.fill(QColor("white"))

        # Creating necessary painting instances
        self.painter = QPainter(self.canvas)
        self.pen = QPen()
        self.brush = QBrush()

        QLabel("Select your conversion :", self).setGeometry(30, 20, 130, 20)

        # QRadioButtons to specify type of conversion
        self.ColorToOhmRadioButton = QRadioButton("Color code to Ohm Value", self)
        self.ColorToOhmRadioButton.setGeometry(30, 50, 160, 20)
        self.ColorToOhmRadioButton.setChecked(True)  # Default Option
        self.ColorToOhmRadioButton.toggled.connect(self.draw_resistor)
        self.ColorToOhmRadioButton.toggled.connect(self.state_one)

        self.OhmToColorRadioButton = QRadioButton("Ohm value to color code", self)
        self.OhmToColorRadioButton.setGeometry(30, 80, 160, 20)  # will be developed soon
        self.OhmToColorRadioButton.toggled.connect(self.draw_resistor)
        self.OhmToColorRadioButton.toggled.connect(self.state_two)

        self.line1 = QFrame(self)
        self.line1.setLineWidth(2)
        self.line1.setGeometry(30, 105, 220, 20)
        self.line1.setFrameShape(QFrame.Shape.HLine)

        self.label = QLabel("Result :", self)
        self.label.setGeometry(32, 118, 180, 20)

        # This QTextedit will be used for color code to ohm value conversion
        self.result = QTextEdit(self)
        self.result.setReadOnly(True)
        self.result.setGeometry(30, 140, 220, 35)

        # This QTextedit will be used for ohm value to color code conversion which is by default invisible
        self.input = QTextEdit(self)
        self.input.setGeometry(30, 140, 220, 35)
        self.input.setVisible(False)
        self.input.textChanged.connect(self.coloring_resistor)

        self.line2 = QFrame(self)
        self.line2.setLineWidth(2)
        self.line2.setGeometry(30, 170, 220, 20)
        self.line2.setFrameShape(QFrame.Shape.HLine)

        # Number of Bands QComboBox
        self.number_of_bands_str = QLabel("Select number of bands :", self)
        self.number_of_bands_str.setGeometry(32, 185, 150, 20)
        self.number_of_bands = QComboBox(self)
        self.number_of_bands.addItems(["4 Bands", "5 Bands", "6 Bands"])
        self.number_of_bands.setGeometry(30, 210, 220, 25)
        self.number_of_bands.setCurrentIndex(-1)
        self.number_of_bands.setPlaceholderText("Choose number of bands")
        self.number_of_bands.currentTextChanged.connect(self.reset_index)
        self.number_of_bands.currentTextChanged.connect(self.selected_band)

        self.line3 = QFrame(self)
        self.line3.setLineWidth(2)
        self.line3.setGeometry(30, 237, 220, 20)
        self.line3.setFrameShape(QFrame.Shape.HLine)

        # Qrect objects to draw bands easily later
        self.first_band_rect = QRect(120, 130, 13, 70)
        self.second_band_rect = QRect(155, 133, 13, 65)
        self.third_band_rect = QRect(180, 133, 13, 65)
        self.forth_band_rect = QRect(205, 133, 13, 65)
        self.fifth_band_rect = QRect(270, 133, 13, 65)
        self.sixth_band_rect = QRect(313, 130, 13, 70)

        # First band ComboBox
        self.first_band_str = QLabel("1st Digit :", self)
        self.first_band_str.setGeometry(30, 250, 105, 25)
        self.first_band = QComboBox(self)
        self.first_band.setGeometry(28, 275, 105, 25)
        self.first_band.setCurrentIndex(-1)
        self.first_band.setPlaceholderText("Select Color")
        self.first_band.currentTextChanged.connect(self.change_first_band_color)
        self.first_band.currentTextChanged.connect(self.calculate_resistance)

        # second band ComboBox
        self.second_band_str = QLabel("2nd Digit :", self)
        self.second_band_str.setGeometry(150, 250, 105, 25)
        self.second_band = QComboBox(self)
        self.second_band.setGeometry(148, 275, 105, 25)
        self.second_band.setCurrentIndex(-1)
        self.second_band.setPlaceholderText("Select Color")
        self.second_band.currentTextChanged.connect(self.change_second_band_color)
        self.second_band.currentTextChanged.connect(self.calculate_resistance)

        # Third band ComboBox
        self.third_band_str = QLabel("3rd Digit :", self)
        self.third_band_str.setGeometry(30, 300, 105, 25)
        self.third_band = QComboBox(self)
        self.third_band.setGeometry(28, 325, 105, 25)
        self.third_band.setCurrentIndex(-1)
        self.third_band.setPlaceholderText("Select Color")
        self.third_band.currentTextChanged.connect(self.change_third_band_color)
        self.third_band.currentTextChanged.connect(self.calculate_resistance)

        # Forth band ComboBox
        self.forth_band_str = QLabel("Multiplier :", self)
        self.forth_band_str.setGeometry(150, 300, 105, 25)
        self.forth_band = QComboBox(self)
        self.forth_band.setGeometry(148, 325, 105, 25)
        self.forth_band.setCurrentIndex(-1)
        self.forth_band.setPlaceholderText("Select Color")
        self.forth_band.currentTextChanged.connect(self.change_forth_band_color)
        self.forth_band.currentTextChanged.connect(self.calculate_resistance)

        # Fifth Band ComboBox
        self.fifth_band_str = QLabel("Tolerance :", self)
        self.fifth_band_str.setGeometry(30, 350, 105, 25)
        self.fifth_band = QComboBox(self)
        self.fifth_band.setGeometry(28, 375, 105, 25)
        self.fifth_band.setVisible(False)
        self.fifth_band_str.setVisible(False)
        self.fifth_band.setCurrentIndex(-1)
        self.fifth_band.setPlaceholderText("Select Color")
        self.fifth_band.currentTextChanged.connect(self.change_fifth_band_color)
        self.fifth_band.currentTextChanged.connect(self.calculate_resistance)

        # Sixth band ComboBox
        self.sixth_band_str = QLabel("Tempco :", self)
        self.sixth_band_str.setGeometry(150, 350, 105, 25)
        self.sixth_band = QComboBox(self)
        self.sixth_band.setGeometry(148, 375, 105, 25)
        self.sixth_band.setVisible(False)
        self.sixth_band_str.setVisible(False)
        self.sixth_band.setCurrentIndex(-1)
        self.sixth_band.setPlaceholderText("Select Color")
        self.sixth_band.currentTextChanged.connect(self.change_sixth_band_color)
        self.sixth_band.currentTextChanged.connect(self.calculate_resistance)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setGeometry(95, 415, 120, 25)
        self.reset_button.clicked.connect(self.reset_index)
        self.reset_button.clicked.connect(self.selected_band)

        self.copy_value_button = QPushButton("Copy value to clipboard", self)
        self.copy_value_button.setGeometry(298, 355, 150, 45)
        self.copy_value_button.clicked.connect(self.copy_value)

        self.save_button = QPushButton("Save image", self)
        self.save_button.setGeometry(450, 355, 150, 45)
        self.save_button.clicked.connect(self.save_resistor_image)

        self.copy_image_button = QPushButton("Copy image to clipboard", self)
        self.copy_image_button.setGeometry(602, 355, 150, 45)
        self.copy_image_button.clicked.connect(self.copy_image)

        self.draw_resistor()

    def draw_resistor(self):

        # Resistor terminals
        self.pen.setWidth(4)
        self.pen.setColor(QColor(TERMINAL_COLOR))

        self.brush.setColor(QColor(TERMINAL_COLOR))
        self.brush.setStyle(Qt.BrushStyle.SolidPattern)

        self.painter.setPen(self.pen)
        self.painter.setBrush(self.brush)

        self.painter.drawRect(20, 160, 80, 5)
        self.painter.drawRect(350, 160, 80, 5)

        # Resistor body
        self.pen.setColor(QColor(BODY_COLOR))
        self.brush.setColor(QColor(BODY_COLOR))
        self.painter.setPen(self.pen)
        self.painter.setBrush(self.brush)

        self.painter.drawRect(135, 133, 170, 65)
        self.painter.drawEllipse(90, 130, 75, 70)
        self.painter.drawEllipse(280, 130, 75, 70)
        self.painter.fillRect(0, 250, 450, 60, QColor("white"))
        self.resistor_pixmap.setPixmap(self.canvas)

    def selected_band(self):

        self.band = self.number_of_bands.currentText()
        if self.band == "4 Bands":
            self.first_band.clear()
            self.first_band.addItems(colors_without_black)

            self.second_band.clear()
            self.second_band.addItems(colors)

            self.third_band.clear()
            self.third_band.addItems(multipliers)
            self.third_band_str.setText("Multiplier :")

            for i in range(0, 12):
                self.third_band.setItemIcon(i, QIcon(f"icons/{list(multipliers)[i]}"))

            self.forth_band.clear()
            self.forth_band.addItems(tolerances)
            self.forth_band_str.setText("Tolerance :")
            for i in range(0, 10):
                self.forth_band.setItemIcon(i, QIcon(f"icons/{list(tolerances)[i]}"))

            self.fifth_band.setVisible(False)
            self.fifth_band_str.setVisible(False)
            self.sixth_band.setVisible(False)
            self.sixth_band_str.setVisible(False)

            # drawing 4 bands
            self.painter.fillRect(self.second_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.third_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.forth_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.fifth_band_rect, QColor(DEFAULT_BAND_COLOR))

            # Hiding 5th and 6th band
            self.painter.fillRect(self.first_band_rect, QColor(BODY_COLOR))
            self.painter.fillRect(self.sixth_band_rect, QColor(BODY_COLOR))

            self.resistor_pixmap.setPixmap(self.canvas)

        elif self.band == "5 Bands":
            self.first_band.clear()
            self.first_band.addItems(colors_without_black)

            self.second_band.clear()
            self.second_band.addItems(colors)

            self.third_band.clear()
            self.third_band.addItems(colors)
            self.third_band_str.setText("3rd Digit :")
            for i in range(0, 10):
                self.third_band.setItemIcon(i, QIcon(f"icons/{colors[i]}"))

            self.forth_band.clear()
            self.forth_band.addItems(multipliers)
            self.forth_band_str.setText("Multiplier :")
            for i in range(0, 12):
                self.forth_band.setItemIcon(i, QIcon(f"icons/{list(multipliers)[i]}"))

            self.fifth_band.clear()
            self.fifth_band.addItems(tolerances)
            self.fifth_band_str.setText("Tolerance :")
            for i in range(0, 10):
                self.fifth_band.setItemIcon(i, QIcon(f"icons/{list(tolerances)[i]}"))

            self.fifth_band.setVisible(True)
            self.fifth_band_str.setVisible(True)
            self.sixth_band.setVisible(False)
            self.sixth_band_str.setVisible(False)

            self.painter.fillRect(self.first_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.second_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.third_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.forth_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.fifth_band_rect, QColor(DEFAULT_BAND_COLOR))

            # Hiding 6th band
            self.painter.fillRect(self.sixth_band_rect, QColor(BODY_COLOR))

            self.resistor_pixmap.setPixmap(self.canvas)

        elif self.band == "6 Bands":
            self.first_band.clear()
            self.first_band.addItems(colors_without_black)

            self.second_band.clear()
            self.second_band.addItems(colors)

            self.third_band.clear()
            self.third_band.addItems(colors)
            self.third_band_str.setText("3rd Digit :")
            for i in range(0, 10):
                self.third_band.setItemIcon(i, QIcon(f"icons/{colors[i]}"))

            self.forth_band.clear()
            self.forth_band.addItems(multipliers)
            self.forth_band_str.setText("Multiplier :")
            for i in range(0, 12):
                self.forth_band.setItemIcon(i, QIcon(f"icons/{list(multipliers)[i]}"))

            self.fifth_band.clear()
            self.fifth_band.addItems(tolerances)
            self.fifth_band_str.setText("Tolerance :")

            self.sixth_band.clear()
            self.sixth_band.addItems(tempco)
            self.sixth_band_str.setText("Tempco :")

            self.fifth_band.setVisible(True)
            self.fifth_band_str.setVisible(True)
            self.sixth_band.setVisible(True)
            self.sixth_band_str.setVisible(True)

            # Drawing all bands
            self.painter.fillRect(self.first_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.second_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.third_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.forth_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.fifth_band_rect, QColor(DEFAULT_BAND_COLOR))
            self.painter.fillRect(self.sixth_band_rect, QColor(DEFAULT_BAND_COLOR))

            self.resistor_pixmap.setPixmap(self.canvas)
            
        for i in range(0, 9):
            self.first_band.setItemIcon(i, QIcon(f"icons/{colors_without_black[i]}"))

        for i in range(0, 10):
            self.second_band.setItemIcon(i, QIcon(f"icons/{colors[i]}"))

        for i in range(0, 10):
            self.fifth_band.setItemIcon(i, QIcon(f"icons/{list(tolerances)[i]}"))

        for i in range(0, 6):
            self.sixth_band.setItemIcon(i, QIcon(f"icons/{list(tempco)[i]}"))

    def state_one(self):  # For color code to ohm conversion
        self.label.setText("Result :")
        self.input.setVisible(False)
        self.result.setVisible(True)
        self.result.setReadOnly(True)
        self.result.clear()
        self.line2.setVisible(True)
        self.line3.setVisible(True)
        self.number_of_bands.setCurrentIndex(-1)
        self.number_of_bands.setVisible(True)
        self.number_of_bands_str.setVisible(True)
        self.first_band_str.setVisible(True)
        self.first_band.setVisible(True)
        self.second_band_str.setVisible(True)
        self.second_band.setVisible(True)
        self.third_band_str.setVisible(True)
        self.third_band.setVisible(True)
        self.forth_band_str.setVisible(True)
        self.forth_band.setVisible(True)
        self.fifth_band_str.setVisible(True)
        self.fifth_band.setVisible(True)
        self.sixth_band_str.setVisible(True)
        self.sixth_band.setVisible(True)
        self.reset_button.setVisible(True)

    def state_two(self):  # For Ohm to color code conversion
        self.label.setText("Enter resistance value (in Ohms): ")
        self.result.setVisible(False)
        self.input.setVisible(True)
        self.input.clear()
        self.line2.setVisible(False)
        self.line3.setVisible(False)
        self.number_of_bands.setCurrentIndex(-1)
        self.number_of_bands.setVisible(False)
        self.number_of_bands_str.setVisible(False)
        self.first_band_str.setVisible(False)
        self.first_band.setVisible(False)
        self.second_band_str.setVisible(False)
        self.second_band.setVisible(False)
        self.third_band_str.setVisible(False)
        self.third_band.setVisible(False)
        self.forth_band_str.setVisible(False)
        self.forth_band.setVisible(False)
        self.fifth_band_str.setVisible(False)
        self.fifth_band.setVisible(False)
        self.sixth_band_str.setVisible(False)
        self.sixth_band.setVisible(False)
        self.reset_button.setVisible(False)

    def reset_index(self):
        # Reset QComboBoxes and result when number of bands has changed
        self.first_band.setCurrentIndex(-1)
        self.first_band.clear()
        self.second_band.setCurrentIndex(-1)
        self.second_band.clear()
        self.third_band.setCurrentIndex(-1)
        self.third_band.clear()
        self.forth_band.setCurrentIndex(-1)
        self.forth_band.clear()
        self.fifth_band.setCurrentIndex(-1)
        self.fifth_band.clear()
        self.sixth_band.setCurrentIndex(-1)
        self.sixth_band.clear()
        self.result.clear()
        self.painter.fillRect(0, 250, 450, 60, QColor("white"))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_first_band_color(self, color=DEFAULT_BAND_COLOR):
        if self.band == "4 Bands":
            self.painter.fillRect(self.second_band_rect, QColor(color))
        else:
            self.painter.fillRect(self.first_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_second_band_color(self, color=DEFAULT_BAND_COLOR):
        if self.band == "4 Bands":
            self.painter.fillRect(self.third_band_rect, QColor(color))
        else:
            self.painter.fillRect(self.second_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_third_band_color(self, color=DEFAULT_BAND_COLOR):
        if self.band == "4 Bands":
            self.painter.fillRect(self.forth_band_rect, QColor(color))
        else:
            self.painter.fillRect(self.third_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_forth_band_color(self, color=DEFAULT_BAND_COLOR):
        if self.band == "4 Bands":
            self.painter.fillRect(self.fifth_band_rect, QColor(color))
        else:
            self.painter.fillRect(self.forth_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_fifth_band_color(self, color=DEFAULT_BAND_COLOR):
        self.painter.fillRect(self.fifth_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def change_sixth_band_color(self, color=DEFAULT_BAND_COLOR):
        self.painter.fillRect(self.sixth_band_rect, QColor(color))
        self.resistor_pixmap.setPixmap(self.canvas)

    def calculate_resistance(self):
        self.result.clear()
        self.pen.setColor(QColor("Black"))
        self.painter.setPen(self.pen)
        self.painter.setFont(QFont("bahnschrift", 15))
        if self.band == "4 Bands":
            try:
                digits = int("{0}{1}".format(colors_without_black.index(self.first_band.currentText()) + 1,
                                             colors.index(self.second_band.currentText())))

                digits *= multipliers.get(self.third_band.currentText())

                res = str(digits) + " Ω ± " + str(tolerances.get(self.forth_band.currentText())) + "%"

                self.result.setPlainText(res)
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(100, 250, 250, 300, Qt.AlignHCenter, res)
                self.resistor_pixmap.setPixmap(self.canvas)

            except (ValueError, TypeError):
                self.result.setPlainText("Some Colors are not specified")
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(0, 250, 450, 60, Qt.AlignHCenter, "Some Colors are not specified")
                self.resistor_pixmap.setPixmap(self.canvas)

        elif self.band == "5 Bands":
            try:
                digits = int("{0}{1}{2}".format(colors_without_black.index(self.first_band.currentText()) + 1,
                                                colors.index(self.second_band.currentText()),
                                                colors.index(self.third_band.currentText())))
                digits *= multipliers.get(self.forth_band.currentText())
                res = str(digits) + " Ω ± " + str(tolerances.get(self.fifth_band.currentText())) + "%"

                self.result.setPlainText(res)
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(100, 250, 250, 300, Qt.AlignHCenter, res)
                self.resistor_pixmap.setPixmap(self.canvas)

            except (ValueError, TypeError):
                self.result.setPlainText("Some Colors are not specified")
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(0, 250, 450, 60, Qt.AlignHCenter, "Some Colors are not specified")
                self.resistor_pixmap.setPixmap(self.canvas)

        elif self.band == "6 Bands":
            try:
                digits = int("{0}{1}{2}".format(colors_without_black.index(self.first_band.currentText()) + 1,
                                                colors.index(self.second_band.currentText()),
                                                colors.index(self.third_band.currentText())))

                digits *= multipliers.get(self.forth_band.currentText())

                digits = str(digits) + " Ω ± " + str(tolerances.get(self.fifth_band.currentText())) + "%, "

                res = digits + str(tempco.get(self.sixth_band.currentText())) + " ppm/°C"

                self.result.setPlainText(res)
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(0, 250, 450, 300, Qt.AlignHCenter, res)
                self.resistor_pixmap.setPixmap(self.canvas)

            except (ValueError, TypeError):
                self.result.setPlainText("Some Colors are not specified")
                self.painter.fillRect(0, 250, 450, 60, QColor("white"))
                self.painter.drawText(0, 250, 450, 300, Qt.AlignHCenter, "Some Colors are not specified")
                self.resistor_pixmap.setPixmap(self.canvas)

    def coloring_resistor(self):
        # Setting up pen
        self.pen.setColor(QColor("Black"))
        self.painter.setPen(self.pen)
        self.painter.setFont(QFont("bahnschrift", 15))

        resistance_value = self.input.toPlainText()

        # Using RegEx to capture the digits and amounts of zeros and store it in two variables
        digits, zeros = findall(r"(\d\d\d?)(0*)", resistance_value)[0]

        self.change_second_band_color(colors_without_black[int(digits[0]) - 1])
        self.change_third_band_color(colors[int(digits[1])])
        self.change_forth_band_color(colors[int(digits[2])])
        self.change_fifth_band_color(reversed_multipliers.get(int("1" + zeros)))
        self.painter.fillRect(0, 250, 450, 60, QColor("white"))
        self.painter.drawText(0, 250, 450, 300, Qt.AlignHCenter, resistance_value + " Ω")
        self.resistor_pixmap.setPixmap(self.canvas)

    def copy_value(self):
        clipboard = QClipboard(self)
        clipboard.setText(self.result.toPlainText())

    def save_resistor_image(self):
        filename, selected_filter = QFileDialog.getSaveFileName(self, filter='''JPG Format (*.jpg);;PNG Format (*.png);;
        All files (*)''')
        self.canvas.save(filename)

    def copy_image(self):
        clipboard = QClipboard(self)
        clipboard.setImage(self.canvas.toImage())


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(r"icon.ico"))
window = RCCC()
window.show()
app.exec()
