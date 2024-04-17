```
Exe path: C:\VELO_FFT_service 

Log path: C:\VELO_FFT_service\logs 

Supporting Json path: C:\\VELO_FFT_service\\Vegam_MQTT.json 
```


## Exe creation steps: ***as per pm local***

**Path:**
>D:\src_vel_fft_test>

**Activate venv**
>D:\Venvs\Velo_fft_src\Scripts\activate


## Use this command
pyinstaller --add-data "D:\src_vel_fft_test\AnalyticsJsonHandler.py;." --add-data "D:\src_vel_fft_test\AnalyticsMqtt.py;." --hidden-import paho.mqtt.client --hidden-import paho.mqtt.publish --hidden-import paho.mqtt.subscribe --hidden-import pandas --hidden-import scipy --onefile AnalyticsVelFFT.py

[comment]: <> (pyinstaller --add-data "D:\src_vel_fft_test\import_constants.py;." --add-data "D:\src_vel_fft_test\AnalyticsJsonHandler.py;." --add-data "D:\src_vel_fft_test\AnalyticsMqtt.py;." --hidden-import paho.mqtt.client --hidden-import paho.mqtt.publish --hidden-import paho.mqtt.subscribe --hidden-import pandas --hidden-import scipy --onefile AnalyticsVelFFT.py)



`one can create virtual env by the ` <span style="color:green;">requirements_dev.txt</span> ` file and use the command`


 
[comment]: <> (<span style="color:orange;">-purbasha</span>)

- [points to be checked for next exe creation](#points to be checked for exe creation)
1. folder is not working as package , but `__init__` file is present
2. so, all py file need to added in exe command one by one
3. it is getting created when venv is activated, but pip packages are not
   getting bundled up in exe.
 


<details>
<summary>
  My work stuffs [pm]:
</summary>
<br>

>for /f "delims=" %i in ('pip freeze ^| findstr /v /c:pkg-resources==') do pip install --upgrade %i

>pip list --outdated

git stash

git pull

git stash apply stash@{0}

git push


</details>

>-For data_generate_collet test python file exe :    
pyinstaller  --onefile data_generator_collector.py


```buildoutcfg


pyinstaller --onefile --additional-hooks-dir="D:\vegam_git_projects\Vegam_Analytics\custom_hooks" --add-data "D:\vegam_git_projects\Vegam_Analytics\Scripts\Trending\report\ReportGenerator.py;Scripts\Trending\report" --add-data "D:\vegam_git_projects\Vegam_Analytics\Scripts\Trending\report\ExtractMetaData.py;Scripts\Trending\report" --add-data "D:\vegam_git_projects\Vegam_Analytics\Scripts\Trending\report\ExtractSensorData.py;Scripts\Trending\report" --add-data "D:\vegam_git_projects\Vegam_Analytics\Scripts\Trending\report\TrendGenerator.py;Scripts\Trending\report" --hidden-import=requests --hidden-import=docx --hidden-import=fitz --hidden-import=pandas --hidden-import=docx2pdf --hidden-import=psutil --hidden-import=matplotlib --hidden-import=install --hidden-import=xlsxwriter --hidden-import=openpyxl --hidden-import=scipy --clean "D:\vegam_git_projects\Vegam_Analytics\Scripts\Trending\report\ReportGeneratorFacade.py"

```