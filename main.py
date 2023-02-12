import sqlite3
import cv2
import numpy as np
import torch
import easyocr
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QMessageBox
import re


HEIGHT, WIDTH = 640, 470
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')  # local model
reader = easyocr.Reader(['en'])


class FrameGrabber(QtCore.QThread):
    def __init__(self, parent=None):
        super(FrameGrabber, self).__init__(parent)

    def check_plate(self, candidate):
        connection = sqlite3.connect('cars.db')
        cur = connection.cursor()
        try:
            cur.execute(f"SELECT COUNT() as 'count' FROM spisok WHERE Plate LIKE '{candidate}'")
            res = cur.fetchone()
            return res[0] > 0
        except sqlite3.Error as e:
            return False

    def clean_text(self, text):
        text = text.replace(' ', '')
        text = text.replace('UA', '')
        text = text.replace('|', 'I')
        text = text.replace('l', 'I')
        text = text.replace('L', 'I')
        pattern = r'[^ABCEHIKMOPTX0-9]+'
        text = re.sub(pattern, '', text)
        return text

    def get_coords(self, results):
        try:
            indx = None
            for i in range(len(results.xyxy[0])):
                image_class = int(results.xyxy[0][i][-1].tolist())
                if image_class == 1:
                    indx = i
            plate = results.xyxy[0][indx]
            plate_start_point = tuple(map(int, plate[:2].tolist()))
            plate_end_point = tuple(map(int, plate[2:4].tolist()))
            return plate_start_point, plate_end_point
        except:
            pass
            return 0

    signal = QtCore.pyqtSignal(QtGui.QImage)

    def run(self):
        cap = cv2.VideoCapture(0)
        colour = (0, 255, 0)
        text_size = 1
        thickness = 2
        while cap.isOpened():
            success, frame = cap.read()
            frame = cv2.resize(frame, (HEIGHT, WIDTH))
            results = model(frame)
            frame = np.squeeze(results.render())
            plate_coord = self.get_coords(results)
            if plate_coord:
                crop_plate = frame[plate_coord[0][1]:plate_coord[1][1], plate_coord[0][0]:plate_coord[1][0]]
                txt = ''.join(reader.readtext(crop_plate, detail=0))
                txt = self.clean_text(txt)
                try:
                    number_render = re.findall(r'[ABCEHIKMOPTX]{2}[0-9]{4}[ABCEHIKMOPTX]{2}', txt)[0]
                    if self.check_plate(number_render):
                        colour = (0, 255, 0)
                    else:
                        colour = (0, 0, 255)
                except IndexError:
                    number_render = ''
                frame = cv2.putText(frame, number_render, (plate_coord[0][0], plate_coord[0][1] + 60), cv2.FONT_HERSHEY_SIMPLEX,
                                  text_size, colour, thickness, 2)

            if success:
                image = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_BGR888)
                self.signal.emit(image)


