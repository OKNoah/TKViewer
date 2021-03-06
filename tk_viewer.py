#!/usr/bin/env python3

__author__ = 'DizzyThermal'
__email__ = 'DizzyThermal@gmail.com'
__license__ = 'GNU GPLv3'
__version__ = '1.4'
__version_codename__ = 'Rat'

import binascii
import io
import os
import signal
import sys

from tk_gui import Ui_MainWindow
from file_reader import EPFHandler
from file_reader import PALHandler
from file_reader import MAPHandler
from file_reader import SObjTBLHandler
from file_reader import TBLHandler

from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QWidget

_CUR_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
_ICON = os.path.join(_CUR_DIR, 'icon.png')
_DATA_DIR = os.path.join(_CUR_DIR, 'Data')
_TILE_A = os.path.join(_DATA_DIR, 'TileA')
_TILE_B = os.path.join(_DATA_DIR, 'TileB')
_TILE_C = os.path.join(_DATA_DIR, 'TileC')
_SOBJ = os.path.join(_DATA_DIR, 'SObj')
_TILE_BYTES = 1728
_TILE_B_OFFSET = 49151


class EPFViewer(QMainWindow):
    _TILE_WIDTH = 24
    _TILE_HEIGHT = 24

    def __init__(self, app=None, ui=None):
        super().__init__()
        self.app = app
        self.ui = ui

    def set_images(self, images, scroll_area, start_index=1, col_width=14):
        row = 0
        col = 0
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(1)
        grid_layout.setVerticalSpacing(1)
        self._actions = []
        for i in range(len(images)):
            qim = ImageQt(images[i])
            pixmap = QPixmap.fromImage(qim)
            ql = QLabel()
            ql.setPixmap(pixmap)
            ql.setScaledContents(True)
            ql.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            ql.setContextMenuPolicy(Qt.ActionsContextMenu)
            action = QAction('Export to BMP'.format((i+start_index)), self)
            action.triggered.connect((lambda idx: lambda: self.export_tile(images[idx]))(i))
            self._actions.append(action)
            ql.addAction(action)
            grid_layout.addWidget(ql, row, col)

            col += 1
            if col >= col_width and col_width > 0:
                row += 1
                col = 0

        client = QWidget()
        scroll_area.setWidget(client)
        client.setLayout(grid_layout)
        
    def export(self, images, prefix='tile', dir_path=None, multi=True):
        if not dir_path:
            multi=False
            dir_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if not dir_path:
            return

        pad_length = len(str(len(images)))
        for i in range(len(images)):
            images[i].save(os.path.join(dir_path, '_'.join(
                (prefix, str(i).zfill(pad_length))) + '.bmp'))
        if not multi:
            QMessageBox.about(self, 'EPFViewer', 'Successfully exported tiles to: "{}"'.format(dir_path))

    def export_all(self, images, prefixes=['tileA', 'tileB', 'tileC', 'tileStatic']):
        dir_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if not dir_path:
            return

        for i in range(len(images)):
            self.export(images[i], prefix=prefixes[i], dir_path=dir_path)

        QMessageBox.about(self, 'EPFViewer', 'Successfully exported tiles to: "{}"'.format(dir_path))

    def export_tile(self, image):
        dir_path = QFileDialog.getSaveFileName(self,
                'Save Tile', os.path.join(os.path.expanduser('~'),
                    'tile.bmp'))
    
        if not dir_path:
            return

        image.save(dir_path[0])
        QMessageBox.about(self, 'EPFViewer', 'Successfully exported tile')

    def view_map(self, a_images, b_images, sobj_objects, sobj_images):
        dir_path = QFileDialog.getOpenFileName(self,
                'Map File', os.path.join(os.path.expanduser('~')))

        if not dir_path:
            return

        map_name = os.path.split(dir_path[0])[1]
        map_handler = MAPHandler(dir_path[0])
        map_width = map_handler.width
        map_height = map_handler.height
        tiles = map_handler.tiles

        black = Image.new('RGBA', (24, 24), 'black')
        im = Image.new('RGBA', (map_width * 24, map_height * 24), 'black')
        depth = 0
        length = 0

        for i in range(len(tiles)):
            if tiles[i]['ab_tile'] >= _TILE_B_OFFSET:
                tile = b_images[tiles[i]['ab_tile']-_TILE_B_OFFSET]
            elif tiles[i]['ab_tile'] > 0:
                tile = a_images[tiles[i]['ab_tile']]
            else:
                tile = black

            im.paste(tile, (length * 24, depth * 24))

            # If a Static Object is here, render upwards to height
            if tiles[i]['sobj_tile']:
                tile_index = tiles[i]['sobj_tile']
                sobj_image = sobj_images[tile_index]

                height = sobj_objects[tile_index]['height']-1
                im.paste(sobj_image, (length * 24, (depth-height) * 24),
                        sobj_image)

            if (((i+1) % map_width) == 0) and (i != 0):
                depth += 1
                length = 0
            else:
                length += 1

        im.show(map_name)

    def show_about(self):
        dialog = QMessageBox.information(self, 'TKViewer v{} ({})'.format(
            __version__,
            __version_codename__),
                '\n'.join((
                    'Github: https://github.com/DizzyThermal/TKViewer',
                    '',
                    'Formerly known as: EPFViewer')))

