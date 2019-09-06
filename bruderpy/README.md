# BruderPy Addon

This addon receives images from network enabled document scanners via webdav, runs OCR on them and archives them GPG encrypted to the /share folder. 

Maintenance State / Software Quality: Experimental Software

## Features

* Fully automatic document archiving directly from printer
* Deskewing, thumbnailing and OCR
* Archiving of original raw images
* Detects document date from the letterhead
* Storage in encrypted archive
* Triggers custom Homeassistant Events
* Open file format (just files in a folder) compatible with [OpenPaper](https://openpaper.work/en-us/)


## Configuration

### Scanner

Create a new webdav destination (called "Sharepoint" on *Brother ADS-2400N*) with the hostname and selected port of the hassio server. File, folder names and authentication are ignored by BruderPy. Select an [supported image format (e.g. JPEG)](https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html) instead of PDF. Multipage scanning throught "Automatic Document Feeding" ist supported and pages will be collected into a single folder.


### Hassio
Choose an public port in the hassio addon (or leave the default) and enter the desired gpg key ids in the options. The public keys are fetched from [hkps://keys.openpgp.org](https://keys.openpgp.org).

The addon triggers two events within homeassitant: `bruderpy_scancomplete` when a scan has been sucessfully processed and archived, and `bruderpy_scanerror` when there was an error. Information about the documents path, the number of received pages and any labels generated for the document are passed as json data.
```
{
    "path" : "/share/bruderpy/201901010000.tar.gpg",
    "pages" : 3,
    "labels" : []
}
```

## Supported Devices
Only tested with a **Brother ADS-2400N**. Likely that any webdav supporting scanner will work.