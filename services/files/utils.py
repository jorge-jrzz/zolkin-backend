"""
Utility functions for file processing and management.
"""
import os
import re
import unicodedata


def secure_filename(filename: str) -> str:
        """Pass it a filename and it will return a secure version of it.  This
        filename can then safely be stored on a regular file system.
        """
        _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_.-]")
        _windows_device_files = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{i}" for i in range(10)),
            *(f"LPT{i}" for i in range(10)),
        }
        filename = unicodedata.normalize("NFKD", filename)
        filename = filename.encode("ascii", "ignore").decode("ascii")

        for sep in os.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, " ")
        filename = str(_filename_ascii_strip_re.sub("", "_".join(filename.split()))).strip(
            "._"
        )
        if (
            os.name == "nt"
            and filename
            and filename.split(".")[0].upper() in _windows_device_files
        ):
            filename = f"_{filename}"

        return filename
