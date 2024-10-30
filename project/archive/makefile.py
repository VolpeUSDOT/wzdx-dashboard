import io
import json
import os
import tempfile
import zipfile

# adapted from
# https://julianrawcliffe.wordpress.com/2018/02/17/dynamic-in-memory-zip-file-creation/


def makeFile(dir, filename, data):
    """
    A simple function to write a file in a given directory
    """
    fname = str(dir) + "/" + str(filename)
    fh = open(fname, "w")
    fh.write(data)
    fh.close()
    return True


def mkZipFile(values):
    """
    Function to create a zip file containing the application configuration files
    To create the zip file, we need to create a memory file (BytesIO))
    Params:
     row: Database row object containing columns for filename and
     content to be written in the form
     { {"file1": "Content for file 1}, {"file2": "Different content for file"} }
    Returns:
     data: BytesIO object containing the zipped files
    """

    zipdir = tempfile.mkdtemp()
    oldpath = os.getcwd()
    os.chdir(zipdir)

    for row in values:
        makeFile(
            zipdir,
            f"{row['id']}.json",
            json.dumps(row["data"], indent=4),
        )

    # Create the in-memory zip image
    data = io.BytesIO()
    with zipfile.ZipFile(data, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname in os.listdir("."):
            z.write(fname)
            os.unlink(fname)
    data.seek(0)

    os.chdir(oldpath)
    os.rmdir(zipdir)
    return data