class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, MainWindow):
        super().__init__()
        self.MainWindow = MainWindow
        self.setupUi(self.MainWindow)
        self.grabber = FrameGrabber()
        self.grabber.signal.connect(self.updateFrame)
        self.grabber.start()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(1250, 665)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(0, 0))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setGeometry(QtCore.QRect(50, 30, 501, 521))
        self.tabWidget.setMinimumSize(QtCore.QSize(0, 0))
        self.tabWidget.setObjectName("tabWidget")
        self.imgLabel = QtWidgets.QLabel(self.centralwidget)
        self.imgLabel.setGeometry(QtCore.QRect(580, 80, HEIGHT, WIDTH))
        self.imgLabel.setObjectName('imgLabel')
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tableWidget = QtWidgets.QTableWidget(self.tab)
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 511, 501))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tableWidget_2 = QtWidgets.QTableWidget(self.tab_2)
        self.tableWidget_2.setGeometry(QtCore.QRect(-5, 1, 511, 501))
        self.tableWidget_2.setObjectName("tableWidget_2")
        self.tableWidget_2.setColumnCount(3)
        self.tableWidget_2.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_2.setHorizontalHeaderItem(2, item)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.lineEdit = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit.setGeometry(QtCore.QRect(140, 60, 191, 21))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit_2 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_2.setGeometry(QtCore.QRect(140, 100, 191, 21))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_3 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_3.setGeometry(QtCore.QRect(140, 140, 191, 21))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_4 = QtWidgets.QLineEdit(self.tab_3)
        self.lineEdit_4.setGeometry(QtCore.QRect(140, 180, 191, 21))
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.comboBox = QtWidgets.QComboBox(self.tab_3)

        self.comboBox.setGeometry(QtCore.QRect(140, 230, 191, 26))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.label = QtWidgets.QLabel(self.tab_3)
        self.label.setGeometry(QtCore.QRect(200, 40, 60, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.tab_3)
        self.label_2.setGeometry(QtCore.QRect(180, 80, 121, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.tab_3)
        self.label_3.setGeometry(QtCore.QRect(180, 120, 111, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.tab_3)
        self.label_4.setGeometry(QtCore.QRect(200, 160, 60, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.tab_3)
        self.label_5.setGeometry(QtCore.QRect(200, 210, 60, 16))
        self.label_5.setObjectName("label_5")
        self.pushButton_3 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_3.setGeometry(QtCore.QRect(170, 270, 113, 32))
        self.pushButton_3.setObjectName("pushButton_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.label_6 = QtWidgets.QLabel(self.tab_4)
        self.label_6.setGeometry(QtCore.QRect(190, 90, 111, 16))
        self.label_6.setObjectName("label_6")
        self.lineEdit_5 = QtWidgets.QLineEdit(self.tab_4)
        self.lineEdit_5.setGeometry(QtCore.QRect(180, 120, 113, 21))
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.pushButton_4 = QtWidgets.QPushButton(self.tab_4)
        self.pushButton_4.setGeometry(QtCore.QRect(180, 160, 113, 32))
        self.pushButton_4.setObjectName("pushButton_4")
        self.tabWidget.addTab(self.tab_4, "")
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setGeometry(QtCore.QRect(830, 20, 171, 20))
        self.checkBox.setObjectName("checkBox")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(760, 50, 113, 32))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(960, 50, 113, 32))
        self.pushButton_2.setObjectName("pushButton_2")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(2)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.loaddata()
        self.pushButton_3.clicked.connect(self.add_car)
        self.pushButton_4.clicked.connect(self.delete_car)

    @QtCore.pyqtSlot(QtGui.QImage)
    def updateFrame(self, image):
        self.imgLabel.setPixmap(QtGui.QPixmap.fromImage(image))

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "NeuroBarrier"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Owner"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Plate number"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Apartment"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "Phone"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "Status"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "List"))
        item = self.tableWidget_2.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Plate number"))
        item = self.tableWidget_2.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Owner"))
        item = self.tableWidget_2.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Time"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Journal"))
        self.comboBox.setItemText(0, _translate("MainWindow", "Resident"))
        self.comboBox.setItemText(1, _translate("MainWindow", "Guest"))
        self.label.setText(_translate("MainWindow", "Owner"))
        self.label_2.setText(_translate("MainWindow", "Plate number"))
        self.label_3.setText(_translate("MainWindow", "Apartment"))
        self.label_4.setText(_translate("MainWindow", "Phone"))
        self.label_5.setText(_translate("MainWindow", "Status"))
        self.pushButton_3.setText(_translate("MainWindow", "Add"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Add car"))
        self.label_6.setText(_translate("MainWindow", "Plate number"))
        self.pushButton_4.setText(_translate("MainWindow", "Remove"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("MainWindow", "Remove car"))
        self.checkBox.setText(_translate("MainWindow", "Only manual control"))
        self.pushButton.setText(_translate("MainWindow", "Close"))
        self.pushButton_2.setText(_translate("MainWindow", "Open"))

    def loaddata(self):
        connection = sqlite3.connect('cars.db')
        cur = connection.cursor()
        sqlquery_spisok = "SELECT * FROM spisok"
        sqlquery_journal = "SELECT * FROM journal"

        cur.execute("SELECT COUNT(*) FROM spisok")
        number_of_rows_spisok = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM journal")
        number_of_rows_journal = cur.fetchall()

        self.tableWidget.setRowCount(number_of_rows_spisok[0][0])
        tablerow = 0
        for row in cur.execute(sqlquery_spisok):
            self.tableWidget.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(row[0]))
            self.tableWidget.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(str(row[2])))
            self.tableWidget.setItem(tablerow, 3, QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow, 4, QtWidgets.QTableWidgetItem(row[4]))
            tablerow += 1

        self.tableWidget_2.setRowCount(number_of_rows_journal[0][0])
        tablerow = 0
        for row in cur.execute(sqlquery_journal):
            self.tableWidget_2.setItem(tablerow, 0, QtWidgets.QTableWidgetItem(row[0]))
            self.tableWidget_2.setItem(tablerow, 1, QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget_2.setItem(tablerow, 2, QtWidgets.QTableWidgetItem(str(row[2])))
            tablerow += 1

    def show_popup(self, text):
        msg = QMessageBox()
        msg.setWindowTitle('Information')
        msg.setText(f'{text}')
        msg.exec_()

    def clear_lines(self):
        self.lineEdit.clear()
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()

    def add_car(self):
        connection = sqlite3.connect('cars.db')
        cur = connection.cursor()
        try:
            cur.execute(f"SELECT COUNT() as 'count' FROM spisok WHERE Plate LIKE '{self.lineEdit_2.text()}'")
            res = cur.fetchone()
            if res[0] > 0:
                self.show_popup('Такая машина уже есть')
                return False

            cur.execute("INSERT INTO spisok VALUES(?, ?, ?, ?, ?, ?)", (
                self.lineEdit.text(), self.lineEdit_2.text(), self.lineEdit_3.text(), self.lineEdit_4.text(),
                self.comboBox.currentText(), 0))
            connection.commit()
            self.clear_lines()
            self.show_popup('Done!')
            self.loaddata()
        except sqlite3.Error as e:
            self.show_popup('Ошибка добавления пользователя в БД' + str(e))
            return False
        return True

    def delete_car(self):
        connection = sqlite3.connect('cars.db')
        cur = connection.cursor()
        try:
            cur.execute(f"SELECT COUNT() as 'count' FROM spisok WHERE Plate LIKE '{self.lineEdit_5.text()}'")
            res = cur.fetchone()
            if res[0] == 0:
                self.show_popup('Такой машины нет')
                return False

            cur.execute(f"DELETE FROM spisok WHERE Plate LIKE '{self.lineEdit_5.text()}'")
            connection.commit()
            self.clear_lines()
            self.show_popup('Done!')
            self.loaddata()
        except sqlite3.Error as e:
            self.show_popup('Ошибка удаления пользователя из БД ' + str(e))
            return False
        return True


    def quitApp(self):
        QtWidgets.QApplication.quit()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
