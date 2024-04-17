print("Custom fitz hook is being used.")
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('PyMuPDF')
# from PyInstaller.utils.hooks import collect_data_files
# datas, binaries, hiddenimports = collect_data_files('PyMuPDF')


print("Custom fitz hook is being used. or not??")