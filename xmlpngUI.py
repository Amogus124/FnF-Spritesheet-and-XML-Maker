import sys
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QResizeEvent
from PyQt5.QtWidgets import QAction, QApplication, QCheckBox, QFrame, QGridLayout, QInputDialog, QLineEdit, QMessageBox, QPushButton, QWidget, QLabel, QFileDialog
from PyQt5 import uic
import ntpath

import xmlpngengine

class SpriteFrame(QWidget):
    def __init__(self, imgpath, parent):
        super().__init__()
        self.imgpath = imgpath
        self.image_pixmap = QPixmap(imgpath)
        self.pose_name = "idle"
        self.myframe = QFrame(self)

        self.img_label = QLabel(self.myframe)
        self.img_label.setToolTip(self.get_tooltip_string(parent))
        self.img_label.setPixmap(self.image_pixmap.scaled(128, 128))

        self.setFixedSize(QSize(130, 130))

        self.remove_btn = QPushButton(self.myframe)
        self.remove_btn.move(90, 90)
        self.remove_btn.setIcon(QIcon('./image-assets/remove-frame-icon.svg'))
        self.remove_btn.setIconSize(QSize(40, 40))
        self.remove_btn.setFixedSize(40, 40)
        self.remove_btn.setToolTip("Delete Frame")
        self.remove_btn.clicked.connect(lambda: self.remove_self(parent))

        self.select_checkbox = QCheckBox(self.myframe)
        self.select_checkbox.move(5, 5)
        self.select_checkbox.stateChanged.connect(lambda : self.add_to_selected_arr(parent))

        self.myframe.setStyleSheet("QFrame{border-style:solid; border-color:black; border-width:2px}")
    
    # overriding the default mousePressEvent
    def mousePressEvent(self, event):
        prevstate = self.select_checkbox.checkState()
        newstate = 0 if prevstate != 0 else 1
        self.select_checkbox.setChecked(newstate)
    
    # overriding the default enterEvent
    def enterEvent(self, event):
        self.myframe.setStyleSheet("QFrame{ border-style:solid; border-color:#FFC9DEF5; border-width:4px }")
    
    # overriding the default leaveEvent
    def leaveEvent(self, event):
        self.myframe.setStyleSheet("QFrame{border-style:solid; border-color:black; border-width:2px}")
    
    def remove_self(self, parent):
        parent.labels.remove(self)
        parent.num_labels -= 1

        parent.layout.removeWidget(self)
        self.deleteLater()

        parent.re_render_grid()
        print("Deleting image, count: ", parent.num_labels, "Len of labels", len(parent.labels))
        if len(parent.labels) == 0:
            parent.set_animation_button.setDisabled(True)
    
    def add_to_selected_arr(self, parent):
        if self.select_checkbox.checkState() == 0:
            parent.selected_labels.remove(self)
        else:
            parent.selected_labels.append(self)
    
    def get_tooltip_string(self, parent):
        charname = parent.character_name_textbox.text()
        charname = charname.strip() if charname.strip() != "" else "[ENTER YOUR CHARACTER NAME]"
        return f"Image: {ntpath.basename(self.imgpath)}\nCurrent Pose: {self.pose_name}\nWill appear in XML as:\n\t<SubTexture name=\"{charname} {self.pose_name}####\" (...) >\n\t# = digit from 0-9"


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        uic.loadUi('XmlPngUIFile.ui', self)
        # self.setFixedSize(834, 520)
        # self.setFixedSize(834, 545)
        self.xml_generate_button.clicked.connect(self.generate_xml)
        self.setWindowTitle("XML Generator")
        self.sprite_frames.setWidgetResizable(True)
        self.sprite_frame_content = QWidget()
        self.layout = QGridLayout(self.sprite_frame_content)
        self.sprite_frames.setWidget(self.sprite_frame_content)

        self.num_labels = 0
        self.labels = []
        self.selected_labels = []

        self.add_img_button = QPushButton()
        self.add_img_button.setIcon(QIcon("./image-assets/AddImg.png"))
        self.add_img_button.setGeometry(0, 0, 130, 130)
        self.add_img_button.setFixedSize(QSize(130, 130))
        self.add_img_button.setIconSize(QSize(130, 130))
        self.add_img_button.clicked.connect(self.open_file_dialog)

        self.layout.addWidget(self.add_img_button, 0, 0, Qt.AlignmentFlag(0x1|0x20))
        self.myTabs.setCurrentIndex(0)

        self.setWindowIcon(QIcon("./image-assets/appicon.png"))
        self.icongrid_zoom = 1
        self.pngUploadButton.clicked.connect(self.uploadIconGrid)
        self.icongridgenbutton.clicked.connect(self.getNewIconGrid)
        self.icon_upload_button.clicked.connect(self.appendIcon)

        self.action_zoom_in = QAction(self.icongrid_holder_label)
        self.icongrid_holder_label.addAction(self.action_zoom_in)
        self.action_zoom_in.triggered.connect(self.zoomInPixmap)
        self.action_zoom_in.setShortcut("Ctrl+i")

        self.action_zoom_out = QAction(self.icongrid_holder_label)
        self.icongrid_holder_label.addAction(self.action_zoom_out)
        self.action_zoom_out.triggered.connect(self.zoomOutPixmap)
        self.action_zoom_out.setShortcut("Ctrl+o")

        self.zoomLabel.setText("Zoom: 100%")

        self.iconpaths = []
        self.icongrid_path = ""

        self.set_animation_button.clicked.connect(self.setAnimationNames)
        self.character_name_textbox.textChanged.connect(self.onCharacterNameChange)

        self.num_cols = 4
    
    def onCharacterNameChange(self):
        for label in self.labels:
            label.img_label.setToolTip(label.get_tooltip_string(self))
    
    def resizeEvent(self, a0):
        w = self.width()
        # print("Current width", w)
        if w < 1228:
            self.num_cols = 4
        elif 1228 <= w <= 1652:
            self.num_cols = 8
        else:
            self.num_cols = 12
        self.re_render_grid()
        return super().resizeEvent(a0)
    
    def open_file_dialog(self):
        imgpaths = QFileDialog.getOpenFileNames(
            caption="Select sprite frames", 
            filter="PNG Images (*.png)",
        )[0]
        for pth in imgpaths:
            self.add_img(pth)
        if len(self.labels) > 0:
            self.set_animation_button.setDisabled(False)
    
    def add_img(self, imgpath):
        print("Adding image, prevcount: ", self.num_labels)
        self.labels.append(SpriteFrame(imgpath, self))
        self.layout.removeWidget(self.add_img_button)
        self.layout.addWidget(self.labels[-1], self.num_labels // self.num_cols, self.num_labels % self.num_cols, Qt.AlignmentFlag(0x1|0x20))
        self.num_labels += 1
        self.layout.addWidget(self.add_img_button, self.num_labels // self.num_cols, self.num_labels % self.num_cols, Qt.AlignmentFlag(0x1|0x20))
    
    def re_render_grid(self):
        for i, sp in enumerate(self.labels):
            self.layout.addWidget(sp, i//4, i%4, Qt.AlignmentFlag(0x1|0x20))
        self.layout.removeWidget(self.add_img_button)
        self.layout.addWidget(self.add_img_button, self.num_labels // 4, self.num_labels % 4, Qt.AlignmentFlag(0x1|0x20))
    
    def generate_xml(self):
        charname = self.character_name_textbox.text()
        charname = charname.strip()
        clip = self.border_clip_checkbox.checkState()
        if self.num_labels > 0 and charname != '':
            savedir = QFileDialog.getExistingDirectory(caption="Save files to...")
            print("Stuff saved to: ", savedir)
            if savedir != '':
                statuscode, errmsg = xmlpngengine.make_png_xml([lab.imgpath for lab in self.labels], [lab.pose_name for lab in self.labels], savedir, charname, False if clip == 0 else True)
                if errmsg is None:
                    self.display_msg_box(
                        window_title="Done!", 
                        text="Your files have been generated!\nCheck the folder you had selected",
                        icon=QMessageBox.Information
                    )
                else:
                    self.display_msg_box(
                        window_title="Error!",
                        text=("Some error occured! Error message: " + errmsg),
                        icon=QMessageBox.Critical
                    )
        else:
            errtxt = "Please enter some frames" if self.num_labels <= 0 else "Please enter the name of your character"
            self.display_msg_box(
                window_title="Error!", 
                text=errtxt,
                icon=QMessageBox.Critical
            )
    
    def zoomInPixmap(self):
        if self.icongrid_path and self.icongrid_zoom <= 5:
            self.icongrid_zoom *= 1.1
            icongrid_pixmap = QPixmap(self.icongrid_path)
            w = icongrid_pixmap.width()
            h = icongrid_pixmap.height()
            icongrid_pixmap = icongrid_pixmap.scaled(int(w*self.icongrid_zoom), int(h*self.icongrid_zoom), 1)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
            self.zoomLabel.setText("Zoom: %.2f %%" % (self.icongrid_zoom*100))


    def zoomOutPixmap(self):
        if self.icongrid_path and self.icongrid_zoom >= 0.125:
            self.icongrid_zoom /= 1.1
            icongrid_pixmap = QPixmap(self.icongrid_path)
            w = icongrid_pixmap.width()
            h = icongrid_pixmap.height()
            icongrid_pixmap = icongrid_pixmap.scaled(int(w*self.icongrid_zoom), int(h*self.icongrid_zoom), 1)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
            self.zoomLabel.setText("Zoom: %.2f %%" % (self.icongrid_zoom*100))
    
    def uploadIconGrid(self):
        print("Uploading icongrid...")
        self.icongrid_path = QFileDialog.getOpenFileName(
            caption="Select the Icon-grid", 
            filter="PNG Images (*.png)",
        )[0]
        icongrid_pixmap = QPixmap(self.icongrid_path)
        self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
        self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
        self.icongrid_holder_label.setPixmap(icongrid_pixmap)
    
    def getNewIconGrid(self):
        if self.icongrid_path != '' and len(self.iconpaths) > 0:
            print("Valid!")
            # savedir = QFileDialog.getExistingDirectory(caption="Save New Icongrid to...")
            # if savedir != '':
            stat, newinds, problemimg, exception_msg = xmlpngengine.appendIconToIconGrid(self.icongrid_path, self.iconpaths) #, savedir)
            print("[DEBUG] Function finished with status: ", stat)
            errmsgs = [
                'Icon grid was too full to insert a new icon', 
                'Your character icon: {} is too big! Max size: 150 x 150',
                'Unable to find suitable location to insert your icon'
            ]

            if exception_msg is not None:
                self.display_msg_box(
                    window_title="An Error occured", 
                    text=("An Exception (Error) oeccured somewhere\nError message:"+exception_msg),
                    icon=QMessageBox.Critical
                )

            if stat == 0:
                self.display_msg_box(
                    window_title="Done!", 
                    text="Your icon-grid has been generated!\nYour icon's indices are {}".format(newinds),
                    icon=QMessageBox.Information
                )
            elif stat == 4:
                self.display_msg_box(
                    window_title="Warning!", 
                    text="One of your icons was smaller than the 150 x 150 icon size!\nHowever, your icon-grid is generated but the icon has been re-adjusted. \nYour icon's indices: {}".format(newinds),
                    icon=QMessageBox.Warning
                )
            else:
                self.display_msg_box(
                    window_title="Error!", 
                    text=errmsgs[stat - 1].format(problemimg),
                    icon=QMessageBox.Critical
                )
            icongrid_pixmap = QPixmap(self.icongrid_path)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
        else:
            errtxt = "Please add an icon-grid image" if self.icongrid_path == '' else "Please add an icon"
            self.display_msg_box(
                window_title="Error!", 
                text=errtxt,
                icon=QMessageBox.Critical
            )
    
    def appendIcon(self):
        print("Appending icon")
        self.iconpaths = QFileDialog.getOpenFileNames(
            caption="Select your character icon", 
            filter="PNG Images (*.png)",
        )[0]
        print("Got icon: ", self.iconpaths)
        if len(self.iconpaths) > 0:
            print("Valid selected")
            self.curr_icon_label.setText("Number of\nicons selected:\n{}".format(len(self.iconpaths)))
    
    def setAnimationNames(self):
        if len(self.selected_labels) == 0:
            self.display_msg_box(window_title="Error", text="Please select some frames to rename by checking the checkboxes on them", icon=QMessageBox.Critical)
        else:
            text, okPressed = QInputDialog.getText(None, "Change Animation (Pose) Prefix Name", "Current Animation (Pose) prefix:"+(" "*50), QLineEdit.Normal) # very hack-y soln but it works!
            if okPressed and text != '':
                print("new pose prefix = ", text)
                for label in self.selected_labels:
                    label.pose_name = text
                    label.img_label.setToolTip(label.get_tooltip_string(self))
                
                for label in list(self.selected_labels):
                    label.select_checkbox.setChecked(False)
            else:
                print("Cancel pressed!")
    
    def display_msg_box(self, window_title="MessageBox", text="Text Here", icon=None):
        self.msgbox = QMessageBox(self)
        self.msgbox.setWindowTitle(window_title)
        self.msgbox.setText(text)
        if not icon:
            self.msgbox.setIcon(QMessageBox.Information)
        else:
            self.msgbox.setIcon(icon)
        x = self.msgbox.exec_()
        print("[DEBUG] Exit status of msgbox: "+str(x))




if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    myapp = MyApp()
    myapp.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print("Closing...")