# BruderPy Addon

This addon receives images from network enabled document scanners via webdav, runs OCR on them and archives them GPG encrypted to the /share folder. 

Maintenance State / Software Quality: Experimental Software

## Features

* Fully automatic document archiving directly from scanner
* Deskewing, thumbnailing and OCR
* Archiving of original raw images
* Detects document date from the letterhead
* Storage in encrypted archive
* Triggers custom HomeAssistant Events
* Open file format (just files in a folder) compatible with [OpenPaper](https://openpaper.work/en-us/)

## Installation

This addon is available through the repository https://github.com/gregod/hassio-addon-repo. See the [Homeassistant Documentation](https://www.home-assistant.io/hassio/installing_third_party_addons/) for installation instructions.

## Configuration

### Scanner

Create a new webdav destination (called "Sharepoint" on *Brother ADS-2400N*) with the hostname and selected port of the HomeAssistant server. File, folder names and authentication are ignored by BruderPy. Select an [supported image format (e.g. JPEG)](https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html) instead of PDF. Multipage scanning throught "Automatic Document Feeding" ist supported and pages will be collected into a single folder.


### Hassio
Choose an public port in the hassio addon and enter the desired gpg key ids in the options. The public keys are fetched from [hkps://keys.openpgp.org](https://keys.openpgp.org).

Encrypted files are stored within the `/share/bruderpy/` directory, that can be accessed using any of the FTP/SMB plugins that hassio provides.

The addon triggers two events within HomeAssistant: `bruderpy_scancomplete` when a scan has been successfully processed and archived, and `bruderpy_scanerror` when there was an error. Information about the documents path, the number of received pages and any labels generated for the document are passed as JSON data.
```
{
    "path" : "/share/bruderpy/201901010000.tar.gpg",
    "pages" : 3,
    "labels" : []
}
```

## Supported Devices
Only tested with a **Brother ADS-2400N**. Likely that any webdav supporting scanner will work.
