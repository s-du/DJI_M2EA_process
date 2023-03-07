# import custom packages
import resources as res

# import Pyqt packages
import PyQt5.uic
from PyQt5 import QtCore, QtGui, QtWidgets

# other packages
import os
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image
from PIL import ImageFilter
from matplotlib import cm
from matplotlib import pyplot as plt


class DialogOptions(QtWidgets.QDialog):
    """
    Dialog that allows the user to visualize the orthoimage and process it
    """
    def __init__(self, em, dist, rh, temp, parent=None):
        QtWidgets.QDialog.__init__(self)
        basepath = os.path.dirname(__file__)
        basename = 'dialog_options'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)
        self.lineEdit_em.setText(em)
        self.lineEdit_dist.setText(dist)
        self.lineEdit_rh.setText(rh)
        self.lineEdit_temp.setText(temp)

        # define constraints on lineEdit

        # button actions
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class ThermalProcess(QtWidgets.QMainWindow):
    """
    Main Window class for the Pointify application.
    """

    def __init__(self, parent=None):
        """
        Function to initialize the class
        :param parent:
        """
        super(ThermalProcess, self).__init__(parent)

        # load the ui
        basepath = os.path.dirname(__file__)
        basename = 'thermal_proc'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        # define useful paths
        self.gui_folder = os.path.dirname(__file__)
        self.sdk_tool_path = Path(res.find('dji/dji_irp.exe'))

        # Fill combobox with colormaps choices
        self.colormap_list = ['plasma', 'inferno', 'Greys', 'Greys_r', 'coolwarm', 'jet', 'rainbow', 'Spectral_r', 'cividis', 'viridis', 'gnuplot2']
        self.comboBox.addItems(self.colormap_list)

        self.out_of_lim = ['black', 'white', 'red']
        self.out_of_matp = ['k', 'w', 'r']
        self.img_post = ['none','sharpen','sharpen strong','edge enhance' ]
        self.comboBox_colors_low.addItems(self.out_of_lim)
        self.comboBox_colors_high.addItems(self.out_of_lim)
        self.comboBox_post.addItems(self.img_post)
        self.advanced_options = False

        # default thermal options:
        self.em = 0.95
        self.dist = 5
        self.rh = 50
        self.refl_temp = 25

        to_find = 'img/plasma.png'
        pixmap = QtGui.QPixmap(res.find(to_find))
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()

        # create connections (signals)
        self.create_connections()

    def create_connections(self):
        # 'Simplify buttons'
        self.pushButton_folder.clicked.connect(self.load_imgs)
        self.pushButton_go.clicked.connect(self.process)
        self.comboBox.currentIndexChanged.connect(self.on_combo_changed)
        self.pushButton_estimate.clicked.connect(self.estimate_temp)
        self.pushButton_advanced.clicked.connect(self.define_options)

        # on lineedit fill
        self.lineEdit_min_temp.textChanged.connect(self.on_edit_change)
        self.lineEdit_max_temp.textChanged.connect(self.on_edit_change)


    def define_options(self):
        dialog = DialogOptions(str(self.em), str(self.dist), str(self.rh), str(self.refl_temp))
        dialog.setWindowTitle("Choose advanced thermal options")

        if dialog.exec_():
            try:
                self.advanced_options = True
                em = float(dialog.lineEdit_em.text())
                if em < 0.1 or em > 1:
                    raise ValueError
                else:
                    self.em = em
                dist = float(dialog.lineEdit_dist.text())
                if dist < 1 or dist > 25:
                    raise ValueError
                else:
                    self.dist = dist
                rh = float(dialog.lineEdit_rh.text())
                if rh < 20 or rh > 100:
                    raise ValueError
                else:
                    self.rh = rh
                refl_temp = float(dialog.lineEdit_temp.text())
                if refl_temp < -40 or refl_temp > 500:
                    raise ValueError
                else:
                    self.refl_temp = refl_temp

            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Warning",
                                              "Oops! Some of the values are not valid!")
                self.define_options()

    def on_edit_change(self):
        try:
            tmin = self.lineEdit_min_temp.text()
            tmax = self.lineEdit_max_temp.text()
            tmin = float(tmin)
            tmax = float(tmax)
            if tmax > tmin:
                self.pushButton_go.setEnabled(True)
            else:
                self.pushButton_go.setEnabled(False)
        except:
            self.pushButton_go.setEnabled(False)


    def estimate_temp(self):
        def compute_delta(img_path):
            raw_out = img_path[:-4] + '.raw'
            self.read_dji_image(img_path, raw_out)

            fd = open(raw_out, 'rb')
            rows = 512
            cols = 640
            f = np.fromfile(fd, dtype='<f4', count=rows * cols)
            im = f.reshape((rows, cols))
            fd.close()

            comp_tmin = np.amin(im)
            comp_tmax = np.amax(im)

            os.remove(raw_out)

            return comp_tmin, comp_tmax

        ref_pic_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',
                                                             self.folder, "Image files (*.jpg *.JPG *.gif)")
        img_path = ref_pic_name[0]
        if img_path != '':
            tmin, tmax = compute_delta(img_path)
            self.lineEdit_min_temp.setText(str(round(tmin, 2)))
            self.lineEdit_max_temp.setText(str(round(tmax, 2)))

    def on_combo_changed(self):
        i = self.comboBox.currentIndex()
        img_thumb_list = ['plasma.png', 'inferno.png', 'greys.png', 'greys_r.png', 'coolwarm.png', 'jet.png',
                          'rainbow.png', 'spectral_r.png', 'cividis.png', 'viridis.png', 'gnuplot2.png']
        to_find = 'img/' + img_thumb_list[i]
        pixmap = QtGui.QPixmap(res.find(to_find))
        pixmap = pixmap.scaledToWidth(200)
        self.label_thumb.setPixmap(pixmap)
        self.label_thumb.show()

    def load_imgs(self):
        # get the user to select folder
        self.folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.folder:
            # create image list
            list_file = os.listdir(self.folder)
            self.list_img = []
            self.list_path = []
            for file in list_file:
                if file.endswith('JPG'):
                    self.list_img.append(file)
                    self.list_path.append(Path(os.path.join(self.folder, file)))

            print(self.list_img)
            print(self.list_path)

            # Enable actions
            self.lineEdit_min_temp.setEnabled(True)
            self.lineEdit_max_temp.setEnabled(True)
            self.lineEdit_colors.setEnabled(True)
            self.comboBox.setEnabled(True)
            self.comboBox_colors_low.setEnabled(True)
            self.comboBox_colors_high.setEnabled(True)
            self.comboBox_post.setEnabled(True)
            self.pushButton_estimate.setEnabled(True)
            self.pushButton_advanced.setEnabled(True)

    def read_dji_image(self, img_in, raw_out):
        subprocess.run(
            [str(self.sdk_tool_path), "-s", f"{img_in}", "-a", "measure", "-o", f"{raw_out}", "--measurefmt", "float32"],
            universal_newlines=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )


    def process(self):
        rename = False
        # get parameters
        #   colormap
        i = self.comboBox.currentIndex()
        colormap = self.colormap_list[i]

        #   number of color classes
        try:
            n_colors = int(self.lineEdit_colors.text())
            if n_colors > 1024:
                n_colors = 1024
        except:
            n_colors = 256
        print(n_colors, ' colors will be used')

        #   temp limits
        tmin = float(self.lineEdit_min_temp.text())
        tmax = float(self.lineEdit_max_temp.text())

        #   out of limits color
        i = self.comboBox_colors_low.currentIndex()
        user_lim_col_low = self.out_of_matp[i]
        i = self.comboBox_colors_high.currentIndex()
        user_lim_col_high = self.out_of_matp[i]

        #   post process operation
        k = self.comboBox_post.currentIndex()
        post_process = self.img_post[k]

        # create subfolder
        desc = 'img_th_processed_' + colormap + '_' + str(round(tmin, 0)) + '_' \
               + str(round(tmax, 0)) + '_' + post_process
        self.subfolder = os.path.join(self.folder, desc)

        if not os.path.exists(self.subfolder):
            os.mkdir(self.subfolder)

        # create raw outputs for each image
        for i, img_path in enumerate(self.list_path):
            _, filename = os.path.split(str(img_path))
            new_raw_path = Path(str(img_path)[:-4]+str(i)+'.raw')

            self.read_dji_image(str(img_path), str(new_raw_path))

            # read raw dji output
            fd = open(new_raw_path, 'rb')
            rows = 512
            cols = 640
            f = np.fromfile(fd, dtype='<f4', count=rows * cols)
            im = f.reshape((rows, cols))  # notice row, column format
            fd.close()

            # compute new normalized temperature
            thermal_normalized = (im - tmin) / (tmax - tmin)

            # get colormap
            custom_cmap = cm.get_cmap(colormap, n_colors)

            custom_cmap.set_over(user_lim_col_high)
            custom_cmap.set_under(user_lim_col_low)

            thermal_cmap = custom_cmap(thermal_normalized)
            thermal_cmap = np.uint8(thermal_cmap*255)

            img_thermal = Image.fromarray(thermal_cmap[:,:,[0,1,2]])
            thermal_filename = os.path.join(self.subfolder, filename)

            if post_process == 'none':
                img_thermal.save(thermal_filename)
            elif post_process == 'sharpen':
                img_th_sharpened = img_thermal.filter(ImageFilter.SHARPEN)
                img_th_sharpened.save(thermal_filename)
            elif post_process == 'sharpen strong':
                img_th_sharpened = img_thermal.filter(ImageFilter.SHARPEN)
                img_th_sharpened2 = img_th_sharpened.filter(ImageFilter.SHARPEN)
                img_th_sharpened2.save(thermal_filename)
            elif post_process == 'edge enhance':
                img_th_enedge = img_thermal.filter(ImageFilter.EDGE_ENHANCE)
                img_th_enedge.save(thermal_filename)

            # remove raw file
            os.remove(new_raw_path)

            if i == len(self.list_path)-1:
                fig, ax = plt.subplots()
                data = np.clip(np.random.randn(10, 10)*100, tmin, tmax)
                print(data)

                cax = ax.imshow(data, cmap=custom_cmap)

                # Add colorbar, make sure to specify tick locations to match desired ticklabels
                if n_colors > 12:
                    n_colors = 12
                ticks = np.linspace(tmin, tmax, n_colors+1, endpoint=True)
                cbar = fig.colorbar(cax, ticks=ticks, extend='both')
                ax.remove()

                legend_path = os.path.join(self.subfolder,'plot_onlycbar_tight.png')
                plt.savefig(legend_path, bbox_inches='tight')

        print('Process_done')