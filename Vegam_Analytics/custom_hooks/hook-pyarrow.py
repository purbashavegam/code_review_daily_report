print("Custom pyarrow hook is being used.")
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('pyarrow')
# from PyInstaller.utils.hooks import collect_data_files
# datas, binaries, hiddenimports = collect_data_files('PyMuPDF')


print("Custom pyarrow hook is being used. or not??")