def main(argv):
    tbl_a = TBLHandler('.'.join((_TILE_A, 'tbl')))
    pals_a = []
    for i in range(tbl_a.palette_count):
        pal = PALHandler('.'.join((_TILE_A + '{}'.format(i), 'pal')))
        pals_a.append(pal.pals[0])
        pal.close()

    epf_a = EPFHandler('.'.join((_TILE_A, 'epf')), pals=pals_a, tbl=tbl_a)
    a_images = epf_a.get_frames()
    epf_a.close()
    tbl_a.close()

    tbl_b = TBLHandler('.'.join((_TILE_B, 'tbl')))
    pals_b = []
    for i in range(tbl_b.palette_count):
        pal = PALHandler('.'.join((_TILE_B + '{}'.format(i), 'pal')))
        pals_b.append(pal.pals[0])
        pal.close()
    epf_b = EPFHandler('.'.join((_TILE_B, 'epf')), pals=pals_b, tbl=tbl_b)
    b_images = epf_b.get_frames()
    epf_b.close()
    tbl_b.close()

    tbl_c = TBLHandler('.'.join((_TILE_C, 'tbl')))
    pals_c = []
    for i in range(tbl_c.palette_count):
        pal = PALHandler('.'.join((_TILE_C + '{}'.format(i), 'pal')))
        pals_c.append(pal.pals[0])
        pal.close()
    epf_c = EPFHandler('.'.join((_TILE_C, 'epf')), pals=pals_c, tbl=tbl_c)
    c_images = epf_c.get_frames()

    sobj = SObjTBLHandler('.'.join((_SOBJ, 'tbl')), epf=epf_c)
    sobj_images = sobj.get_images(alpha_rgb=(0, 0, 255),
            background_color='blue', height_pad=10)
    sobj_images_raw = sobj.get_images(alpha_rgb=(0, 0, 0, 0),
            background_color=None)
    sobj.close()
    epf_c.close()
    tbl_c.close()

    app = QApplication(argv)
    ui = Ui_MainWindow()
    window = EPFViewer(app, ui)
    ui.setupUi(window)

    window.set_images(a_images, ui.a_tiles_scroll_area)
    window.set_images(b_images, ui.b_tiles_scroll_area, start_index=49152)
    window.set_images(c_images, ui.c_tiles_scroll_area)
    window.set_images(sobj_images, ui.sobj_tiles_scroll_area, col_width=-1)

    ui.actionA_Tiles.triggered.connect(lambda: window.export(a_images))
    ui.actionB_Tiles.triggered.connect(lambda: window.export(b_images))
    ui.actionC_Tiles.triggered.connect(lambda: window.export(c_images))
    ui.actionStatic_Tiles.triggered.connect(lambda: window.export(sobj_images))
    ui.actionExport_All.triggered.connect(lambda: window.export_all(
        [a_images, b_images, c_images, sobj_images]))
    ui.actionOpen_Map.triggered.connect(lambda: window.view_map(a_images,
        b_images, sobj.objects, sobj_images_raw))
    ui.actionAbout.triggered.connect(lambda: window.show_about())

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app.setWindowIcon(QIcon(_ICON))

    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
