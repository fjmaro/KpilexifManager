"""base class for pilexif manager"""
from typing import Dict, Optional
from pathlib import Path
import logging
import struct

import piexif
from PIL import Image, UnidentifiedImageError

from kmarotools.basics import logtools, convert


class PrivateTools:
    """
    --------------------------------------------------------------------------
    Functions and tools to be used by PilKernel
    --------------------------------------------------------------------------
    """
    # pylint: disable=too-few-public-methods

    @staticmethod
    def _load_metadata(file2load: Path) -> dict:
        """
        Get all the metadata in the image as it is stored in the file.
        """
        img = Image.open(file2load)
        data_dict: Dict[str, dict] = {}
        for kwd in img.info:
            try:
                data_dict[kwd] = piexif.load(img.info[kwd])
            except UnidentifiedImageError:
                data_dict[kwd] = img.info[kwd]
            except TypeError:
                data_dict[kwd] = img.info[kwd]
            except ValueError:
                data_dict[kwd] = img.info[kwd]
            except OSError:
                data_dict[kwd] = img.info[kwd]
            except struct.error:
                data_dict[kwd] = {}
        return data_dict

    @staticmethod
    def _load_exif_data(file2load: Path, add_basic_keywords=True) -> dict:
        """
        Get the exif and metadata in the file arranged and adds
        the basic missing keys if <add_basic_keywords> is enabled
        """
        data_dict = PrivateTools._load_metadata(file2load)
        exif_dict = {}
        if 'exif' in list(data_dict.keys()):
            exif_dict = data_dict['exif']

        for kwd in list(data_dict.keys()):
            if kwd != 'exif':
                exif_dict[kwd] = data_dict[kwd]

        if add_basic_keywords:
            kwds2add = ["Exif", "0th", "1st", "GPS"]
            for kwd in kwds2add:
                if kwd not in exif_dict:
                    exif_dict[kwd] = {}
        return exif_dict

    @staticmethod
    def _gps2val(gps_metadata_tuple: tuple, zone_positive: bool):
        """convert raw gps-metadata field to a float"""
        degs = gps_metadata_tuple[0][0] / gps_metadata_tuple[0][1]
        mins = gps_metadata_tuple[1][0] / gps_metadata_tuple[1][1]
        secs = gps_metadata_tuple[2][0] / gps_metadata_tuple[2][1]
        return convert.dms_zone2deg(degs, mins, secs, zone_positive)


class PilBaseClass(PrivateTools):
    """
    --------------------------------------------------------------------------
             PyKernel (Python based Kernel) Docstring for Development
    --------------------------------------------------------------------------
    """
    def __init__(self, logger=True, log_path=Path.cwd()) -> None:
        self._log_enabled = logger
        if logger:
            self.log = logtools.get_fast_logger('Pilexifmgr', log_path)
        else:
            self.log = logging.getLogger("")

    @staticmethod
    def help_dev() -> Optional[str]:
        """docstring"""
        return PilBaseClass.__doc__

    def help(self) -> Optional[str]:
        """docstring"""
        return self.__doc__
