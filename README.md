# TKViewer

NexusTK DAT Object Viewer for viewing and exporting EPF/TBL/PAL/MAP files.

![TK Viewer](https://i.imgur.com/5Vdb2xW.png)

## Quickstart

This script will take a bit to load up, give it some time.

**Dependencies**:
* Python 3 (PyQt5)
* Python pip3 dependencies:

```bash
pip install pyqt5
pip install pillow
```

**Running the script**:

```bash
python3 epf_viewer.py
```

## FileReader Module

This module contains readers for the following files:
* DSC
* EPF
* MAP
* PAL
* TBL (TileA, TileB, TileC, SObj)

### File Structures

#### TBL File Structure (Tile TBL)

```cpp
int tile_count                     (4 bytes)
int palette_count                  (4 bytes)
byte[3] unknown                    (3 bytes)
short[tile_count] palette_indicies (2 * tile_count bytes)
```

**Note**: TileX.tbl will refer to various TileX[0-(palette_count-1)].pal files.

#### TBL File Structure (SObj TBL)

```cpp
int obj_count               (4 bytes)
short unknown               (2 bytes)
obj[obj_count]              (obj_count * ((2 * tile_count) + 2) bytes)

typedef struct {
  byte movement_directions  (1 byte)
  byte tile_count           (1 byte)
  short[tile_count]         (2 * tile_count bytes)
} obj
```

**Note**: Movement Directions appear to have 6 states:
* 0x00 (Empty)
* 0x01 (Bottom)
* 0x02 (Top)
* 0x04 (Left)
* 0x08 (Right)
* 0x0F (Full)

#### PAL File Structure

```cpp
byte[9] header               (9 bytes) # DLPalette
byte[15] unknown             (15 bytes)
byte animation_color_count   (1 byte)
byte[7] unknown2             (7 bytes)
short[animation_color_count] (animation_color_count * 2 bytes)
color[256] palette           (1024 bytes)

typedef struct {
  byte blue        (1 byte)
  byte green       (1 byte)
  byte red         (1 byte)
  byte padding     (1 byte)
} color            (4 bytes)
```

#### Packed PAL File Structure

```cpp
int palette_count
PAL[palette_count] palettes
```

**Note**: `PAL` refers to the File Structure of PAL (above)

#### EPF File Structure

```cpp
short tile_count                    (2 bytes)
short height                        (2 bytes)
short width                         (2 bytes)
short unknown                       (2 bytes)
int pixel_data_length               (4 bytes)
byte[pixel_data_length] pixel_data  (pixel_data_length bytes)
tile_entry[tile_count] tile_entries (tile_count * 16 bytes)

typedef struct {
  short pad_top                     (2 bytes)
  short pad_left                    (2 bytes)
  short height                      (2 bytes)
  short width                       (2 bytes)
  int pixel_data_offset             (4 bytes)
  int stencil_data_offset           (4 bytes)
} tile_entry                        (16 bytes)
```

#### MAP File Structure

```cpp
short width              (2 bytes)
short height             (2 bytes)
tile[width*height] tiles (width * height * 4 bytes)

typedef struct {
  short ab_tile_id       (2 bytes)
  short sobj_tile_id     (2 bytes)
} tile                   (4 bytes)
```

## TKViewer GUI (PyQt5)

A GUI using the FileReader module to perform some functions.

**Features**:

The TKViewer attempts to mimic parts of the NexusTK Map Editor.

The **Data** directory (from NexusTK Map Editor) is required. This contains the
following files:

```cpp
SObj.tbl
TileA0.pal
TileA1.pal
TileA2.pal
TileA3.pal
TileA4.pal
TileA5.pal
TileA6.pal
TileA7.pal
TileA.epf
TileA.tbl
TileB0.pal
TileB1.pal
TileB2.pal
TileB3.pal
TileB4.pal
TileB.epf
TileB.tbl
TileC0.pal
TileC1.pal
TileC2.pal
TileC3.pal
TileC4.pal
TileC5.pal
TileC6.pal
TileC7.pal
TileC8.pal
TileC9.pal
TileC10.pal
TileC.epf
TileC.tbl
```

The Map Editor and its **Data** directory contents are intentionally
**NOT INCLUDED** here. These files are binary files and do not belong
in this repository.

These Data files are **required**
Since this exports NexusTK EPF/PAL/TBL files, the TKViewer is coded to
reference TileA, TileB, TileC format - this can be modified for custom projects.

* Open and Display MAP file
* Export A Tiles to Bitmaps
* Export B Tiles to Bitmaps
* Export C Tiles to Bitmaps
* Export Static Objects to Bitmaps
* Export All Tile Groups (A, B, C, and Static Objects)
* Export individual Tiles to Bitmap (Right-Click)

## Contributors

Huge thank you to everyone who helps figure out NTK file structures:

  * DDeokk
  * herbert3000
  * wattostudios
