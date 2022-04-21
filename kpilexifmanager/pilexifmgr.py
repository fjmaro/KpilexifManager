"""
------------------------------------------------------------------------------
PilExifManager (Pillow-Piexif Manager/wrapper)
------------------------------------------------------------------------------
"""
from typing import Optional, Tuple, List
from pathlib import Path
import datetime

import piexif
from kjmarotools.basics import filetools, convert

from .baseclass import PilBaseClass


class PilExifManager(PilBaseClass):
    """
    --------------------------------------------------------------------------
    JPG Exif manager based on Pillow and Piexif Libraries
    --------------------------------------------------------------------------
    Development
    - New future compatible extensions must be added to:
        > EDITABLE_EXTENSIONS
        > READABLE_EXTENSIONS
    --------------------------------------------------------------------------
    """
    # pylint: disable=too-many-public-methods
    EDITABLE_EXTENSIONS = "JPG", "JPEG"
    READABLE_EXTENSIONS = EDITABLE_EXTENSIONS + ("PNG", )

    def __init__(self, logger=True, log_path=Path.cwd()) -> None:
        super().__init__(logger, log_path)
        self.metadata: dict = {}
        self._filepath: Optional[Path] = None
        self._temporal_keywords: List[str] = []

    @property
    def metadata_as_string(self) -> str:
        """return the metadata in string format"""
        if not self.metadata:
            return ""
        spacer = max([len(x) for x in list(self.metadata.keys())])
        out_str = ""
        for kwd in list(self.metadata.keys()):
            if kwd == "thumbnail":
                continue
            new_line = ("{:<" + str(spacer) + "} | ").format(kwd)
            out_str += new_line + str(self.metadata[kwd]) + "\n"
        return out_str

    @property
    def has_gps_data(self) -> bool:
        """has GPS data"""
        try:
            self.get_gps_data()
            return True
        except KeyError:
            pass
        return False

    @property
    def has_date_original(self) -> bool:
        """DateTimeOriginal"""
        return piexif.ExifIFD.DateTimeOriginal in self.metadata['Exif']

    @property
    def has_date_digitized(self) -> bool:
        """DateTimeDigitized"""
        return piexif.ExifIFD.DateTimeDigitized in self.metadata['Exif']

    @property
    def has_valid_date_original(self) -> bool:
        """DateTimeOriginal"""
        if self.has_date_original:
            return self.get_date_original().year != 1
        return False

    @property
    def has_valid_date_digitized(self) -> bool:
        """DateTimeDigitized"""
        if self.has_date_digitized:
            return self.get_date_digitized().year != 1
        return False

    def load_file(self, file: Path) -> None:
        """load file"""
        if self._log_enabled:
            self.log.info("[PilexifMgr] Loading file: %s", file)
        err_msg = f"File '{file.name}' not compatible with metadata reading"
        err_msg += f" [Compatible Formats = {self.READABLE_EXTENSIONS}]"
        assert file.suffix[1:].upper() in self.READABLE_EXTENSIONS, err_msg
        self._temporal_keywords = []
        self._filepath = file
        self.metadata = self._load_exif_data(file)

    def save_file(self, filename="", overwrite=False) -> None:
        """
        ----------------------------------------------------------------------
        Save the file with the updated metadata in the same path.
        > filename: If empty, the original filename is used
        > overwrite: If False, the new file is saved as original_filename(x)
        ----------------------------------------------------------------------
        """
        assert self._filepath is not None
        sfx = self._filepath.suffix[1:].upper()
        err_msg = "File not compatible with metadata writing"
        err_msg += f" [Compatible Formats = {self.EDITABLE_EXTENSIONS}]"
        assert sfx not in self.EDITABLE_EXTENSIONS, err_msg

        exif_bytes = piexif.dump(self.metadata)
        base_path = self._filepath.parent
        output_file = self._filepath

        if filename:
            output_file = base_path.joinpath(filename)

        if not overwrite:
            output_file = filetools.itername(output_file)

        if self._log_enabled:
            self.log.info("[PilexifMgr] Writing file: %s <in> %s",
                          output_file.name, output_file.parent)
        piexif.insert(exif_bytes, str(self._filepath), output_file)

    def clear_metadata(self) -> None:
        """clear the file metadata"""
        self.metadata = {}

    def get_date_original(self) -> datetime.datetime:
        """
        returns the file metadata date original
        """
        dttkn = self.metadata['Exif'][piexif.ExifIFD.DateTimeOriginal]
        try:
            return convert.str2datetime(dttkn.decode('utf-8'), ":", " ", ":")
        except ValueError:
            return datetime.datetime(1, 1, 1)

    def get_date_digitized(self) -> datetime.datetime:
        """
        returns the file metadata date-taken field
        """
        dttkn = self.metadata['Exif'][piexif.ExifIFD.DateTimeDigitized]
        try:
            return convert.str2datetime(dttkn.decode('utf-8'), ":", " ", ":")
        except ValueError:
            return datetime.datetime(1, 1, 1)

    def get_gps_data(self) -> Tuple[float, float, float, bool]:
        """get the gps data in lat-lon-alt-altitude_in_msl"""
        meta_dat = self.metadata['GPS'][piexif.GPSIFD.GPSLatitude]
        zbn = self.metadata['GPS'][piexif.GPSIFD.GPSLatitudeRef]
        zone_positive = zbn == b'N'
        lat = self._gps2val(meta_dat, zone_positive)

        meta_dat = self.metadata['GPS'][piexif.GPSIFD.GPSLongitude]
        zbn = self.metadata['GPS'][piexif.GPSIFD.GPSLongitudeRef]
        zone_positive = zbn == b'E'
        lon = self._gps2val(meta_dat, zone_positive)

        meta_dat = self.metadata['GPS'][piexif.GPSIFD.GPSAltitude]
        alt_ref = self.metadata['GPS'][piexif.GPSIFD.GPSAltitudeRef]
        alt = meta_dat[0] / meta_dat[1]
        msl = alt_ref == 1
        return lat, lon, alt, msl

    def get_keywords(self) -> List[str]:
        """get video keywords as list of strings"""
        has0th = '0th' in self.metadata
        kwd_idx = piexif.ImageIFD.XPKeywords
        if has0th and kwd_idx in self.metadata['0th']:
            tags_bytes = bytes(self.metadata['0th'][kwd_idx])
            tags_str = tags_bytes.decode('utf-16').split("\x00", maxsplit=1)[0]
            return tags_str.split(";")
        return []

    def get_camera_maker(self) -> str:
        """get camera maker as string"""
        has0th = '0th' in self.metadata
        if has0th and (piexif.ImageIFD.Make in self.metadata['0th']):
            return self.metadata['0th'][piexif.ImageIFD.Make]
        return ""

    def get_camera_model(self) -> str:
        """get camera model as string"""
        has0th = '0th' in self.metadata
        if has0th and (piexif.ImageIFD.Model in self.metadata['0th']):
            return self.metadata['0th'][piexif.ImageIFD.Model]
        return ""

    def get_description(self) -> str:
        """get the description"""
        has0th = '0th' in self.metadata
        idx_dsc = piexif.ImageIFD.ImageDescription
        if has0th and (idx_dsc in self.metadata['0th']):
            return self.metadata['0th'][idx_dsc]
        return ""

    def get_copyright(self) -> str:
        """get the copyright"""
        has0th = '0th' in self.metadata
        idx_cpr = piexif.ImageIFD.Copyright
        if has0th and (idx_cpr in self.metadata['0th']):
            return self.metadata['0th'][idx_cpr]
        return ""

    def set_date_original(self, new_datetime: datetime.datetime) -> None:
        """set_date_original"""
        datetime2add = convert.datetime2str(new_datetime, ":", " ", ":")
        self.metadata['Exif'][piexif.ExifIFD.SubSecTimeOriginal] = b'00'
        self.metadata['Exif'][piexif.ExifIFD.DateTimeOriginal
                              ] = datetime2add.encode('utf-8')

    def set_date_digitized(self, new_datetime: datetime.datetime) -> None:
        """set_date_digitized"""
        datetime2add = convert.datetime2str(new_datetime, ":", " ", ":")
        self.metadata['Exif'][piexif.ExifIFD.SubSecTimeDigitized] = b'00'
        self.metadata['Exif'][piexif.ExifIFD.DateTimeDigitized
                              ] = datetime2add.encode('utf-8')

    def set_artist(self, artist: str) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Artist
                             ] = artist.encode('utf-8')

    def set_camera_maker(self, camera_maker: str) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Make
                             ] = camera_maker.encode('utf-8')

    def set_camera_model(self, camera_model: str) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Model
                             ] = camera_model.encode('utf-8')

    def set_copyright(self, img_copyright: str) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Copyright
                             ] = img_copyright.encode('utf-8')

    def set_exif_version(self, version="0220") -> None:
        """add the field to the <Exif> data"""
        self.metadata['Exif'][piexif.ExifIFD.ExifVersion
                              ] = version.encode('utf-8')

    def set_software(self, software: str) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Software
                             ] = software.encode('utf-8')

    def set_orientation(self, orientation: int) -> None:
        """add the field to the <image> data"""
        self.metadata['0th'][piexif.ImageIFD.Orientation] = orientation

    def set_gps_data(self, lat: float, lon: float, alt: float,
                     mean_sea_level=True) -> None:
        """add_gps_data field"""
        lat_dmsz = convert.deg2dms_zone(lat, ("N", "S"))
        lon_dmsz = convert.deg2dms_zone(lon, ("E", "W"))

        gps_lat = ((lat_dmsz[0], 1), (lat_dmsz[1], 1),
                   (int(lat_dmsz[2] * 100), 100))
        gps_log = ((lon_dmsz[0], 1), (lon_dmsz[1], 1),
                   (int(lon_dmsz[2] * 100), 100))

        self.metadata['GPS'][piexif.GPSIFD.GPSVersionID] = (2, 2, 0, 0)
        self.metadata['GPS'][piexif.GPSIFD.GPSAltitudeRef] = int(
            mean_sea_level)
        self.metadata['GPS'][piexif.GPSIFD.GPSLatitudeRef] = lat_dmsz[3]
        self.metadata['GPS'][piexif.GPSIFD.GPSLongitudeRef] = lon_dmsz[3]
        self.metadata['GPS'][piexif.GPSIFD.GPSLatitude] = gps_lat
        self.metadata['GPS'][piexif.GPSIFD.GPSLongitude] = gps_log
        self.metadata['GPS'][piexif.GPSIFD.GPSAltitude] = (
            int(alt * 100), 100)

    def add_keywords(self, keywords: list, overwrite=False) -> None:
        """add keywords (overwrite keywords if desired)"""
        assert isinstance(keywords, list), "<keys2add> must be a list"
        if not overwrite:
            new_keys2add = []
            for kwd in keywords:
                if kwd not in self._temporal_keywords:
                    new_keys2add.append(kwd)
            new_keywords = ";".join(self._temporal_keywords + new_keys2add)
        else:
            new_keywords = ";".join(keywords)
        utf16_keywords = new_keywords.encode('utf-16')
        self.metadata['0th'][piexif.ImageIFD.XPKeywords] = utf16_keywords
